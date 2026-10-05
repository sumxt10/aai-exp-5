"""Role-based permissions (least privilege)."""

# Which tools each agent role may execute (Tool Authorization table)
TOOL_PERMISSIONS = {
    "planner":      {"planning_tool"},
    "router":       set(),
    "search":       {"search_tool"},
    "synchronizer": set(),
    "filter":       {"filter_tool"},
    "comparison":   {"comparison_tool"},
    "ranking":      {"ranking_tool"},
    "validator":    {"validation_tool"},
    "supervisor":   {"workflow_control_tool"},
}

# Which shared-state keys each role may write
WRITE_PERMISSIONS = {
    "system":       {"sanitized_query"},
    "planner":      {"requirements", "plan"},
    "router":       {"routing"},
    "search":       {"search_results"},
    "synchronizer": {"merged_results", "conflicts"},
    "filter":       {"filtered_results", "rejected_results"},
    "comparison":   {"comparison"},
    "ranking":      {"ranking"},
    "validator":    {"validation"},
    "supervisor":   {"supervisor_decision", "final_recommendation"},
    "human":        {"human_approval"},
}
