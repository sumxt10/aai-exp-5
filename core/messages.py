"""Structured inter-agent message: Agent -> Task -> Input -> Output -> Status."""
import time
from dataclasses import dataclass, field, asdict

@dataclass
class AgentMessage:
    sender: str
    receiver: str
    task: str
    input_summary: str
    output_summary: str
    status: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return asdict(self)
