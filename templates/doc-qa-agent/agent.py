"""
Doc QA Agent

Answers a natural language question about a folder of documents by
retrieving the most relevant chunks and grounding its answer strictly in
that retrieved content.

Usage:
    python agent.py --docs ./docs "What is the refund policy?"
    python agent.py --docs ./docs --model claude-haiku-4-5 "Do you offer annual billing?"
"""

import json
import os
import sys

import anthropic
import click
from rich.console import Console
from rich.panel import Panel

from tools import TOOL_DEFINITIONS, configure_docs, dispatch_tool

console = Console()

SYSTEM_PROMPT = """You are a document QA assistant. You must answer strictly from retrieved content, never from general knowledge.

1. Call list_documents to see what's available in the target folder.
2. Call retrieve_chunks with a search query derived from the question to pull the most relevant passages.
3. If the retrieved chunks don't clearly cover the question, issue a follow-up retrieve_chunks call with a refined query.
4. Answer using only the retrieved chunks, citing the source document for each claim.
5. If the documents don't contain an answer, say so explicitly instead of guessing."""


def run_agent(question: str, model: str) -> None:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages: list[dict] = [{"role": "user", "content": question}]

    console.print(Panel(f"[bold]Question:[/bold] {question}", title="Doc QA Agent", style="blue"))

    iteration = 0
    max_iterations = 10

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
                if block.name == "retrieve_chunks":
                    console.print(f"\n  [cyan]Tool:[/cyan] retrieve_chunks (query: \"{block.input.get('query')}\")")
                else:
                    console.print(f"\n  [cyan]Tool:[/cyan] {block.name}")

                result_str = dispatch_tool(block.name, block.input)
                result_data = json.loads(result_str)

                if block.name == "list_documents":
                    console.print(f"  Documents found: {result_data.get('count', 0)}")
                elif block.name == "retrieve_chunks":
                    console.print(f"  Chunks retrieved: {len(result_data.get('chunks', []))}")

                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result_str}
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


@click.command()
@click.argument("question")
@click.option("--docs", required=True, help="Path to a folder of .txt/.pdf documents.")
@click.option("--model", default="claude-opus-4-5", show_default=True, help="Claude model to use.")
def main(question: str, docs: str, model: str) -> None:
    if "ANTHROPIC_API_KEY" not in os.environ:
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable is not set.[/red]")
        sys.exit(1)

    doc_count = configure_docs(docs)
    if doc_count == 0:
        console.print(f"[red]No .txt or .pdf files found in {docs}[/red]")
        sys.exit(1)

    run_agent(question, model)


if __name__ == "__main__":
    main()
