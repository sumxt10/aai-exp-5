from agents.base_agent import BaseAgent
from core.exceptions import InvalidOutputError

class SearchAgent(BaseAgent):
    """Collects candidate products from ONE source. Never makes recommendations."""
    name, role = "SearchAgent", "search"

    def execute(self, state, task, label, span, source=None, **kw):
        items = self.call_tool(state, "search_tool", span, source=source, requirements=state.requirements)
        if not isinstance(items, list):
            raise InvalidOutputError(f"Search tool returned invalid output for {source}")
        state.write("search", "search_results", items, sub=source)
        return len(items)
