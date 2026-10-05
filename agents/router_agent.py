from agents.base_agent import BaseAgent
from core.exceptions import InvalidInputError

AGENT_FOR_TYPE = {
    "search": "SearchAgent", "sync": "SynchronizerAgent", "filter": "FilterAgent",
    "compare": "ComparisonAgent", "rank": "RankingAgent",
    "validate": "ValidatorAgent", "supervise": "SupervisorAgent",
}

class RouterAgent(BaseAgent):
    """Assigns each task to its specialist and builds dependency-aware execution stages.
    Tasks in the same stage are independent (parallel-safe); stages run in order."""
    name, role = "RouterAgent", "router"

    def execute(self, state, task, label, span, **kw):
        plan = state.plan
        by_id = {t["id"]: t for t in plan}
        assignments = {}
        for t in plan:
            if t["type"] not in AGENT_FOR_TYPE:
                raise InvalidInputError(f"No agent for task type '{t['type']}'")
            assignments[t["id"]] = AGENT_FOR_TYPE[t["type"]]

        level = {}
        def depth(tid, seen=()):
            if tid in seen:
                raise InvalidInputError("Circular dependency in plan")
            if tid not in level:
                deps = by_id[tid]["depends_on"]
                level[tid] = 0 if not deps else 1 + max(depth(d, seen + (tid,)) for d in deps)
            return level[tid]
        for t in plan:
            depth(t["id"])

        stages = [[] for _ in range(max(level.values()) + 1)]
        for tid, lv in level.items():
            stages[lv].append(tid)
        routing = {"assignments": assignments, "stages": stages,
                   "parallel_stages": [i for i, s in enumerate(stages) if len(s) > 1]}
        state.write("router", "routing", routing)
        return routing
