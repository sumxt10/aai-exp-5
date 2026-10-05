from workflow.orchestrator import Orchestrator

Q = "Find laptops under ₹70,000 with at least 16 GB RAM, 512 GB storage and rating above 4.2."

def test_parallel_faster_than_sequential():
    seq = Orchestrator(parallel=False).run(Q)
    par = Orchestrator(parallel=True).run(Q)
    assert par.metrics.total_time < seq.metrics.total_time
    assert par.final_recommendation["top_recommendation"]["id"] == seq.final_recommendation["top_recommendation"]["id"]

def test_cost_and_counters():
    s = Orchestrator().run(Q)
    m = s.metrics.summary()
    assert m["agent_calls"] == 14 and m["tool_calls"] == 12 and m["experimental_cost_units"] > 0
