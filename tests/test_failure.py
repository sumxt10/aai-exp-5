from core.failure import injector
from core.exceptions import ToolFailure
from workflow.orchestrator import Orchestrator
from mcp_tools.registry import build_default_registry

Q = "Find laptops under ₹70,000 with at least 16 GB RAM, 512 GB storage and rating above 4.2."

def test_transient_failure_is_retried():
    injector.add("search:StoreB", times=1)
    s = Orchestrator().run(Q)
    assert s.status == "completed" and s.metrics.retries == 1

def test_retry_is_bounded():
    injector.add("search:StoreB", times=99)
    s = Orchestrator().run(Q)
    assert s.metrics.retries == 2                     # MAX_RETRIES, then give up
    assert any("StoreB" in e["agent"] for e in s.errors)
    assert s.status == "completed"                    # other sources still served

def test_permanent_failure_not_retried():
    injector.add("search:StoreC", permanent=True)
    s = Orchestrator().run(Q)
    assert s.metrics.retries == 0 and s.status == "completed"

def test_all_sources_fail_aborts():
    for src in ("StoreA", "StoreB", "StoreC"):
        injector.add(f"search:{src}", permanent=True)
    assert Orchestrator().run(Q).status == "failed"

def test_invalid_input():
    assert Orchestrator().run("").status == "failed"
    assert Orchestrator().run("hello there").status == "failed"      # no category

def test_validation_failure_triggers_reanalysis_then_recovers():
    reg = build_default_registry()
    real, calls = reg._tools["ranking_tool"].func, {"n": 0}
    def flaky(**kw):                                   # first call returns badly-ordered ranking
        out = real(**kw); calls["n"] += 1
        return list(reversed(out)) if calls["n"] == 1 else out
    reg._tools["ranking_tool"].func = flaky
    s = Orchestrator(registry=reg).run(Q)
    assert s.reanalysis_count == 1 and s.final_recommendation["status"] == "approved"
