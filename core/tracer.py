"""Execution tracing: which agent ran, when, what task, status, tools, retries, errors."""
import threading, time

class Tracer:
    def __init__(self):
        self.spans = []
        self._lock = threading.Lock()

    def start(self, agent, task):
        span = {"agent": agent, "task": task, "start": time.time(), "end": None, "duration_s": None,
                "status": "running", "tools": [], "retries": 0, "error": None, "output_status": None}
        with self._lock:
            self.spans.append(span)
        return span

    def note_retry(self, span, attempt, error):
        span["retries"] = attempt
        span["error"] = f"retry {attempt}: {error}"

    def end(self, span, status, output_status=None, error=None):
        span["end"] = time.time()
        span["duration_s"] = round(span["end"] - span["start"], 4)
        span["status"] = status
        span["output_status"] = output_status
        if error:
            span["error"] = error

    def ordered(self):
        return sorted(self.spans, key=lambda s: s["start"])
