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

## Adapting templates to production

`tools.py` contains mock implementations. To connect to real systems:

- Replace `fetch_jira_tickets` with your actual Jira client (the `jira` Python library or the Jira REST API).
- Replace `load_metrics_csv` with your production database connection.

The agent logic in `agent.py` does not need to change when you swap in real tool implementations.


## Related Projects

- [pm-agents](https://github.com/swethasalunke-tech/pm-agents) - six Claude agents for PM workflows (PRD writing, roadmap prioritization, meeting notes, user research synthesis, sprint retro, competitive intel)
