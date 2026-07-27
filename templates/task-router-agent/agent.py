"""
Task Router Agent

Reads a list of tasks (JSON file or stdin) and routes each one to the team
best positioned to handle it, then writes a routing report.

Usage:
    python agent.py --tasks examples/tasks.json
    cat examples/tasks.json | python agent.py
    python agent.py --tasks examples/tasks.json --model claude-haiku-4-5
"""

import json
import os
import sys

import anthropic
import click
from rich.console import Console
from rich.panel import Panel

from tools import TOOL_DEFINITIONS, dispatch_tool, reset_state

console = Console()

SYSTEM_PROMPT = """You are a task routing assistant for a product organization.

For every task you receive:
1. Read the title and description.
2. Call route_task with the owning team (engineering, design, product, or support), a confidence level, and a one-sentence rationale.
3. If confidence is low or the task clearly spans multiple teams, also call flag_for_review with a short reason.

Once every task has been routed, call write_routing_report exactly once with a short prose summary of how work was distributed."""


def run_agent(tasks: list[dict], model: str) -> None:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    reset_state()

    user_message = f"Route the following {len(tasks)} tasks:\n\n" + json.dumps(tasks, indent=2)
    messages: list[dict] = [{"role": "user", "content": user_message}]

    console.print(Panel(f"Routing [bold]{len(tasks)}[/bold] tasks", title="Task Router Agent", style="blue"))

    iteration = 0
    max_iterations = 30

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
                result_str = dispatch_tool(block.name, block.input)
                result_data = json.loads(result_str)

                if block.name == "route_task":
                    console.print(
                        f"  [cyan]Tool:[/cyan] route_task -> {result_data['task_id']} "
                        f"routed to {result_data['team']} (confidence: {result_data['confidence']})"
                    )
                elif block.name == "flag_for_review":
                    console.print(
                        f"  [yellow]Tool:[/yellow] flag_for_review -> {result_data['task_id']} ({result_data['reason']})"
                    )
                elif block.name == "write_routing_report":
                    console.print("  [cyan]Tool:[/cyan] write_routing_report")

                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result_str}
                )
            elif block.type == "text" and block.text.strip():
                console.print(Panel(block.text, title="Agent Note", style="green"))

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    console.print(f"\n[dim]Completed in {iteration} iteration(s)[/dim]")


@click.command()
@click.option("--tasks", default=None, help="Path to a JSON file of tasks. Reads stdin if omitted.")
@click.option("--model", default="claude-opus-4-5", show_default=True, help="Claude model to use.")
def main(tasks: str, model: str) -> None:
    if "ANTHROPIC_API_KEY" not in os.environ:
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable is not set.[/red]")
        sys.exit(1)

    if tasks:
        with open(tasks) as f:
            task_list = json.load(f)
    else:
        task_list = json.load(sys.stdin)

    run_agent(task_list, model)


if __name__ == "__main__":
    main()
