# Weekly Report Agent

An agent that autonomously generates a weekly product report by fetching Jira tickets, loading a metrics CSV, synthesizing both into a narrative, and formatting the result for Slack.

This template demonstrates multi-tool orchestration: the agent decides when to call each tool, in what order, and how to combine the results into a coherent output — without explicit step-by-step instructions in the user prompt.

## What it does

Given a project key and a metrics CSV, the agent:

1. Calls `fetch_jira_tickets` to retrieve all tickets updated in the last seven days.
2. Calls `load_metrics_csv` to load the week's product and business metrics.
3. Analyzes both sources to identify the most significant movements, completed work, risks, and upcoming priorities.
4. Calls `format_for_slack` to produce a structured, mrkdwn-formatted Slack message ready to post.

The agent is instructed to be specific: every bullet must contain a real data point or a concrete work item, not generic filler language.

## Prerequisites

- Python 3.10 or later
- An Anthropic API key

## Setup

```bash
cd templates/weekly-report-agent
pip install -r ../../requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

## Run

Generate a report for the PROD project using the sample metrics:

```bash
python agent.py
```

Use a different project or metrics file:

```bash
python agent.py --project INFRA --metrics examples/metrics_sample.csv
python agent.py --project DATA --week-ending 2025-04-25
```

Available mock project keys: `PROD`, `INFRA`, `DATA`

## Sample output

```
Generating weekly report for PROD | week ending 2025-04-25

  Tool: fetch_jira_tickets
  Tickets retrieved: 7
  Tool: load_metrics_csv
  Metrics rows loaded: 15
  Tool: format_for_slack
  Slack message formatted: 1,204 characters

Slack Message (ready to post)
*Weekly Report: PROD* | Week ending 2025-04-25

_Bulk-assign shipped to GA and MRR grew 1.9% week-over-week, while a search latency spike drove a P3 incident that is now in review._

*Metrics*
• Active users: 4,821 (+3.2% WoW)
• New signups: 312 (+8.1% WoW) — strongest week in eight weeks
• MRR: $187,400 (+1.9%); expansion MRR $8,200 (+22.4%)
• Support tickets opened fell 18.5% to 88, likely helped by the locale bug fix
• NPS: 52 (+3 points)

*Shipped this week*
• PROD-1821: Bulk-assign GA with permissions guard
• PROD-1834: Date picker locale regression fix
• PROD-1815: Time-tracking feature removed from nav
• PROD-1856: P2 export service post-mortem completed

*Risks and blockers*
:warning: Search latency fix (PROD-1850) in review — monitor p99 next week
:warning: Auth-service scaling work (INFRA-310) still in progress ahead of anticipated load

*Next week*
• Land PROD-1850 (search caching) to address latency risk
• Move PROD-1840 (AI summaries feedback UI) from review to done
• Complete PROD-1842 (export retry UI) to reduce repeat support tickets
```

## Adapting to real data sources

To connect to live systems, replace the mock functions in `tools.py`:

- `fetch_jira_tickets`: use the `jira` Python library or the Jira REST API
- `load_metrics_csv`: replace with a database query, BigQuery call, or an analytics API

The agent logic in `agent.py` does not need to change.

## Files

```
weekly-report-agent/
  agent.py                      main agent loop with multi-tool orchestration
  tools.py                      fetch_jira_tickets, load_metrics_csv, format_for_slack
  examples/
    metrics_sample.csv          15 rows of sample product metrics for week of 2025-04-25
  README.md
```
