"""Least-privilege tool authorization."""
from config.permissions import TOOL_PERMISSIONS

def is_authorized(role, tool_name):
    return tool_name in TOOL_PERMISSIONS.get(role, set())
