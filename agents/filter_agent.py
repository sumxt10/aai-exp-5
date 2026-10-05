from agents.base_agent import BaseAgent

class FilterAgent(BaseAgent):
    """Constraint-based filtering using the locked user requirements."""
    name, role = "FilterAgent", "filter"

    def execute(self, state, task, label, span, **kw):
        out = self.call_tool(state, "filter_tool", span, products=state.merged_results, requirements=state.requirements)
        state.write("filter", "filtered_results", out["kept"])
        state.write("filter", "rejected_results", out["rejected"])
        return len(out["kept"])
