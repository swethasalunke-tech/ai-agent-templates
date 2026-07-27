# Feedback Triage Agent

An agent that reads a batch of raw customer feedback, classifies each item, submits a Jira ticket, and drafts a customer-facing response — all in one agentic loop.

This template demonstrates a three-step-per-item pipeline where the agent has to keep track of many parallel items and apply consistent classification rules across all of them.

## What it does

For each feedback item in the batch, the agent:

1. Calls `classify_feedback` with category (bug/feature_request/question/praise), severity (critical/high/medium/low), owner team, and a one-sentence summary.
2. Calls `submit_to_jira` to create a ticket using that classification (category maps to issue type, severity maps to priority).
3. Calls `draft_response` to write a short, professional customer-facing reply in a tone appropriate to the category.

`submit_to_jira` is a mock — it returns a fake ticket key and URL so the template runs with no external Jira account required.

## Prerequisites

- Python 3.10 or later
- An Anthropic API key

## Setup

```bash
cd templates/feedback-triage-agent
pip install -r ../../requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

## Run

```bash
python agent.py --input examples/feedback_batch.json
```

Use a different model:

```bash
python agent.py --input examples/feedback_batch.json --model claude-sonnet-4-5
```

## Input format

The input file must be a JSON array of objects, each with `id`, `text`, `submitted_at` (ISO 8601, used for context only), and `source` (in-app, email, support_chat, app_store, etc.). See `examples/feedback_batch.json` for ten sample items.

## Sample output

Triaging the 10 items in `examples/feedback_batch.json`:

| ID | Category | Severity | Team | Jira Ticket | Summary |
|---|---|---|---|---|---|
| FB-001 | Bug | High | Engineering | PROD-9216 | App crashes during PDF export, causing users to lose work. |
| FB-002 | Feature Request | Medium | Product | PROD-9217 | Bulk-assign feature for team settings to speed up onboarding. |
| FB-003 | Question | Low | Support | PROD-9218 | Can't find Google Calendar integration settings in the new UI. |
| FB-004 | Praise | Low | Product | PROD-9219 | Positive review praising keyboard shortcuts and overall quality. |
| FB-005 | Bug | Medium | Engineering | PROD-9220 | Search takes 8–10 seconds on workspaces with 500+ tasks. |
| FB-006 | Feature Request | Medium | Design | PROD-9221 | Dark mode request for nighttime use. |
| FB-007 | Bug | **Critical** | Engineering | PROD-9222 | 503 errors blocking the entire team from logging in (active outage). |
| FB-008 | Bug | Medium | Engineering | PROD-9223 | Date picker ignores the configured UK locale. |
| FB-009 | Feature Request | Medium | Engineering | (created) | Webhook endpoint request to push status changes to Slack. |
| FB-010 | Praise | Low | Product | (created) | Onboarding flow praised as fast and well-guided. |

Completed in 3 iterations: one turn classified all 10 items, one turn submitted all 10 Jira tickets and drafted all 10 responses, and the final turn produced the summary table above. Note that `submit_to_jira`'s ticket numbers come from a hash of the feedback ID, so they'll differ between runs.

## Adapting to real data sources

Replace `submit_to_jira` in `tools.py` with a real call to the Jira REST API (or your ticketing system of choice), and pipe `--input` from a live feedback source (Zendesk, Intercom, app store review exports, etc.) instead of a static JSON file. The agent logic in `agent.py` does not need to change.

## Files

```
feedback-triage-agent/
  agent.py                      main agent loop, per-item classify/ticket/respond
  tools.py                      classify_feedback, submit_to_jira (mock), draft_response
  examples/
    feedback_batch.json         10 sample feedback items across bug/feature/question/praise
  README.md
```
