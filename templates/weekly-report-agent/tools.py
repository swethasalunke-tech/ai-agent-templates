"""
Tool definitions and mock implementations for the weekly report agent.

Demonstrates multi-tool orchestration: fetch Jira tickets, load a CSV of
metrics, and format the synthesized result for Slack.
"""

import csv
import json
from pathlib import Path
from typing import Any

TOOL_DEFINITIONS = [
    {
        "name": "fetch_jira_tickets",
        "description": (
            "Fetch Jira tickets for a given project key that were updated or created "
            "within the last N days. Returns a list of ticket summaries."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_key": {
                    "type": "string",
                    "description": "The Jira project key, e.g. 'PROD', 'INFRA', 'DATA'.",
                },
                "days": {
                    "type": "integer",
                    "description": "How many days back to look. Typically 7 for a weekly report.",
                    "minimum": 1,
                    "maximum": 90,
                },
                "status_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of statuses to include, e.g. ['Done', 'In Review']. Empty list returns all statuses.",
                },
            },
            "required": ["project_key", "days"],
        },
    },
    {
        "name": "load_metrics_csv",
        "description": (
            "Load product or business metrics from a CSV file. "
            "Returns all rows as structured records."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to the CSV file, relative to the agent script.",
                },
                "filter_week_ending": {
                    "type": "string",
                    "description": "Optional ISO date string (YYYY-MM-DD) to filter rows by week_ending column.",
                },
            },
            "required": ["filepath"],
        },
    },
    {
        "name": "format_for_slack",
        "description": (
            "Format a weekly report narrative as a Slack message using mrkdwn. "
            "Returns the formatted string ready to post via the Slack API or copy-paste."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "week_ending": {
                    "type": "string",
                    "description": "ISO date of the week ending, e.g. '2025-04-25'.",
                },
                "headline": {
                    "type": "string",
                    "description": "One sentence capturing the most important story of the week.",
                },
                "metrics_highlights": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Three to five bullet points covering key metric movements.",
                },
                "shipped_this_week": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tickets or work items completed this week.",
                },
                "risks_and_blockers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Current risks, blockers, or items needing attention. Can be empty.",
                },
                "next_week_focus": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Two to three priorities for the coming week.",
                },
            },
            "required": [
                "project_name",
                "week_ending",
                "headline",
                "metrics_highlights",
                "shipped_this_week",
                "risks_and_blockers",
                "next_week_focus",
            ],
        },
    },
]

# Mock Jira data keyed by project key
MOCK_JIRA_DATA: dict[str, list[dict[str, str]]] = {
    "PROD": [
        {"key": "PROD-1821", "summary": "Launch bulk-assign GA with permissions guard", "status": "Done", "type": "Story", "assignee": "Alice Chen"},
        {"key": "PROD-1834", "summary": "Fix date picker locale regression in task modal", "status": "Done", "type": "Bug", "assignee": "Bob Martins"},
        {"key": "PROD-1840", "summary": "AI summaries beta: add feedback thumbs UI", "status": "In Review", "type": "Story", "assignee": "Cate Liu"},
        {"key": "PROD-1842", "summary": "Add retry UI for failed PDF exports", "status": "In Progress", "type": "Story", "assignee": "David Park"},
        {"key": "PROD-1815", "summary": "Deprecate time-tracking feature — remove from nav", "status": "Done", "type": "Task", "assignee": "Alice Chen"},
        {"key": "PROD-1850", "summary": "Search latency: add query result caching", "status": "In Review", "type": "Story", "assignee": "Frank Müller"},
        {"key": "PROD-1856", "summary": "P2 post-mortem: export service silent failure", "status": "Done", "type": "Task", "assignee": "Hiro Tanaka"},
    ],
    "INFRA": [
        {"key": "INFRA-302", "summary": "Migrate billing cron job to new scheduler", "status": "Done", "type": "Task", "assignee": "Grace Okonkwo"},
        {"key": "INFRA-310", "summary": "Scale auth-service to handle 2x peak load", "status": "In Progress", "type": "Story", "assignee": "Omar Hassan"},
        {"key": "INFRA-315", "summary": "Enable OTEL tracing on export-service", "status": "In Review", "type": "Task", "assignee": "Nina Patel"},
    ],
    "DATA": [
        {"key": "DATA-88", "summary": "Build weekly active user cohort pipeline", "status": "Done", "type": "Story", "assignee": "Kim Nakamura"},
        {"key": "DATA-91", "summary": "Add revenue churn breakdown by plan to dashboard", "status": "In Review", "type": "Story", "assignee": "Lena Kovač"},
    ],
}


def fetch_jira_tickets(
    project_key: str,
    days: int,
    status_filter: list[str] | None = None,
) -> dict[str, Any]:
    tickets = MOCK_JIRA_DATA.get(project_key.upper(), [])

    if status_filter:
        tickets = [t for t in tickets if t["status"] in status_filter]

    return {
        "project_key": project_key.upper(),
        "days_back": days,
        "status_filter": status_filter or [],
        "ticket_count": len(tickets),
        "tickets": tickets,
    }


def load_metrics_csv(
    filepath: str,
    filter_week_ending: str | None = None,
) -> dict[str, Any]:
    path = Path(filepath)
    if not path.exists():
        # Try relative to the script directory
        path = Path(__file__).parent / filepath

    if not path.exists():
        return {"error": f"File not found: {filepath}"}

    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if filter_week_ending and row.get("week_ending") != filter_week_ending:
                continue
            rows.append(row)

    return {
        "filepath": str(path),
        "row_count": len(rows),
        "records": rows,
    }


def format_for_slack(
    project_name: str,
    week_ending: str,
    headline: str,
    metrics_highlights: list[str],
    shipped_this_week: list[str],
    risks_and_blockers: list[str],
    next_week_focus: list[str],
) -> dict[str, Any]:
    lines = [
        f"*Weekly Report: {project_name}* | Week ending {week_ending}",
        "",
        f"_{headline}_",
        "",
        "*Metrics*",
    ]
    for bullet in metrics_highlights:
        lines.append(f"• {bullet}")

    lines += ["", "*Shipped this week*"]
    for item in shipped_this_week:
        lines.append(f"• {item}")

    if risks_and_blockers:
        lines += ["", "*Risks and blockers*"]
        for item in risks_and_blockers:
            lines.append(f":warning: {item}")

    lines += ["", "*Next week*"]
    for item in next_week_focus:
        lines.append(f"• {item}")

    formatted = "\n".join(lines)
    return {
        "status": "formatted",
        "character_count": len(formatted),
        "slack_message": formatted,
    }


def dispatch_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name == "fetch_jira_tickets":
        result = fetch_jira_tickets(**tool_input)
    elif tool_name == "load_metrics_csv":
        result = load_metrics_csv(**tool_input)
    elif tool_name == "format_for_slack":
        result = format_for_slack(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result, indent=2)
