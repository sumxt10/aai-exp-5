# Architecture

```
User Query
   │  security/input_guard (strip prompt injection)
   ▼
Planner ─► Validator[requirements] ─► Router (dependency-aware stages)
                                         │
   Stage 0 (parallel):  Search[StoreA] │ Search[StoreB] │ Search[StoreC]
                                         ▼  barrier
   Stage 1: Synchronizer (merge, de-dup, conflict resolution by trusted source)
   Stage 2: Filter ─► Stage 3: Validator[filtering] ─► Stage 4: Comparison
   Stage 5: Ranking ─► Stage 6: Validator[ranking] ─► Stage 7: Supervisor
                                         ▼
   Supervisor decision ─► Human Approval (approve / reject / reanalyze) ─► Supervisor.finalize
```
Every box runs through BaseAgent.run(): trace span + metrics + log + controlled retry.
Every tool call goes through ToolRegistry.execute(): role-based authorization + audit log.
Every shared-state write goes through WorkflowState.write(): per-role key permissions + locked requirements (SHA-256).
