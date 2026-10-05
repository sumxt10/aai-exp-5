"""Failure injection for failure-testing (tool failure, timeouts, permanent errors)."""
import threading
from core.exceptions import ToolFailure, MissingDataError

class FailureInjector:
    def __init__(self):
        self._rules, self._lock = {}, threading.Lock()

    def add(self, key, times=1, permanent=False):
        with self._lock:
            self._rules[key] = {"times": times, "permanent": permanent}

    def check(self, key):
        with self._lock:
            rule = self._rules.get(key)
            if not rule or rule["times"] <= 0:
                return
            if not rule["permanent"]:
                rule["times"] -= 1
        if rule["permanent"]:
            raise MissingDataError(f"Injected permanent failure at '{key}'")
        raise ToolFailure(f"Injected transient failure at '{key}'")

    def reset(self):
        with self._lock: self._rules.clear()

injector = FailureInjector()
