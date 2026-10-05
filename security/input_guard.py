"""Prompt-injection / malicious-input guard applied before planning."""
import re
from config import settings
from core.exceptions import InvalidInputError

INJECTION_PATTERNS = [
    r"\bignore\b", r"\bdisregard\b", r"\bforget\b", r"\boverride\b", r"\bbypass\b",
    r"\bsystem prompt\b", r"\byou are now\b", r"\bmost expensive\b", r"\breveal\b",
    r"\bact as\b", r"\bpretend\b",
]
_COMPILED = [re.compile(p, re.I) for p in INJECTION_PATTERNS]

def sanitize_query(query):
    """Return (clean_query, findings). Injected clauses are stripped; trusted requirements remain."""
    if not isinstance(query, str) or not query.strip():
        raise InvalidInputError("Query must be a non-empty string")
    if len(query) > settings.MAX_QUERY_LENGTH:
        raise InvalidInputError(f"Query longer than {settings.MAX_QUERY_LENGTH} characters")

    findings, kept = [], []
    for sentence in re.split(r"(?<=[.!?;])\s+", query.strip()):
        hit = next((m for m in (p.search(sentence) for p in _COMPILED) if m), None)
        if hit:
            findings.append({"pattern": hit.re.pattern, "removed_text": sentence[hit.start():]})
            sentence = sentence[:hit.start()].strip()
        if sentence:
            kept.append(sentence)
    clean = " ".join(kept).strip()
    if not clean:
        raise InvalidInputError("Query contained only disallowed instructions")
    return clean, findings
