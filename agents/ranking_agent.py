from agents.base_agent import BaseAgent
from core.exceptions import InvalidOutputError

class RankingAgent(BaseAgent):
    """Scores and sorts products with transparent, requirement-aware reasoning."""
    name, role = "RankingAgent", "ranking"

    def execute(self, state, task, label, span, **kw):
        table = state.comparison["table"] if state.comparison else []
        ranked = self.call_tool(state, "ranking_tool", span, products=table, requirements=state.requirements)
        if not isinstance(ranked, list):
            raise InvalidOutputError("Ranking tool returned invalid output")
        state.write("ranking", "ranking", ranked)
        return len(ranked)
