"""
Feedback Triage Agent

Reads a batch of customer feedback items, classifies each one, submits a Jira
ticket, and drafts a customer response — all in a single agentic loop.

Usage:
    python agent.py --input examples/feedback_batch.json
    python agent.py --input examples/feedback_batch.json --model claude-sonnet-4-5
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

SYSTEM_PROMPT = """You are a product operations assistant that triages customer feedback.

For each feedback item you receive, you must:
1. Call classify_feedback with your assessment of category, severity, owner team, and a one-sentence summary.
2. Call submit_to_jira to create a ticket using the classification. Map category to issue_type (bug→Bug, feature_request→Story, question→Task, praise→Task). Map severity to priority (critical→Critical, high→High, medium→Medium, low→Low).
3. Call draft_response to write a short, professional customer-facing reply.

Process every item in the batch. Do not skip any. After processing all items, provide a brief summary table of what was triaged."""


def run_agent(feedback_items: list[dict], model: str) -> None:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_message = (
        f"Please triage the following {len(feedback_items)} customer feedback items.\n\n"
        + json.dumps(feedback_items, indent=2)
    )

    messages: list[dict] = [{"role": "user", "content": user_message}]

    console.print(
        Panel(
            f"Starting feedback triage for [bold]{len(feedback_items)}[/bold] items",
            title="Feedback Triage Agent",
            style="blue",
        )
    )

    iteration = 0
    max_iterations = 50  # guard against runaway loops

    while iteration < max_iterations:
        iteration += 1

        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # Collect all tool uses and text blocks from this response
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                console.print(
                    f"  [cyan]Tool call:[/cyan] {block.name}({json.dumps(block.input, separators=(',', ':'))})"
                )
                result_str = dispatch_tool(block.name, block.input)
                result_data = json.loads(result_str)
                console.print(f"  [green]Result:[/green] {result_data.get('status', 'ok')}")

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    }
                )
            elif block.type == "text" and block.text.strip():
                console.print(Panel(block.text, title="Agent Summary", style="green"))

        # Append the assistant turn
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            # No tool results and not end_turn — something unexpected
            break

    console.print(f"\n[dim]Completed in {iteration} iteration(s)[/dim]")


@click.command()
@click.option(
    "--input",
    "input_path",
    default="examples/feedback_batch.json",
    show_default=True,
    help="Path to JSON file containing feedback items.",
)
@click.option(
    "--model",
    default="claude-opus-4-5",
    show_default=True,
    help="Claude model to use.",
)
def main(input_path: str, model: str) -> None:
    if "ANTHROPIC_API_KEY" not in os.environ:
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable is not set.[/red]")
        sys.exit(1)

    path = Path(input_path)
    if not path.exists():
        console.print(f"[red]Error: File not found: {input_path}[/red]")
        sys.exit(1)

    feedback_items = json.loads(path.read_text())
    run_agent(feedback_items, model)


if __name__ == "__main__":
    main()
