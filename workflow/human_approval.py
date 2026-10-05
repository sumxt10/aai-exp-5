"""Human-in-the-loop governance gate."""
import time

class HumanApproval:
    """Modes: 'auto' (approve), 'reject', 'reanalyze_once', 'interactive' (asks on console)."""
    def __init__(self, mode="auto"):
        self.mode, self._reanalysed = mode, False

    def request(self, state):
        if self.mode == "auto":
            return self._resp("approved", "auto-approved (test mode)")
        if self.mode == "reject":
            return self._resp("rejected", "auto-rejected (test mode)")
        if self.mode == "reanalyze_once":
            if not self._reanalysed:
                self._reanalysed = True
                return self._resp("reanalyze", "requested another analysis")
            return self._resp("approved", "approved after reanalysis")
        return self._interactive(state)

    def _resp(self, status, comment):
        return {"status": status, "comment": comment, "mode": self.mode, "timestamp": time.time()}

    def _interactive(self, state):
        print("\n=== HUMAN APPROVAL REQUIRED ===")
        print("Supervisor:", state.supervisor_decision)
        for p in state.ranking[:3]:
            print(f"  #{p['rank']} {p['name']}  Rs.{p['price']:,}  score={p['score']}")
        while True:
            c = input("[a]pprove  [r]eject  [n] another analysis  [v]iew reasoning  [i]ncorrect info > ").strip().lower()
            if c == "a": return self._resp("approved", "approved by human")
            if c == "r": return self._resp("rejected", "rejected by human")
            if c == "n": return self._resp("reanalyze", "human requested another analysis")
            if c == "i": return self._resp("rejected", "incorrect info: " + input("describe the issue: "))
            if c == "v":
                for p in state.ranking[:3]:
                    print(f"  #{p['rank']} {p['name']}: " + "; ".join(p["reasons"]))
