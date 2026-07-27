"""
Data Explorer Agent

Accepts a natural language question, translates it to SQL, runs it against a
local SQLite database, and iterates if the results need clarification.

Usage:
    python agent.py "How many users signed up each month in 2023?"
    python agent.py "Which plan generates the most revenue?" --model claude-haiku-4-5
    python agent.py  # runs a default demo question
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

SYSTEM_PROMPT = """You are a data analyst assistant with access to a SQLite database containing product metrics.

Tables available:
- users       — user accounts with plan, country, signup date, and active status
- events      — product usage events (page_view, export_pdf, api_call, feature_used, signup, upgrade_plan)
- revenue     — monthly revenue records per user and plan
- features    — product features with launch date, status, and owner team

Approach:
1. If you are not sure of exact column names, call get_schema first.
2. Write a precise SQL SELECT query and call run_sql_query.
3. If the result is empty or ambiguous, revise the query and try again.
4. Once you have good data, interpret it clearly in plain language for a non-technical audience.
5. If the question cannot be answered with the available data, say so directly.

Always explain what each query is doing in the 'explanation' field."""


def run_agent(question: str, model: str) -> None:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages: list[dict] = [{"role": "user", "content": question}]

    console.print(Panel(f'[bold]Question:[/bold] {question}', title="Data Explorer Agent", style="blue"))

    iteration = 0
    max_iterations = 20

    while iteration < max_iterations:
        iteration += 1

        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "run_sql_query":
                    console.print(f"\n[cyan]SQL query:[/cyan] {block.input.get('explanation', '')}")
                    sql = block.input.get("query", "")
                    console.print(Syntax(sql, "sql", theme="monokai", word_wrap=True))
                elif block.name == "get_schema":
                    console.print(f"\n[cyan]Fetching schema for:[/cyan] {block.input.get('table_name')}")

                result_str = dispatch_tool(block.name, block.input)
                result_data = json.loads(result_str)

                if block.name == "run_sql_query" and "row_count" in result_data:
                    console.print(f"[green]Rows returned:[/green] {result_data['row_count']}")

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    }
                )
            elif block.type == "text" and block.text.strip():
                console.print(Panel(block.text, title="Answer", style="green"))

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    console.print(f"\n[dim]Completed in {iteration} iteration(s)[/dim]")


DEFAULT_QUESTION = "What are the top three most-used product features, and which team owns each one?"


@click.command()
@click.argument("question", default=DEFAULT_QUESTION)
@click.option(
    "--model",
    default="claude-opus-4-5",
    show_default=True,
    help="Claude model to use.",
)
def main(question: str, model: str) -> None:
    if "ANTHROPIC_API_KEY" not in os.environ:
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable is not set.[/red]")
        sys.exit(1)

    run_agent(question, model)


if __name__ == "__main__":
    main()
