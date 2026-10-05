"""Controlled retry: only RecoverableError, bounded attempts, no infinite loops."""
import time
from core.exceptions import RecoverableError

def run_with_retry(fn, max_retries, on_retry=None, backoff=0.05):
    attempt = 0
    while True:
        try:
            return fn(), attempt
        except RecoverableError as exc:
            if attempt >= max_retries:
                raise                      # give up -> failure handling / Supervisor
            attempt += 1
            if on_retry:
                on_retry(attempt, exc)
            time.sleep(backoff * attempt)
