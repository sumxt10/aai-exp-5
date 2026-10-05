"""Runs sequential vs parallel, security tests, and writes the OBSERVATION TABLE."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from config import settings
from core.failure import injector
from workflow.orchestrator import Orchestrator
from workflow.report import save_report
from security.security_tests import run_security_tests

QUERY = "Find laptops under ₹70,000 with at least 16 GB RAM, 512 GB storage and rating above 4.2."

def main(approval="auto"):
    injector.reset()
    seq = Orchestrator(parallel=False, approval_mode=approval).run(QUERY)
    injector.reset()
    par = Orchestrator(parallel=True, approval_mode=approval).run(QUERY)
    save_report(par)
    # retry demonstration: one transient failure in StoreB search
    injector.reset(); injector.add("search:StoreB", times=1)
    retry_run = Orchestrator(parallel=True, approval_mode=approval).run(QUERY)
    injector.reset()
    sec_summary, _ = run_security_tests(verbose=False)

    ts, tp = seq.metrics.total_time, par.metrics.total_time
    top = (par.final_recommendation or {}).get("top_recommendation")
    rows = [
        ("User Query", QUERY),
        ("Number of Agents Executed", f"{par.metrics.agent_calls} agent executions"),
        ("Sequential Execution Time", f"{ts:.3f} s"),
        ("Parallel Execution Time", f"{tp:.3f} s  (speedup = {ts/tp:.2f}x)"),
        ("Number of Tool Calls", par.metrics.tool_calls),
        ("Experimental Cost (units)", f"{par.metrics.cost()}  (sequential {seq.metrics.cost()}, with-retry run {retry_run.metrics.cost()})"),
        ("Number of Retries", f"{retry_run.metrics.retries} (in failure-injection run)"),
        ("Human Approval", (par.human_approval or {}).get("status")),
        ("Security Test Result", sec_summary),
        ("Final Recommendation", f"{top['name']} - Rs.{top['price']:,} (score {top['score']})" if top else "none"),
    ]
    md = "| Parameter | Observation |\n|---|---|\n" + "\n".join(f"| {k} | {v} |" for k, v in rows)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (settings.OUTPUT_DIR / "observation_table.md").write_text(md, encoding="utf-8")
    print(md)

if __name__ == "__main__":
    main()
