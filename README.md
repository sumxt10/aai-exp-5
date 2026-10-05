# Lab 5 – E-Commerce Product Analysis & Recommendation Pipeline (Multi-Agent)

**Name:** <YOUR NAME>  **Roll No:** <YOUR ROLL NO>  **Date of Performance / Submission:** <DOP> / <DOS>

## Run
```bash
pip install -r requirements.txt
python main.py                                   # default query, parallel, auto-approval
python main.py --mode sequential                 # sequential execution
python main.py --approval interactive            # real human-in-the-loop on console
python main.py --inject search:StoreB=1          # transient failure -> controlled retry
python main.py --inject search:StoreC=permanent  # permanent failure -> no retry
python main.py --query "Find laptops under ₹60,000 with 16 GB RAM"
python main.py --security-tests                  # security suite
python experiments/run_experiment.py            # fills the observation table -> outputs/observation_table.md
streamlit run app.py                            # interactive final demonstration
python -m pytest -q                              # functional, failure, security, performance tests
```
Outputs: `logs/workflow_<id>.log` (JSON-lines), `outputs/report_<id>.json` (trace, messages, metrics, cost, security, approval).

## Streamlit demonstration

Run `streamlit run app.py` from this folder. The sidebar can run the same coordinated
workflow in parallel or sequential mode, exercise auto/reject/reanalysis approval
paths, inject bounded search failures, run the full observation-table experiment,
and run the security suite. The page displays the shared requirements, dependency
router stages, agent messages, synchronized conflicts, checkpoints, supervisor and
human decisions, execution trace, metrics, ranked products, and downloadable JSON/
Markdown artifacts.

## Concept -> file map
| Concept | File |
|---|---|
| Planner / query decomposition | agents/planner_agent.py, mcp_tools/tools.py::planning_tool |
| Router, dependency-aware stages | agents/router_agent.py |
| Search / Filter / Compare / Rank | agents/*_agent.py, mcp_tools/tools.py |
| Synchronization + conflict resolution | agents/synchronizer_agent.py |
| Validator (checkpoints) / Supervisor | agents/validator_agent.py, agents/supervisor_agent.py |
| Shared state + write permissions | core/state.py, config/permissions.py |
| Inter-agent messages | core/messages.py, workflow/orchestrator.py |
| Parallel vs sequential | workflow/orchestrator.py (`parallel=` flag) |
| Human-in-the-loop | workflow/human_approval.py |
| Retry / failure handling | core/retry.py, core/failure.py, core/exceptions.py |
| Logging / tracing | core/logger.py, core/tracer.py |
| Performance / cost | core/metrics.py, experiments/run_experiment.py |
| MCP-style registry + authorization | mcp_tools/registry.py, mcp_tools/authorization.py |
| Security validation | security/input_guard.py, security/security_tests.py |

> The MCP layer is intentionally simplified (not the full MCP protocol) – full protocol is Experiment 06.
