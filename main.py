"""CLI entry point.
Examples:
  python main.py
  python main.py --query "Find laptops under ₹60,000 with 16 GB RAM" --approval interactive
  python main.py --mode sequential --inject search:StoreB=1
  python main.py --security-tests
"""
import argparse
from config import settings
from core.failure import injector
from workflow.orchestrator import Orchestrator
from workflow.report import print_report, save_report

DEFAULT_QUERY = "Find laptops under ₹70,000 with at least 16 GB RAM, 512 GB storage and rating above 4.2."

def main():
    ap = argparse.ArgumentParser(description="Multi-agent e-commerce recommendation pipeline")
    ap.add_argument("--query", default=DEFAULT_QUERY)
    ap.add_argument("--mode", choices=["parallel", "sequential"], default="parallel")
    ap.add_argument("--approval", choices=["auto", "interactive", "reject", "reanalyze_once"], default="auto")
    ap.add_argument("--inject", action="append", default=[],
                    help="failure injection 'key=N' (transient N times) or 'key=permanent', e.g. search:StoreB=1")
    ap.add_argument("--verbose", action="store_true", help="print log events")
    ap.add_argument("--security-tests", action="store_true")
    args = ap.parse_args()

    settings.VERBOSE = args.verbose
    if args.security_tests:
        from security.security_tests import run_security_tests
        summary, _ = run_security_tests()
        print("Security Test Result:", summary)
        return

    for rule in args.inject:
        key, _, val = rule.partition("=")
        injector.add(key, permanent=(val == "permanent"), times=1 if val == "permanent" else int(val or 1))

    state = Orchestrator(parallel=(args.mode == "parallel"), approval_mode=args.approval).run(args.query)
    print_report(state)
    print("Report saved to:", save_report(state))

if __name__ == "__main__":
    main()
