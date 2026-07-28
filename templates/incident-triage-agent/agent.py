"""
Incident Triage Agent

Reads incident descriptions, classifies each one by severity (P1-P4), identifies
affected systems, retrieves the relevant runbook, and posts a customer-facing
status update.

Usage:
    python agent.py
    python agent.py --input examples/incidents.json
    python agent.py --single "Auth service returning 503s for all users"
"""

import json
import os
import sys
from pathlib import Path

import anthropic
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tools import TOOL_DEFINITIONS, dispatch_tool

console = Console()

SYSTEM_PROMPT = """You are an incident response assistant for a SaaS product company.

For each incident you receive, follow these steps in order:
1. Call classify_incident to assign severity (P1-P4), identify likely affected systems, and write a one-sentence impact summary.
2. Call lookup_runbook for the primary affected system (the one most central to the incident).
3. Call post_status_update with status 'investigating', a clear headline, and a three to five sentence customer-facing body that states what is affected, what the team is doing, and when the next update will be posted.

Severity guidelines:
- P1: Complete outage or data loss risk affecting all users. Respond immediately.
- P2: Major feature broken or significant portion of users affected.
- P3: Degraded performance, workaround available.
- P4: Single customer affected or minor cosmetic issue.

After processing all incidents, print a brief triage summary table."""


def run_agent(incidents: list[dict], model: str) -> None:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_message = (
        f"Please triage the following {len(incidents)} incident(s).\n\n"
        + json.dumps(incidents, indent=2)
    )

    messages: list[dict] = [{"role": "user", "content": user_message}]

    console.print(
        Panel(
            f"Starting incident triage for [bold]{len(incidents)}[/bold] incident(s)",
            title="Incident Triage Agent",
            style="red",
        )
    )

    iteration = 0
    max_iterations = 60

    while iteration < max_iterations:
        iteration += 1

        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                severity_display = ""
                if block.name == "classify_incident":
                    sev = block.input.get("severity", "")
                    color = {"P1": "red", "P2": "yellow", "P3": "cyan", "P4": "green"}.get(sev, "white")
                    severity_display = f" [[{color}]{sev}[/{color}]]"
                console.print(
                    f"  [cyan]Tool:[/cyan] {block.name}{severity_display} — {block.input.get('incident_id', block.input.get('system_name', ''))}"
                )

                result_str = dispatch_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    }
                )
            elif block.type == "text" and block.text.strip():
                console.print(Panel(block.text, title="Triage Summary", style="yellow"))

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    console.print(f"\n[dim]Completed in {iteration} iteration(s)[/dim]")


@click.command()
@click.option(
    "--input",
    "input_path",
    default="examples/incidents.json",
    show_default=True,
    help="Path to JSON file containing incident descriptions.",
)
@click.option(
    "--single",
    "single_description",
    default=None,
    help="Triage a single incident from a text description instead of a file.",
)
@click.option(
    "--model",
    default="claude-opus-4-5",
    show_default=True,
    help="Claude model to use.",
)
def main(input_path: str, single_description: str | None, model: str) -> None:
    if "ANTHROPIC_API_KEY" not in os.environ:
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable is not set.[/red]")
        sys.exit(1)

    if single_description:
        incidents = [{"id": "INC-ADHOC", "reported_at": "now", "reporter": "cli", "description": single_description}]
    else:
        path = Path(input_path)
        if not path.exists():
            console.print(f"[red]Error: File not found: {input_path}[/red]")
            sys.exit(1)
        incidents = json.loads(path.read_text())

    run_agent(incidents, model)


if __name__ == "__main__":
    main()
