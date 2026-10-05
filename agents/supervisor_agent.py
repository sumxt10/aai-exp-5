from agents.base_agent import BaseAgent

class SupervisorAgent(BaseAgent):
    """Monitors the workflow, checks validation, decides recovery/escalation, finalizes."""
    name, role = "SupervisorAgent", "supervisor"

    def execute(self, state, task, label, span, **kw):
        if task == "finalize":
            return self._finalize(state, span)
        validation_passed = all(v["passed"] for v in state.validation.values())
        decision = self.call_tool(state, "workflow_control_tool", span, action="review",
                                  fatal_errors=False, validation_passed=validation_passed,
                                  has_results=bool(state.ranking), reanalysis_count=state.reanalysis_count)
        state.write("supervisor", "supervisor_decision", decision)
        return decision

    def _finalize(self, state, span):
        approval = (state.human_approval or {}).get("status")
        validation_failed = not all(v["passed"] for v in state.validation.values())
        res = self.call_tool(state, "workflow_control_tool", span, action="finalize", approval=approval,
                             validation_failed=validation_failed, has_results=bool(state.ranking))
        final = {"status": res["status"], "top_recommendation": None, "ranked_products": []}
        if res["status"] == "approved":
            final["top_recommendation"] = state.ranking[0]
            final["ranked_products"] = state.ranking
        state.write("supervisor", "final_recommendation", final)
        return final
