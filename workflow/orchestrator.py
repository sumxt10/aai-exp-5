"""Orchestrates the whole pipeline: sanitize -> plan -> validate -> route -> staged execution
(parallel where independent) -> supervise -> human approval -> finalize."""
import time
from concurrent.futures import ThreadPoolExecutor
from config import settings
from core.exceptions import WorkflowError, WorkflowAborted, SecurityViolation
from core.logger import log_event
from core.state import WorkflowState
from mcp_tools.registry import build_default_registry
from security.input_guard import sanitize_query
from workflow.human_approval import HumanApproval
from agents.planner_agent import PlannerAgent
from agents.router_agent import RouterAgent
from agents.search_agent import SearchAgent
from agents.synchronizer_agent import SynchronizerAgent
from agents.filter_agent import FilterAgent
from agents.comparison_agent import ComparisonAgent
from agents.ranking_agent import RankingAgent
from agents.validator_agent import ValidatorAgent
from agents.supervisor_agent import SupervisorAgent

ANALYSIS_TASKS = {"filter", "validate_filter", "compare", "rank", "validate_rank", "supervise"}

class Orchestrator:
    def __init__(self, parallel=True, approval_mode="auto", registry=None):
        self.parallel = parallel
        self.registry = registry or build_default_registry()
        self.human = HumanApproval(approval_mode)
        r = self.registry
        self.planner = PlannerAgent(r, settings.SEARCH_SOURCES)
        self.router = RouterAgent(r)
        self.validator = ValidatorAgent(r)
        self.supervisor = SupervisorAgent(r)
        self.handlers = {"search": SearchAgent(r), "sync": SynchronizerAgent(r), "filter": FilterAgent(r),
                         "compare": ComparisonAgent(r), "rank": RankingAgent(r),
                         "validate": self.validator, "supervise": self.supervisor}

    # ------------------------------------------------------------------ run
    def run(self, query):
        state = WorkflowState(query)
        state.status = "running"
        log_event(state.workflow_id, "workflow_start", query=query, parallel=self.parallel)
        t0 = time.perf_counter()
        try:
            clean, findings = sanitize_query(query)
            state.write("system", "sanitized_query", clean)
            for f in findings:
                state.add_security_event("prompt_injection_stripped", **f)
            state.add_message("User", "PlannerAgent", "query", query, clean, "sanitized" if findings else "ok")

            reqs = self.planner.run(state, "plan")
            state.add_message("PlannerAgent", "ValidatorAgent", "plan", clean, str(reqs), "success")
            self.validator.run(state, "validate_requirements", stage="requirements")   # checkpoint 1
            routing = self.router.run(state, "route")
            state.add_message("RouterAgent", "Orchestrator", "route", f"{len(state.plan)} tasks",
                              f"{len(routing['stages'])} stages, parallel stages {routing['parallel_stages']}", "success")

            self._execute_stages(state)
            self._approval_loop(state)
            self.supervisor.run(state, "finalize")
            state.status = "completed"
        except SecurityViolation as exc:
            state.status = "blocked_security"
            state.add_error("Orchestrator", exc)
        except WorkflowError as exc:
            state.status = "failed"
            state.add_error("Orchestrator", exc)
        finally:
            state.metrics.total_time = time.perf_counter() - t0
            log_event(state.workflow_id, "workflow_end", status=state.status, **state.metrics.summary())
        return state

    # ------------------------------------------------------- stage execution
    def _execute_stages(self, state, only=None):
        tasks = {t["id"]: t for t in state.plan}
        for stage in state.routing["stages"]:
            ids = [i for i in stage if only is None or i in only]
            if not ids:
                continue
            if self.parallel and len(ids) > 1:
                with ThreadPoolExecutor(max_workers=len(ids)) as ex:
                    list(ex.map(lambda i: self._run_task(state, tasks[i]), ids))   # barrier = synchronization
            else:
                for i in ids:
                    self._run_task(state, tasks[i])

    def _run_task(self, state, task):
        ttype, tid = task["type"], task["id"]
        agent = self.handlers[ttype]
        label = f"SearchAgent[{task['source']}]" if ttype == "search" else agent.name
        kwargs = {"source": task.get("source")} if ttype == "search" else {"stage": task.get("stage")} if ttype == "validate" else {}
        receivers = sorted({state.routing["assignments"][t["id"]] for t in state.plan if tid in t["depends_on"]}) or ["Orchestrator"]
        try:
            out = agent.run(state, tid, label=label, **kwargs)
            state.add_message(label, ",".join(receivers), tid, f"task={tid}", str(out)[:120], "success")
            return True
        except SecurityViolation:
            raise
        except WorkflowError as exc:
            state.add_message(label, ",".join(receivers), tid, f"task={tid}", str(exc)[:120], "failed")
            if ttype == "search":        # tolerate partial search failure; sync uses what is available
                return False
            raise WorkflowAborted(f"Task '{tid}' failed: {exc}") from exc

    # --------------------------------------------------- supervisor + human
    def _reanalyze(self, state):
        state.reanalysis_count += 1
        log_event(state.workflow_id, "reanalysis", count=state.reanalysis_count)
        self._execute_stages(state, only=ANALYSIS_TASKS)

    def _approval_loop(self, state):
        while True:
            decision = state.supervisor_decision
            if decision["action"] == "abort":
                raise WorkflowAborted(decision["reason"])
            if decision["action"] == "retry_analysis" and state.reanalysis_count < settings.MAX_REANALYSIS:
                self._reanalyze(state)
                continue
            resp = self.human.request(state)
            state.write("human", "human_approval", resp)
            state.add_message("HumanReviewer", "SupervisorAgent", "approval", str(decision), resp["status"], "success")
            if resp["status"] == "reanalyze" and state.reanalysis_count < settings.MAX_REANALYSIS:
                self._reanalyze(state)
                continue
            return
