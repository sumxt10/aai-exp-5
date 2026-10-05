"""Structured JSON-lines logging (one file per workflow)."""
import json, threading, time
from config import settings

_lock = threading.Lock()

def log_event(workflow_id, event, **fields):
    record = {"ts": round(time.time(), 4), "workflow_id": workflow_id, "event": event, **fields}
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, default=str, ensure_ascii=False)
    with _lock:
        with open(settings.LOG_DIR / f"workflow_{workflow_id}.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
        if settings.VERBOSE:
            print("[LOG]", line)
