"""Central configuration for the multi-agent e-commerce pipeline."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "products.json"
LOG_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "outputs"

# ---- Search ---------------------------------------------------------------
SEARCH_SOURCES = ["StoreA", "StoreB", "StoreC"]          # one Search Agent per source
TRUSTED_SOURCE_PRIORITY = ["StoreA", "StoreB", "StoreC"]  # used for conflict resolution
SEARCH_LATENCY = 0.5   # seconds; simulates network delay so parallel speedup is measurable

# ---- Retry / reanalysis ---------------------------------------------------
MAX_RETRIES = 2
MAX_REANALYSIS = 1

# ---- Experimental cost units ----------------------------------------------
COST_UNITS = {
    "agent_call": 1.0,
    "tool_call": 2.0,
    "retry": 3.0,
    "processing_op": 0.05,   # per item processed by a tool
}

# ---- Ranking weights (must sum to 1.0) ------------------------------------
RANK_WEIGHTS = {"price": 0.30, "rating": 0.30, "ram": 0.20, "storage": 0.20}

# ---- Planner vocabulary ----------------------------------------------------
CATEGORY_KEYWORDS = {
    "laptop": "laptop", "notebook": "laptop",
    "smartphone": "smartphone", "phone": "smartphone", "mobile": "smartphone",
}

REQUIRED_PRODUCT_FIELDS = ["id", "name", "brand", "price", "ram_gb", "storage_gb", "rating"]
MAX_QUERY_LENGTH = 500
VERBOSE = False   # True -> also print log events to console
