"""Shared workflow state with write-permission enforcement and requirement-integrity lock."""
import hashlib, json, threading, uuid
from config.permissions import WRITE_PERMISSIONS
from core.exceptions import UnauthorizedStateWrite, SecurityViolation
from core.logger import log_event
from core.metrics import Metrics
from core.tracer import Tracer
from core.messages import AgentMessage

class WorkflowState:
    def __init__(self, user_query):
        self.workflow_id = uuid.uuid4().hex[:8]
        self.user_query = user_query
        self.sanitized_query = None
        self.requirements = None
        self._req_hash = None            # set once requirements are locked
        self.plan = None
        self.routing = None
        self.messages = []
        self.search_results = {}         # {source: [products]}
        self.merged_results = []
        self.conflicts = []
        self.filtered_results = []
        self.rejected_results = []
        self.comparison = None
        self.ranking = []
        self.validation = {}             # {stage: {passed, issues}}
        self.supervisor_decision = None
        self.human_approval = None
        self.final_recommendation = None
        self.errors = []
        self.security_events = []
        self.reanalysis_count = 0
        self.status = "created"
        self.tracer = Tracer()
        self.metrics = Metrics()
        self._lock = threading.RLock()

    # ---- guarded writes ----------------------------------------------------
    def write(self, role, key, value, sub=None):
        allowed = WRITE_PERMISSIONS.get(role, set())
        with self._lock:
            if key not in allowed:
                self.add_security_event("unauthorized_state_write", role=role, key=key)
                raise UnauthorizedStateWrite(f"Role '{role}' may not write '{key}'")
            if key == "requirements" and self._req_hash is not None:
                self.add_security_event("requirement_manipulation_blocked", role=role)
                raise SecurityViolation("Requirements are locked and cannot be modified")
            if sub is not None:
                getattr(self, key)[sub] = value
            else:
                setattr(self, key, value)
            if key == "requirements":
                self._req_hash = self._hash(value)

    @staticmethod
    def _hash(req):
        return hashlib.sha256(json.dumps(req, sort_keys=True, default=str).encode()).hexdigest()

    def verify_requirements_integrity(self):
        """False if requirements were changed after being locked (e.g., direct tampering)."""
        return self._req_hash is not None and self._hash(self.requirements) == self._req_hash

    # ---- bookkeeping ---------------------------------------------------------
    def add_message(self, sender, receiver, task, input_summary, output_summary, status):
        with self._lock:
            self.messages.append(AgentMessage(sender, receiver, task, input_summary, output_summary, status).to_dict())

    def add_error(self, agent, error):
        with self._lock:
            self.errors.append({"agent": agent, "error": str(error)})
        log_event(self.workflow_id, "error", agent=agent, error=str(error))

    def add_security_event(self, kind, **details):
        with self._lock:
            self.security_events.append({"type": kind, **details})
        log_event(self.workflow_id, "security_event", type=kind, **details)
