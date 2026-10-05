"""Builds and prints the expected final result + saves JSON artifacts."""
import json
from config import settings

def build_report(state):
    return {
        "workflow_id": state.workflow_id, "status": state.status,
        "user_query": state.user_query, "sanitized_query": state.sanitized_query,
        "requirements": state.requirements,
        "ranked_products": state.ranking, "rejected_products": state.rejected_results,
        "conflicts_resolved": state.conflicts,
        "validation_result": state.validation,
        "supervisor_decision": state.supervisor_decision,
        "human_approval": state.human_approval,
        "final_recommendation": state.final_recommendation,
        "agent_communication": state.messages,
        "execution_trace": state.tracer.ordered(),
        "metrics": state.metrics.summary(),
        "security_events": state.security_events,
        "errors": state.errors,
    }

def save_report(state):
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = settings.OUTPUT_DIR / f"report_{state.workflow_id}.json"
    path.write_text(json.dumps(build_report(state), indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    return path

def print_report(state):
    m = state.metrics.summary()
    print("\n" + "=" * 70)
    print(f"WORKFLOW {state.workflow_id}  STATUS: {state.status}")
    print("Query       :", state.user_query)
    if state.sanitized_query != state.user_query:
        print("Sanitized   :", state.sanitized_query)
    print("Requirements:", state.requirements)
    print("-" * 70, "\nRANKED PRODUCTS")
    for p in state.ranking:
        print(f"  #{p['rank']} {p['name']:<26} Rs.{p['price']:>7,}  RAM {p['ram_gb']}GB  {p['storage_gb']}GB  "
              f"rating {p['rating']}  score {p['score']}")
        print("       why:", "; ".join(p["reasons"]))
    print("-" * 70)
    for c in state.conflicts:
        print(f"CONFLICT {c['product_id']}.{c['field']} {c['values']} -> {c['resolved_to']} ({c['method']})")
    print("Validation  :", {k: v["passed"] for k, v in state.validation.items()})
    print("Supervisor  :", state.supervisor_decision)
    print("Human       :", (state.human_approval or {}).get("status"))
    fr = state.final_recommendation or {}
    top = fr.get("top_recommendation")
    print("FINAL       :", fr.get("status"), "->", top["name"] if top else "none")
    print("Security    :", state.security_events or "no events")
    print("Errors      :", state.errors or "none")
    print("-" * 70, "\nEXECUTION TRACE")
    for s in state.tracer.ordered():
        print(f"  {s['agent']:<24} {s['task']:<16} {s['status']:<8} {s['duration_s']}s tools={s['tools']} retries={s['retries']}")
    print("-" * 70, "\nMETRICS", m)
    print("=" * 70)
