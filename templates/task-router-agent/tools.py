"""
Tool definitions and implementations for the task router agent.
"""

import json
from typing import Any

TOOL_DEFINITIONS = [
    {
        "name": "route_task",
        "description": "Route a single task to the team best positioned to handle it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "team": {
                    "type": "string",
                    "enum": ["engineering", "design", "product", "support"],
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                },
                "rationale": {
                    "type": "string",
                    "description": "One-sentence reason for the routing decision.",
                },
            },
            "required": ["task_id", "team", "confidence", "rationale"],
        },
    },
    {
        "name": "flag_for_review",
        "description": "Flag a task for human review when routing confidence is low or the task spans multiple teams.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["task_id", "reason"],
        },
    },
    {
        "name": "write_routing_report",
        "description": "Write the final routing report once every task has been routed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Short prose summary of how tasks were distributed across teams.",
                },
            },
            "required": ["summary"],
        },
    },
]

_ROUTED: list[dict[str, Any]] = []
_FLAGGED: list[dict[str, Any]] = []


def reset_state() -> None:
    global _ROUTED, _FLAGGED
    _ROUTED = []
    _FLAGGED = []


def route_task(task_id: str, team: str, confidence: str, rationale: str) -> dict[str, Any]:
    record = {"task_id": task_id, "team": team, "confidence": confidence, "rationale": rationale}
    _ROUTED.append(record)
    return {"status": "routed", **record}


def flag_for_review(task_id: str, reason: str) -> dict[str, Any]:
    record = {"task_id": task_id, "reason": reason}
    _FLAGGED.append(record)
    return {"status": "flagged", **record}


def write_routing_report(summary: str) -> dict[str, Any]:
    by_team: dict[str, int] = {}
    for r in _ROUTED:
        by_team[r["team"]] = by_team.get(r["team"], 0) + 1
    return {
        "status": "report_written",
        "summary": summary,
        "routed_count": len(_ROUTED),
        "by_team": by_team,
        "flagged_count": len(_FLAGGED),
        "flagged": _FLAGGED,
    }


def dispatch_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name == "route_task":
        result = route_task(**tool_input)
    elif tool_name == "flag_for_review":
        result = flag_for_review(*ª'tool_input)
    elif tool_name == "write_routing_report":
        result = write_routing_report(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result, indent=2)
