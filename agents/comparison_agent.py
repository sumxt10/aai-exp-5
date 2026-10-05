from agents.base_agent import BaseAgent

class ComparisonAgent(BaseAgent):
    """Compares the filtered products on price, RAM, storage, rating."""
    name, role = "ComparisonAgent", "comparison"

    def execute(self, state, task, label, span, **kw):
        out = self.call_tool(state, "comparison_tool", span, products=state.filtered_results, requirements=state.requirements)
        state.write("comparison", "comparison", out)
        return out["summary"]
