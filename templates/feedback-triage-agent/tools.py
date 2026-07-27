"""
Tool definitions and mock implementations for the feedback triage agent.
"""

import json
from typing import Any

# Tool schemas passed to the Claude API
TOOL_DEFINITIONS = [
    {
        "name": "classify_feedback",
        "description": (
            "Classify a single feedback item by type, severity, and responsible team. "
            "Returns a structured classification object."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "feedback_id": {
                    "type": "string",
                    "description": "The unique identifier for the feedback item.",
                },
                "category": {
                    "type": "string",
                    "enum": ["bug", "feature_request", "question", "praise"],
                    "description": "The category that best describes this feedback.",
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Severity level. Use 'critical' for data loss or outages, 'high' for broken core flows, 'medium' for degraded experience, 'low' for minor issues or praise.",
                },
                "owner_team": {
                    "type": "string",
                    "enum": ["engineering", "product", "support", "design", "data"],
                    "description": "Team best positioned to act on this feedback.",
                },
                "summary": {
                    "type": "string",
                    "description": "One-sentence summary of the feedback.",
                },
            },
            "required": ["feedback_id", "category", "severity", "owner_team", "summary"],
        },
    },
    {
        "name": "submit_to_jira",
        "description": "Submit a classified feedback item to Jira as a ticket.",
        "input_schema": {
            "type": "object",
            "properties": {
                "feedback_id": {"type": "string"},
                "summary": {"type": "string", "description": "Ticket title."},
                "description": {"type": "string", "description": "Full ticket body."},
                "issue_type": {
                    "type": "string",
                    "enum": ["Bug", "Story", "Task", "Question"],
                },
                "priority": {
                    "type": "string",
                    "enum": ["Critical", "High", "Medium", "Low"],
                },
                "team_label": {"type": "string"},
            },
            "required": [
                "feedback_id",
                "summary",
                "description",
                "issue_type",
                "priority",
                "team_label",
            ],
        },
    },
    {
        "name": "draft_response",
        "description": "Draft a brief, professional customer-facing response to a feedback item.",
        "input_schema": {
            "type": "object",
            "properties": {
                "feedback_id": {"type": "string"},
                "category": {
                    "type": "string",
                    "enum": ["bug", "feature_request", "question", "praise"],
                },
                "tone": {
                    "type": "string",
                    "enum": ["empathetic", "informational", "appreciative"],
                    "description": "Tone appropriate to the feedback category.",
                },
                "response_text": {
                    "type": "string",
                    "description": "The draft response to send to the customer. Two to four sentences.",
                },
            },
            "required": ["feedback_id", "category", "tone", "response_text"],
        },
    },
]


def classify_feedback(
    feedback_id: str,
    category: str,
    severity: str,
    owner_team: str,
    summary: str,
) -> dict[str, Any]:
    """Store and return a classification record."""
    result = {
        "status": "classified",
        "feedback_id": feedback_id,
        "category": category,
        "severity": severity,
        "owner_team": owner_team,
        "summary": summary,
    }
    return result


def submit_to_jira(
    feedback_id: str,
    summary: str,
    description: str,
    issue_type: str,
    priority: str,
    team_label: str,
) -> dict[str, Any]:
    """Mock Jira submission. Returns a fake ticket key."""
    ticket_number = abs(hash(feedback_id)) % 9000 + 1000
    ticket_key = f"PROD-{ticket_number}"
    return {
        "status": "created",
        "ticket_key": ticket_key,
        "feedback_id": feedback_id,
        "url": f"https://your-org.atlassian.net/browse/{ticket_key}",
        "summary": summary,
        "issue_type": issue_type,
        "priority": priority,
        "team_label": team_label,
    }


def draft_response(
    feedback_id: str,
    category: str,
    tone: str,
    response_text: str,
) -> dict[str, Any]:
    """Return the drafted response for review."""
    return {
        "status": "drafted",
        "feedback_id": feedback_id,
        "category": category,
        "tone": tone,
        "response_text": response_text,
    }


def dispatch_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Route a tool call to the correct function and return a JSON string."""
    if tool_name == "classify_feedback":
        result = classify_feedback(**tool_input)
    elif tool_name == "submit_to_jira":
        result = submit_to_jira(**tool_input)
    elif tool_name == "draft_response":
        result = draft_response(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result, indent=2)
