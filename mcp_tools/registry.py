"""Basic MCP-style tool registry: register -> discover -> select -> authorized execute.
NOTE: simplified; this is NOT the full MCP protocol (see Experiment 06)."""
from dataclasses import dataclass
from typing import Callable
from core.exceptions import UnauthorizedToolAccess, InvalidInputError
from core.logger import log_event
from mcp_tools import tools as T
from mcp_tools.authorization import is_authorized

@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict
    func: Callable

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    # --- registration ---
    def register(self, spec: ToolSpec):
        self._tools[spec.name] = spec

    # --- discovery (like MCP tools/list) ---
    def list_tools(self, role=None):
        return [{"name": t.name, "description": t.description, "input_schema": t.input_schema}
                for t in self._tools.values() if role is None or is_authorized(role, t.name)]

    # --- controlled execution (like MCP tools/call) ---
    def execute(self, state, role, tool_name, span=None, **kwargs):
        if tool_name not in self._tools:
            raise InvalidInputError(f"Tool '{tool_name}' is not registered")
        if not is_authorized(role, tool_name):
            state.add_security_event("unauthorized_tool_access", role=role, tool=tool_name)
            raise UnauthorizedToolAccess(f"Access denied: role '{role}' cannot use '{tool_name}'")
        state.metrics.tool_call()
        if span is not None:
            span["tools"].append(tool_name)
        log_event(state.workflow_id, "tool_call", role=role, tool=tool_name)
        result = self._tools[tool_name].func(**kwargs)
        if isinstance(result, list):
            state.metrics.processing(len(result))
        elif isinstance(result, dict):
            for v in result.values():
                if isinstance(v, list):
                    state.metrics.processing(len(v))
        return result

def build_default_registry():
    reg = ToolRegistry()
    for name, desc, schema, fn in [
        ("planning_tool", "Parse a natural-language query into structured requirements", {"query": "str"}, T.planning_tool),
        ("search_tool", "Search one product source for candidates", {"source": "str", "requirements": "dict"}, T.search_tool),
        ("filter_tool", "Apply user constraints to products", {"products": "list", "requirements": "dict"}, T.filter_tool),
        ("comparison_tool", "Compare products on price/RAM/storage/rating", {"products": "list", "requirements": "dict"}, T.comparison_tool),
        ("ranking_tool", "Score and sort products with explanations", {"products": "list", "requirements": "dict"}, T.ranking_tool),
        ("validation_tool", "Validate data at a workflow checkpoint", {"stage": "str", "data": "any", "requirements": "dict"}, T.validation_tool),
        ("workflow_control_tool", "Supervisor review / finalize decisions", {"action": "str"}, T.workflow_control_tool),
    ]:
        reg.register(ToolSpec(name, desc, schema, fn))
    return reg
