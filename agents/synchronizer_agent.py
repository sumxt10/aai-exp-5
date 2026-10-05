from agents.base_agent import BaseAgent
from config import settings
from core.exceptions import MissingDataError
from core.logger import log_event

COMPARE_FIELDS = ["price", "rating", "ram_gb", "storage_gb", "in_stock"]

class SynchronizerAgent(BaseAgent):
    """Barrier after parallel search: merges results, de-duplicates, resolves conflicts
    using trusted-source priority and records every conflict for review."""
    name, role = "SynchronizerAgent", "synchronizer"

    def execute(self, state, task, label, span, **kw):
        if not state.search_results:
            raise MissingDataError("All search agents failed - nothing to synchronize")
        grouped = {}
        for source, items in state.search_results.items():
            for p in items:
                grouped.setdefault(p["id"], []).append(p)

        priority = {s: i for i, s in enumerate(settings.TRUSTED_SOURCE_PRIORITY)}
        merged, conflicts = [], []
        for pid, records in grouped.items():
            records.sort(key=lambda r: priority.get(r["source"], 99))
            winner = dict(records[0])                      # trusted source wins
            for field in COMPARE_FIELDS:
                values = {r["source"]: r[field] for r in records}
                if len(set(values.values())) > 1:
                    conflicts.append({"product_id": pid, "field": field, "values": values,
                                      "resolved_to": winner[field], "method": "trusted_source_priority",
                                      "winner_source": winner["source"]})
            winner["seen_in"] = [r["source"] for r in records]
            merged.append(winner)
        merged.sort(key=lambda p: p["id"])
        state.write("synchronizer", "merged_results", merged)
        state.write("synchronizer", "conflicts", conflicts)
        for c in conflicts:
            log_event(state.workflow_id, "conflict_resolved", **c)
        state.metrics.processing(sum(len(v) for v in grouped.values()))
        return len(merged)
