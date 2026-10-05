from agents.base_agent import BaseAgent
from core.exceptions import InvalidInputError

class ValidatorAgent(BaseAgent):
    """Checkpoint validation: requirements -> filtering -> ranking."""
    name, role = "ValidatorAgent", "validator"

    def execute(self, state, task, label, span, stage=None, **kw):
        data = {"requirements": None, "filtering": state.filtered_results, "ranking": state.ranking}.get(stage)
        result = self.call_tool(state, "validation_tool", span, stage=stage, data=data, requirements=state.requirements)
        if not state.verify_requirements_integrity():          # shared-state manipulation check
            result["passed"] = False
            result["issues"].append("requirements were modified after being locked (tampering)")
            state.add_security_event("requirement_tampering_detected", stage=stage)
        state.write("validator", "validation", result, sub=stage)
        if stage == "requirements" and not result["passed"]:
            raise InvalidInputError(f"Requirement validation failed: {result['issues']}")
        return result
