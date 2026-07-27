# Task Router Agent

An agent that reads a list of tasks and routes each one to the team best positioned to handle it — engineering, design, product, or support — then writes a short routing report.

This template demonstrates batch decision-making: the agent works through an arbitrary number of items in one pass, flags the ones it isn't confident about instead of forcing a guess, and produces a single summary at the end.

## What it does

Given a list of tasks (title + description), the agent:

1. Reads each task and calls `route_task` with the owning team, a confidence level (high/medium/low), and a one-sentence rationale.
2. Calls `flag_for_review` for any task where confidence is low or the task clearly spans multiple teams.
3. Once every task is routed, calls `write_routing_report` exactly once with a short prose summary of how work was distributed.

## Prerequisites

- Python 3.10 or later
- An Anthropic API key

## Setup

```bash
cd templates/task-router-agent
pip install -r ../../requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

## Run

```bash
python agent.py --tasks examples/tasks.json
```

Or pipe tasks in from stdin, or use a different model:

```bash
cat examples/tasks.json | python agent.py
python agent.py --tasks examples/tasks.json --model claude-haiku-4-5
```

## Sample output

Routing the 8 tasks in `examples/tasks.json`:

| Task | Team | Confidence | Rationale |
|---|---|---|---|
| TASK-001 (bulk export 500s) | engineering | high | Backend API bug involving timeouts and 500 errors on a specific endpoint. |
| TASK-002 (admin pagination) | engineering | high | Cursor-based pagination is a backend/frontend engineering task. |
| TASK-003 (migration FK bug) | engineering | high | Database migration ordering is purely an engineering concern. |
| TASK-004 (empty state redesign) | design | high | Illustrated empty state with UX guidance is a design task. |
| TASK-005 (password reset bug) | support | high | Specific customer account issue requiring support investigation. |
| TASK-006 (add-on pricing) | product | medium | Pricing/packaging is a product call, but needs engineering input on metering. |
| TASK-007 (icon set refresh) | design | medium | Design-led, but implementation needs engineering collaboration. |
| TASK-008 (slow dashboard) | engineering | high | Performance profiling to diagnose slow load times. |

Flagged for review:

- **TASK-006** — requires cross-team coordination between product (pricing) and engineering (metering feasibility).
- **TASK-007** — design owns the brand direction, but engineering needs to implement the replacements.

Final report: *"Of the 8 tasks routed, engineering received the largest share with 4 tasks covering API bugs, pagination implementation, migration fixes, and performance investigation. Design was assigned 2 tasks focused on empty state redesign and icon library updates. Product received 1 task for pricing strategy, and support was assigned 1 customer-specific password reset issue. Two tasks (TASK-006 and TASK-007) were flagged for human review due to requiring cross-team coordination."*

Completed in 3 iterations — one turn to route all 8 tasks, one to flag the 2 ambiguous ones, one to write the final report.

## Adapting to real data sources

Point `--tasks` at a live export from your issue tracker (Jira, Linear, GitHub Issues) instead of a static JSON file, and swap `write_routing_report`'s output for a webhook that actually creates the routing labels or assignments. The agent logic in `agent.py` does not need to change.

## Files

```
task-router-agent/
  agent.py                      main agent loop, batch task routing
  tools.py                      route_task, flag_for_review, write_routing_report
  examples/
    tasks.json                  8 sample engineering/design/product/support tasks
  README.md
```
