import sys, pathlib, pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from config import settings
from core.failure import injector

@pytest.fixture(autouse=True)
def fast_and_clean():
    old = settings.SEARCH_LATENCY
    settings.SEARCH_LATENCY = 0.05
    injector.reset()
    yield
    injector.reset()
    settings.SEARCH_LATENCY = old
