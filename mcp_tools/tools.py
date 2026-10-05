"""Tool implementations (pure functions). Agents reach them only through the ToolRegistry."""
import json, re, time
from config import settings
from core.failure import injector
from core.exceptions import InvalidInputError

_CACHE = None

def _load_products():
    global _CACHE
    if _CACHE is None:
        with open(settings.DATA_FILE, encoding="utf-8") as f:
            _CACHE = json.load(f)
    return _CACHE

# ---------------------------------------------------------------- planning_tool
def planning_tool(query):
    """Natural language -> structured requirements."""
    q = query.lower()
    req = {"category": None, "max_budget": None, "min_ram_gb": None, "min_storage_gb": None, "min_rating": None}

    for word, cat in settings.CATEGORY_KEYWORDS.items():
        if word in q:
            req["category"] = cat
            break

    m = re.search(r"(?:under|below|within|upto|up to|max(?:imum)?|less than|<=?)\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(k)?\b", q)
    if not m:
        m = re.search(r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(k)?", q)
    if m:
        val = float(m.group(1).replace(",", ""))
        req["max_budget"] = int(val * 1000 if m.group(2) else val)

    m = re.search(r"(\d+)\s*gb\s*(?:of\s*)?ram", q) or re.search(r"ram\s*(?:of|:)?\s*(\d+)\s*gb", q)
    if m:
        req["min_ram_gb"] = int(m.group(1))

    m = re.search(r"(\d+(?:\.\d+)?)\s*(gb|tb)\s*(?:ssd|hdd|storage|rom)", q) or \
        re.search(r"(?:storage|ssd)\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(gb|tb)", q)
    if m:
        val = float(m.group(1))
        req["min_storage_gb"] = int(val * 1024 if m.group(2) == "tb" else val)

    m = re.search(r"rating\s*(?:of\s*)?(?:above|over|at least|>=|greater than|min(?:imum)?)?\s*(\d(?:\.\d+)?)", q) or \
        re.search(r"(\d(?:\.\d+)?)\s*(?:\+|stars?)", q)
    if m:
        req["min_rating"] = float(m.group(1))

    if req["category"] is None:
        raise InvalidInputError("Planner could not identify a product category in the query")
    return req

# ------------------------------------------------------------------ search_tool
def search_tool(source, requirements):
    """Return candidate products (category match only) from one store/source."""
    time.sleep(settings.SEARCH_LATENCY)          # simulated network latency
    injector.check(f"search:{source}")
    cat = requirements.get("category")
    return [dict(p) for p in _load_products() if p["source"] == source and (cat is None or p["category"] == cat)]

# ------------------------------------------------------------------ filter_tool
def check_constraints(p, req):
    """Return list of violated constraints (empty = product satisfies everything)."""
    reasons = []
    if req.get("max_budget") is not None and p["price"] > req["max_budget"]:
        reasons.append(f"price {p['price']} > budget {req['max_budget']}")
    if req.get("min_ram_gb") is not None and p["ram_gb"] < req["min_ram_gb"]:
        reasons.append(f"RAM {p['ram_gb']}GB < {req['min_ram_gb']}GB")
    if req.get("min_storage_gb") is not None and p["storage_gb"] < req["min_storage_gb"]:
        reasons.append(f"storage {p['storage_gb']}GB < {req['min_storage_gb']}GB")
    if req.get("min_rating") is not None and p["rating"] < req["min_rating"]:
        reasons.append(f"rating {p['rating']} < {req['min_rating']}")
    if not p.get("in_stock", True):
        reasons.append("out of stock")
    return reasons

def filter_tool(products, requirements):
    kept, rejected = [], []
    for p in products:
        reasons = check_constraints(p, requirements)
        (rejected if reasons else kept).append({"product": p, "reasons": reasons} if reasons else p)
    return {"kept": kept, "rejected": rejected}

# ------------------------------------------------------------ comparison_tool
def comparison_tool(products, requirements):
    if not products:
        return {"table": [], "best": {}, "summary": "No products to compare"}
    table = [{**p, "value_ratio": round((p["ram_gb"] + p["storage_gb"] / 64) / (p["price"] / 10000), 3)} for p in products]
    best = {
        "lowest_price": min(table, key=lambda p: p["price"])["name"],
        "highest_rating": max(table, key=lambda p: p["rating"])["name"],
        "most_ram": max(table, key=lambda p: p["ram_gb"])["name"],
        "most_storage": max(table, key=lambda p: p["storage_gb"])["name"],
        "best_value": max(table, key=lambda p: p["value_ratio"])["name"],
    }
    return {"table": table, "best": best, "summary": f"Compared {len(table)} products"}

# -------------------------------------------------------------- ranking_tool
def ranking_tool(products, requirements, weights=None):
    """Transparent scoring: each metric is min-max normalised across the candidate set
    (price inverted: cheaper = better), then weighted. Every score ships with its reasons."""
    weights = weights or settings.RANK_WEIGHTS
    if not products:
        return []

    def norm(key, invert=False):
        vals = [p[key] for p in products]
        lo, hi = min(vals), max(vals)
        if hi == lo:
            return {id(p): 1.0 for p in products}
        return {id(p): ((hi - p[key]) if invert else (p[key] - lo)) / (hi - lo) for p in products}

    n = {"price": norm("price", invert=True), "rating": norm("rating"),
         "ram": norm("ram_gb"), "storage": norm("storage_gb")}
    req = requirements
    scored = []
    for p in products:
        parts = {k: round(weights[k] * n[k][id(p)] * 100, 2) for k in weights}
        reasons = [
            f"price Rs.{p['price']:,}" + (f" (budget Rs.{req['max_budget']:,})" if req.get("max_budget") else ""),
            f"rating {p['rating']}" + (f" (min {req['min_rating']})" if req.get("min_rating") else ""),
            f"RAM {p['ram_gb']}GB" + (f" (min {req['min_ram_gb']}GB)" if req.get("min_ram_gb") else ""),
            f"storage {p['storage_gb']}GB" + (f" (min {req['min_storage_gb']}GB)" if req.get("min_storage_gb") else ""),
            "weights " + ", ".join(f"{k}={int(w*100)}%" for k, w in weights.items()),
        ]
        scored.append({**p, "score": round(sum(parts.values()), 2), "score_breakdown": parts, "reasons": reasons})
    scored.sort(key=lambda x: (-x["score"], x["price"]))
    for i, p in enumerate(scored, 1):
        p["rank"] = i
    return scored

# ----------------------------------------------------------- validation_tool
def validation_tool(stage, data, requirements):
    issues = []
    if stage == "requirements":
        if not requirements or not requirements.get("category"):
            issues.append("category missing")
        if not any(requirements.get(k) is not None for k in ("max_budget", "min_ram_gb", "min_storage_gb", "min_rating")):
            issues.append("no constraints extracted")
        for k in ("max_budget", "min_ram_gb", "min_storage_gb", "min_rating"):
            v = requirements.get(k)
            if v is not None and v <= 0:
                issues.append(f"{k} must be positive")
    elif stage in ("filtering", "ranking"):
        for p in data:
            missing = [f for f in settings.REQUIRED_PRODUCT_FIELDS if p.get(f) is None]
            if missing:
                issues.append(f"{p.get('name', '?')}: missing {missing}")
                continue
            for r in check_constraints(p, requirements):
                issues.append(f"{p['name']}: violates {r}")
        if stage == "ranking":
            scores = [p.get("score") for p in data]
            if any(s is None for s in scores):
                issues.append("ranking: score missing")
            elif scores != sorted(scores, reverse=True):
                issues.append("ranking: not sorted by score")
            if [p.get("rank") for p in data] != list(range(1, len(data) + 1)):
                issues.append("ranking: rank numbers inconsistent")
            if any(not p.get("reasons") for p in data):
                issues.append("ranking: missing selection reasoning")
    else:
        issues.append(f"unknown validation stage '{stage}'")
    return {"stage": stage, "passed": not issues, "issues": issues}

# ------------------------------------------------------ workflow_control_tool
def workflow_control_tool(action, **info):
    if action == "review":
        if info["fatal_errors"]:
            return {"action": "abort", "reason": "fatal errors present"}
        if not info["validation_passed"]:
            if info["reanalysis_count"] < settings.MAX_REANALYSIS:
                return {"action": "retry_analysis", "reason": "validation failed - re-running analysis"}
            return {"action": "escalate_to_human", "reason": "validation failed after reanalysis", "validation_failed": True}
        if not info["has_results"]:
            return {"action": "escalate_to_human", "reason": "no products satisfy the requirements"}
        return {"action": "escalate_to_human", "reason": "validated result ready for approval"}
    if action == "finalize":
        if info["approval"] != "approved":
            return {"status": info["approval"] or "not_approved"}
        if info["validation_failed"]:
            return {"status": "blocked_validation_failed"}
        return {"status": "approved" if info["has_results"] else "no_match"}
    raise InvalidInputError(f"unknown workflow action '{action}'")
