# ai-agent-templates

A collection of practical, working agent patterns for product managers, operations teams, and builders. Each template is a self-contained Python script that runs end-to-end using the Anthropic Claude API with tool use.

## Templates

### weekly-report-agent

Demonstrates multi-tool orchestration: the agent autonomously fetches Jira tickets, loads a metrics CSV, synthesizes both sources into a narrative, and formats the result as a Slack message â without explicit step-by-step instructions in the user prompt.

## Prerequisites

- Python 3.10 or later
- An Anthropic API key set as `ANTHROPIC_API_KEY` in your environment

## Install

```bash
pip install -r requirements.txt
```

Or create a virtual environment first:

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run any template

```bash
export ANTHROPIC_API_KEY=your_key_here
cd templates/weekly-report-agent
python agent.py
```

Each template's README documents its specific options and input formats.

## Structure

```
ai-agent-templates/
  requirements.txt
  .gitignore
  README.md
  templates/
    weekly-report-agent/
      agent.py
      tools.py
      examples/metrics_sample.csv
      README.md
```

## How the agent loop works

Every template follows the same pattern:

1. Send the user message and tool definitions to the Claude API.
2. If the response contains `tool_use` blocks, execute each tool call and collect the results.
3. Append the assistant response and the tool results to the message history.
4. Repeat until the model returns `stop_reason: end_turn`.

This loop is implemented directly in `agent.py` using the `anthropic` Python SDK. There is no framework or abstraction layer â the code is straightforward to read, modify, and extend.

## Design principles

This repo is meant to be read, not just run. The patterns below are deliberate, drawn from Anthropic's and AWS's published guidance on building agents, and each is fixable/verifiable in the code itself rather than asserted here:

- **Bounded iteration.** Every agent loop has a hard `max_iterations` cap and reports explicitly if it's hit without a normal end turn, instead of running unbounded or silently returning a partial result. ([Anthropic: building effective agents](https://www.anthropic.com/engineering/building-effective-agents) recommends stopping conditions to keep agents under control.)
- **Actionable tool errors, not crashes.** Tool dispatch catches bad arguments and runtime failures and returns them to the model as structured `{"error": "..."}` tool results, so the agent can see what went wrong and retry — rather than the whole process dying on an uncaught exception. ([Anthropic: writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) — "prompt-engineer your error responses to clearly communicate specific and actionable improvements, rather than opaque error codes or tracebacks.")
- **Explicit scope.** Each template's README states what it does and, just as importantly, what it deliberately does not do — following [AWS's guidance](https://aws.amazon.com/blogs/machine-learning/best-practices-for-building-robust-generative-ai-applications-with-amazon-bedrock-agents-part-1/) to define an agent's primary functions and out-of-scope tasks before building it.
- **No silent side effects.** Templates that produce an externally-visible artifact (a Slack message, an email) stop at generating the text. Actually sending it is left as a deliberate, separate step, so nothing gets posted or delivered without a human choosing to do so.
- **Clear tool definitions.** Tool `input_schema`s include a description for every parameter, and tool descriptions state exactly when and how to use each one — Anthropic's "agent-computer interface" (ACI) guidance found that tool description quality has an outsized effect on error rates.

## Adapting templates to production

`tools.py` contains mock implementations. To connect to real systems:

- Replace `fetch_jira_tickets` with your actual Jira client (the `jira` Python library or the Jira REST API).
- Replace `load_metrics_csv` with your production database connection.

The agent logic in `agent.py` does not need to change when you swap in real tool implementations.


## Related Projects

- [pm-agents](https://github.com/swethasalunke-tech/pm-agents) - six Claude agents for PM workflows (PRD writing, roadmap prioritization, meeting notes, user research synthesis, sprint retro, competitive intel)
