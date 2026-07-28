# Incident Triage Agent

An agent that reads incident descriptions, classifies each one by severity (P1-P4), identifies the likely affected systems, retrieves the relevant runbook steps, and drafts a customer-facing status page update.

This template demonstrates how to combine classification, knowledge lookup, and structured output generation in a single agent loop — a pattern applicable to any on-call or operations workflow.

## What it does

For each incident in the input:

1. Calls `classify_incident` — assigns P1/P2/P3/P4 severity based on scope and impact, identifies affected systems from a configurable list, and writes a one-sentence impact summary.
2. Calls `lookup_runbook` — retrieves the runbook for the primary affected system, including step-by-step diagnosis instructions and escalation contacts.
3. Calls `post_status_update` — drafts and posts a customer-facing status update with an appropriate headline and plain-language body.

After all incidents are processed, the agent prints a triage summary.

## Severity guidelines

The agent uses these criteria when classifying:

- P1: Complete outage or data loss risk affecting all users
- P2: Major feature broken, significant portion of users affected
- P3: Degraded performance with a workaround available
- P4: Single customer affected or minor cosmetic issue

## Prerequisites

- Python 3.10 or later
- An Anthropic API key

## Setup

```bash
cd templates/incident-triage-agent
pip install -r ../../requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

## Run

Process the sample incident batch:

```bash
python agent.py
```

Triage a single incident from the command line:

```bash
python agent.py --single "Search latency spiked to 8 seconds on the US-East cluster. Database CPU is at 94%."
```

Use a custom incidents file:

```bash
python agent.py --input path/to/incidents.json
```

## Input format

The input file must be a JSON array. Each object requires:

- `id` — unique incident identifier
- `description` — plain-text description of what is happening
- `reported_at` — ISO 8601 timestamp
- `reporter` — who reported it (on-call engineer, monitoring-alert, support, etc.)

See `examples/incidents.json` for five sample incidents ranging from a full authentication outage (P1) to a single-customer webhook issue (P4).

## Sample output

Triaging the 5 incidents in `examples/incidents.json`:

| ID | Severity | Primary System | Affected Systems | Impact |
|---|---|---|---|---|
| INC-001 | 🔴 P1 | authentication-service | authentication-service, api-gateway | Complete auth outage — all users, all regions, unable to log in. |
| INC-002 | 🟠 P2 | export-service | export-service, storage-service | PDF exports failing for ~15% of EU enterprise accounts. |
| INC-003 | 🟠 P2 | search-service | search-service, database-primary | Search latency up 40x in US-East; database CPU at 94%. |
| INC-004 | ⚪ P4 | webhook-service | webhook-service, authentication-service | Single customer's webhook stopped after an API key rotation. |
| INC-005 | 🟠 P2 | billing-service | billing-service, cron-scheduler, database-primary | Nightly billing job failed; no charges processed this cycle. |

Example status page update (INC-001, status: investigating):

> **Login Services Unavailable - All Regions**
>
> We are currently experiencing an issue that is preventing users from logging into the platform. All regions are affected. Our engineering team has been mobilized and is actively investigating the root cause. We understand the urgency of this issue and are working to restore service as quickly as possible. We will provide an update within 15 minutes.

Completed in 4 iterations: one turn classified all 5 incidents, one turn looked up the runbook for each incident's primary system, one turn posted all 5 status updates, and the final turn produced the triage summary table. Note that `post_status_update`'s update IDs are derived from a hash of the incident ID and status, so they'll differ between runs.

## Configuring known systems

Edit `KNOWN_SYSTEMS` and `RUNBOOKS` in `tools.py` to match your own infrastructure. The agent will only suggest systems from the `KNOWN_SYSTEMS` list and will look up runbooks by the exact system name keys in the `RUNBOOKS` dict.

## Files

```
incident-triage-agent/
  agent.py
  tools.py                    tool schemas, KNOWN_SYSTEMS list, mock runbook data
  examples/
    incidents.json            5 sample incidents across all severity levels
  README.md
```
