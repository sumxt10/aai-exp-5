"""Base class: wraps every agent execution with tracing, metrics, logging and controlled retry."""
import time
from config import settings
from core.logger import log_event
from core.retry import run_with_retry

class BaseAgent:
    name = "BaseAgent"
    role = None

    def __init__(self, registry):
        self.registry = registry

    def call_tool(self, state, tool, span, **kwargs):
        return self.registry.execute(state, self.role, tool, span=span, **kwargs)

    def execute(self, state, task, label, span, **kwargs):
        raise NotImplementedError

    def run(self, state, task, label=None, **kwargs):
        label = label or self.name
        state.metrics.agent_call()
        span = state.tracer.start(label, task)
        log_event(state.workflow_id, "agent_start", agent=label, task=task)
        t0 = time.perf_counter()

        def on_retry(n, exc):
            state.metrics.retry()
            state.tracer.note_retry(span, n, exc)
            log_event(state.workflow_id, "retry", agent=label, attempt=n, error=str(exc))

        try:
            result, _ = run_with_retry(lambda: self.execute(state, task, label, span, **kwargs),
                                       settings.MAX_RETRIES, on_retry)
            state.tracer.end(span, "success", output_status="ok")
            log_event(state.workflow_id, "agent_end", agent=label, task=task, status="success")
            return result
        except Exception as exc:
            state.add_error(label, exc)
            state.tracer.end(span, "failed", output_status="error", error=str(exc))
            raise
        finally:
            state.metrics.add_agent_time(label, time.perf_counter() - t0)
