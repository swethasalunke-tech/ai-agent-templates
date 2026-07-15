"""
Weekly Report Agent

Given a project name, autonomously fetches Jira tickets, loads a metrics CSV,
synthesizes both sources into a narrative, and formats the output for Slack.

Demonstrates multi-tool orchestration in a single agent loop where the agent
decides the order and combination of tool calls.

Usage:
    python agent.py --project PROD --metrics examples/metrics_sample.csv
    python agent.py --project INFRA --week-ending 2025-04-25
    python agent.py --project DATA --metrics examples/metrics_sample.csv --model claude-haiku-4-5
"""

import json
import os
import sys

import anthropic
import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from tools import TOOL_DEFINITIONS, dispatch_tool

console = Console()

SYSTEM_PROMPT = """You are a product manager assistant that writes concise, data-driven weekly reports.

Your process for every report request:
1. Call fetch_jira_tickets for the given project with days=7. Fetch all statuses.
2. Call load_metrics_csv with the provided filepath to load the week's metrics.
3. Analyze both sources: identify the most meaningful metric movements, note completed and in-progress work, and flag any risks visible in the data.
4. Call format_for_slack with a synthesized report. The headline should capture the single most important story. Metrics highlights should be three to five specific, quantified observations (include the actual numbers and percent changes). Shipped items should reference ticket keys. Next week focus should be informed by in-progress tickets and any metric trends that need attention.

Be specific and direct. Avoid generic language like "continued progress" or "ongoing work." Every bullet should contain a real data point or a concrete work item."""


def run_agent(project: str, metrics_filepath: str, week_ending: str, model: str) -> None:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_message = (
        f"Write the weekly report for project {project}.\n"
        f"Metrics file: {metrics_filepath}\n"
        f"Week ending: {week_ending}\n"
        "Fetch the Jira tickets, load the metrics, synthesize everything, and format for Slack."
    )

    messages: list[dict] = [{"role": "user", "content": user_message}]

    console.print(
        Panel(
            f"Generating weekly report for [bold]{project}[/bold] | week ending {week_ending}",
            title="Weekly Report Agent",
            style="blue",
        )
    )

    iteration = 0
    max_iterations = 20
    final_slack_message: str | None = None

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
                console.print(f"  [cyan]Tool:[/cyan] {block.name}")

                result_str = dispatch_tool(block.name, block.input)
                result_data = json.loads(result_str)

                if block.name == "fetch_jira_tickets":
                    console.print(f"  [green]Tickets retrieved:[/green] {result_data.get('ticket_count', 0)}")
                elif block.name == "load_metrics_csv":
                    console.print(f"  [green]Metrics rows loaded:[/green] {result_data.get('row_count', 0)}")
                elif block.name == "format_for_slack":
                    final_slack_message = result_data.get("slack_message")
                    console.print(f"  [green]Slack message formatted:[/green] {result_data.get('character_count', 0)} characters")

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    }
                )
            elif block.type == "text" and block.text.strip():
                console.print(Panel(block.text, title="Agent Notes", style="dim"))

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    if final_slack_message:
        console.print(
            Panel(
                final_slack_message,
                title="Slack Message (ready to post)",
                style="green",
                padding=(1, 2),
            )
        )
    else:
        console.print("[yellow]No formatted Slack message was produced.[/yellow]")

    console.print(f"\n[dim]Completed in {iteration} iteration(s)[/dim]")


@click.command()
@click.option(
    "--project",
    default="PROD",
    show_default=True,
    help="Jira project key (PROD, INFRA, or DATA in the mock data).",
)
@click.option(
    "--metrics",
    "metrics_filepath",
    default="examples/metrics_sample.csv",
    show_default=True,
    help="Path to the metrics CSV file.",
)
@click.option(
    "--week-ending",
    default="2025-04-25",
    show_default=True,
    help="ISO date for the week ending (used to filter metrics).",
)
@click.option(
    "--model",
    default="claude-opus-4-5",
    show_default=True,
    help="Claude model to use.",
)
def main(project: str, metrics_filepath: str, week_ending: str, model: str) -> None:
    if "ANTHROPIC_API_KEY" not in os.environ:
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable is not set.[/red]")
        sys.exit(1)

    run_agent(project, metrics_filepath, week_ending, model)


if __name__ == "__main__":
    main()
