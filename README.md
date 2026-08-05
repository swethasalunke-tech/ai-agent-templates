# ai-agent-templates

A collection of practical, working agent patterns for product managers, operations teams, and builders. Each template is a self-contained Python script that runs end-to-end using the Anthropic Claude API with tool use.

The focus is on problems that arise in real product and operations work: triaging feedback, exploring data, responding to incidents, and writing weekly reports. Every template uses mock tool responses where external services would be needed, so you can run them immediately and swap in real integrations when you are ready.

## Templates

### doc-qa-agent

Answers natural language questions about a folder of documents by retrieving the most relevant passages and grounding its answer strictly in that content. Uses plain keyword-overlap scoring for retrieval, so it runs with zero extra infrastructure — no embeddings or vector database required.

### task-router-agent

Reads a list of tasks and routes each one to the team best positioned to handle it (engineering, design, product, or support), flags ambiguous ones for human review, and writes a short routing report. A good starting point for any triage-and-assign workflow.

### feedback-triage-agent

Reads a batch of customer feedback items and classifies each one by type (bug, feature request, question, praise), assigns severity, identifies the responsible team, submits a mock Jira ticket, and drafts a customer-facing response. Good starting point for any batch classification workflow.

### data-explorer-agent

Accepts natural language questions about a product metrics database and translates them to SQL queries against a local SQLite database. Iterates if results are empty or need clarification. Ships with a sample database of users, events, revenue, and feature data.

### incident-triage-agent

Reads incident descriptions, classifies severity (P1-P4), identifies likely affected systems from a configurable list, retrieves the relevant runbook, and drafts a customer-facing status page update. Accepts both batch files and single descriptions from the command line.

### weekly-report-agent

Demonstrates multi-tool orchestration: the agent autonomously fetches Jira tickets, loads a metrics CSV, synthesizes both sources into a narrative, and formats the result as a Slack message — without explicit step-by-step instructions in the user prompt.

## Prerequisites

- Python 3.10 or later
- An Anthropic API key set as `ANTHROPIC_API_KEY` in your environment

## Install

All templates share the same dependencies. Install once from the repo root:

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
cd templates/<template-name>
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
    doc-qa-agent/
      agent.py
      tools.py
      examples/docs/billing-faq.txt
      examples/docs/terms-of-service.txt
      README.md
    task-router-agent/
      agent.py
      tools.py
      examples/tasks.json
      README.md
    feedback-triage-agent/
      agent.py
      tools.py
      examples/feedback_batch.json
      README.md
    data-explorer-agent/
      agent.py
      tools.py
      setup_db.py
      README.md
    incident-triage-agent/
      agent.py
      tools.py
      examples/incidents.json
      README.md
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

This loop is implemented directly in each `agent.py` using the `anthropic` Python SDK. There is no framework or abstraction layer — the code is straightforward to read, modify, and extend.

## Adapting templates to production

Each `tools.py` file contains mock implementations. To connect to real systems:

- Replace `submit_to_jira` with calls to the Jira REST API or the `jira` Python library.
- Replace `run_sql_query` with your production database connection.
- Replace `fetch_jira_tickets` with your actual Jira client.
- Replace `post_status_update` with your status page API (Statuspage, Atlassian, etc.).

The agent logic in each `agent.py` does not need to change when you swap in real tool implementations.
