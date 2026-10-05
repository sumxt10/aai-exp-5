from workflow.orchestrator import Orchestrator
from mcp_tools.tools import planning_tool

Q = "Find laptops under ₹70,000 with at least 16 GB RAM, 512 GB storage and rating above 4.2."

def test_requirement_extraction():
    assert planning_tool(Q) == {"category": "laptop", "max_budget": 70000, "min_ram_gb": 16,
                                "min_storage_gb": 512, "min_rating": 4.2}

def test_full_workflow():
    s = Orchestrator().run(Q)
    assert s.status == "completed"
    assert s.final_recommendation["status"] == "approved"
    assert s.ranking and all(p["price"] <= 70000 and p["ram_gb"] >= 16 and p["storage_gb"] >= 512 and p["rating"] >= 4.2 for p in s.ranking)
    assert [p["rank"] for p in s.ranking] == list(range(1, len(s.ranking) + 1))
    assert all(v["passed"] for v in s.validation.values())
    assert s.messages and s.tracer.spans

def test_conflict_resolution_uses_trusted_source():
    s = Orchestrator().run(Q)
    c = [c for c in s.conflicts if c["product_id"] == "L003" and c["field"] == "rating"][0]
    assert c["resolved_to"] == 4.4 and c["winner_source"] == "StoreA"

def test_human_rejection():
    s = Orchestrator(approval_mode="reject").run(Q)
    assert s.final_recommendation["status"] == "rejected" and s.final_recommendation["top_recommendation"] is None

def test_human_reanalysis():
    s = Orchestrator(approval_mode="reanalyze_once").run(Q)
    assert s.reanalysis_count == 1 and s.final_recommendation["status"] == "approved"

def test_no_match():
    s = Orchestrator().run("Find laptops under ₹10,000 with 32 GB RAM")
    assert s.final_recommendation["status"] == "no_match"
