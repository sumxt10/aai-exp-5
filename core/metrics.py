"""Performance and experimental-cost measurement."""
import threading
from config import settings

class Metrics:
    def __init__(self):
        self.agent_calls = 0
        self.tool_calls = 0
        self.retries = 0
        self.processing_ops = 0
        self.agent_times = {}
        self.total_time = 0.0
        self._lock = threading.Lock()

    def agent_call(self):
        with self._lock: self.agent_calls += 1
    def tool_call(self):
        with self._lock: self.tool_calls += 1
    def retry(self):
        with self._lock: self.retries += 1
    def processing(self, n):
        with self._lock: self.processing_ops += n
    def add_agent_time(self, label, secs):
        with self._lock: self.agent_times[label] = self.agent_times.get(label, 0) + secs

    def cost(self):
        u = settings.COST_UNITS
        return round(self.agent_calls * u["agent_call"] + self.tool_calls * u["tool_call"]
                     + self.retries * u["retry"] + self.processing_ops * u["processing_op"], 2)

    def summary(self):
        return {
            "total_time_s": round(self.total_time, 4),
            "sum_of_agent_times_s": round(sum(self.agent_times.values()), 4),
            "agent_times_s": {k: round(v, 4) for k, v in self.agent_times.items()},
            "agent_calls": self.agent_calls, "tool_calls": self.tool_calls,
            "retries": self.retries, "processing_ops": self.processing_ops,
            "experimental_cost_units": self.cost(),
        }
