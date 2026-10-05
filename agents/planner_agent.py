from agents.base_agent import BaseAgent

# task type -> depends_on (by id). Search tasks are generated per source.
class PlannerAgent(BaseAgent):
    """Understands the query, extracts structured requirements, builds the workflow plan.
    It does NOT search/filter/rank - planning only."""
    name, role = "PlannerAgent", "planner"

    def __init__(self, registry, sources):
        super().__init__(registry)
        self.sources = sources

    def execute(self, state, task, label, span, **kw):
        query = state.sanitized_query or state.user_query
        requirements = self.call_tool(state, "planning_tool", span, query=query)
        state.write("planner", "requirements", requirements)       # locks requirements

        search_ids = [f"search_{s}" for s in self.sources]
        plan = [{"id": f"search_{s}", "type": "search", "source": s, "depends_on": []} for s in self.sources]
        plan += [
            {"id": "sync",            "type": "sync",     "depends_on": search_ids},
            {"id": "filter",          "type": "filter",   "depends_on": ["sync"]},
            {"id": "validate_filter", "type": "validate", "stage": "filtering", "depends_on": ["filter"]},
            {"id": "compare",         "type": "compare",  "depends_on": ["validate_filter"]},
            {"id": "rank",            "type": "rank",     "depends_on": ["compare"]},
            {"id": "validate_rank",   "type": "validate", "stage": "ranking", "depends_on": ["rank"]},
            {"id": "supervise",       "type": "supervise","depends_on": ["validate_rank"]},
        ]
        state.write("planner", "plan", plan)
        return requirements
