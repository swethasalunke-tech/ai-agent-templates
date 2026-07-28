"""
Tool definitions and mock implementations for the incident triage agent.
"""

import json
from typing import Any

# Configurable list of systems the agent knows about
KNOWN_SYSTEMS = [
    "authentication-service",
    "api-gateway",
    "database-primary",
    "database-replica",
    "search-service",
    "export-service",
    "billing-service",
    "webhook-service",
    "notification-service",
    "cdn",
    "storage-service",
    "cron-scheduler",
]

# Mock runbook data keyed by system name
RUNBOOKS: dict[str, dict[str, str]] = {
    "authentication-service": {
        "title": "Authentication Service Outage",
        "steps": (
            "1. Check auth-service pods in Kubernetes: kubectl get pods -n auth\n"
            "2. Tail logs: kubectl logs -n auth -l app=auth-service --tail=100\n"
            "3. Verify downstream dependency: identity-provider health endpoint\n"
            "4. Check recent deployments in the auth namespace\n"
            "5. If pod OOMKilled, scale horizontally and page infra team\n"
            "6. Rollback procedure: helm rollback auth-service --namespace auth"
        ),
        "escalation": "Page @auth-oncall and @platform-lead",
    },
    "export-service": {
        "title": "Export Service Failure",
        "steps": (
            "1. Check export-worker queue depth in Redis\n"
            "2. Verify S3 bucket write permissions (export-artifacts bucket)\n"
            "3. Look for timeout errors in export-service logs\n"
            "4. Confirm PDF renderer container is running and healthy\n"
            "5. Check storage quota for the affected tenant\n"
            "6. Manually requeue failed export jobs via admin panel"
        ),
        "escalation": "Page @export-oncall; loop in @storage-team if S3 errors",
    },
    "search-service": {
        "title": "Search Latency Spike",
        "steps": (
            "1. Check Elasticsearch cluster health: GET /_cluster/health\n"
            "2. Identify slow queries via slow log: GET /_nodes/stats/indices/search\n"
            "3. Check database CPU and active connections\n"
            "4. Look for index fragmentation — consider force-merge if segments > 100\n"
            "5. Check if a heavy batch indexing job is running concurrently\n"
            "6. Scale read replicas if sustained load"
        ),
        "escalation": "Page @search-oncall; escalate to @db-team if CPU stays above 90%",
    },
    "billing-service": {
        "title": "Billing Job Failure",
        "steps": (
            "1. Check cron-scheduler logs for the billing-aggregation job\n"
            "2. Verify environment variables match the new infrastructure endpoints\n"
            "3. Check billing-service database migrations are complete\n"
            "4. Re-run aggregation manually: billing-cli run-aggregation --date YYYY-MM-DD\n"
            "5. Verify idempotency — confirm no duplicate charges before rerunning\n"
            "6. Notify finance team with estimated resolution time"
        ),
        "escalation": "Page @billing-oncall and notify finance@company.com immediately",
    },
    "webhook-service": {
        "title": "Webhook Delivery Failure",
        "steps": (
            "1. Confirm API key rotation propagated to webhook-service config store\n"
            "2. Check webhook delivery logs for the affected customer ID\n"
            "3. Verify HMAC signing key cache was invalidated on key rotation\n"
            "4. Test delivery manually via webhook-cli send --customer-id=X\n"
            "5. Check for dead-letter queue buildup if retries are failing"
        ),
        "escalation": "Page @integrations-oncall",
    },
    "database-primary": {
        "title": "Database Primary Under Load",
        "steps": (
            "1. Check active queries: SELECT * FROM pg_stat_activity WHERE state='active'\n"
            "2. Identify blocking queries and kill if necessary\n"
            "3. Check for missing indexes on recently added columns\n"
            "4. Confirm connection pool is not exhausted\n"
            "5. Consider promoting a read replica for read traffic"
        ),
        "escalation": "Page @db-oncall",
    },
    "cron-scheduler": {
        "title": "Cron Scheduler Misconfiguration",
        "steps": (
            "1. List all registered jobs: cron-admin list-jobs\n"
            "2. Verify job environment variables against new infrastructure config\n"
            "3. Check for duplicate job registrations from migration\n"
            "4. Manually trigger the missed job and verify output\n"
            "5. Update cron config and redeploy scheduler service"
        ),
        "escalation": "Page @platform-oncall",
    },
}

TOOL_DEFINITIONS = [
    {
        "name": "classify_incident",
        "description": (
            "Classify an incident by severity (P1-P4), identify likely affected systems "
            "from the known system list, and provide a one-sentence impact summary."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "incident_id": {"type": "string"},
                "severity": {
                    "type": "string",
                    "enum": ["P1", "P2", "P3", "P4"],
                    "description": (
                        "P1: complete service outage or data loss risk affecting all users. "
                        "P2: major feature broken, significant subset of users affected. "
                        "P3: degraded performance or partial feature failure, workaround exists. "
                        "P4: minor issue, single customer or cosmetic impact."
                    ),
                },
                "affected_systems": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": f"Systems from this list likely involved: {KNOWN_SYSTEMS}",
                },
                "impact_summary": {
                    "type": "string",
                    "description": "One sentence describing business impact.",
                },
            },
            "required": ["incident_id", "severity", "affected_systems", "impact_summary"],
        },
    },
    {
        "name": "lookup_runbook",
        "description": "Retrieve the runbook for a specific system.",
        "input_schema": {
            "type": "object",
            "properties": {
                "system_name": {
                    "type": "string",
                    "description": f"One of: {list(RUNBOOKS.keys())}",
                },
            },
            "required": ["system_name"],
        },
    },
    {
        "name": "post_status_update",
        "description": (
            "Post a customer-facing status page update for an incident. "
            "Returns a mock confirmation with a status page URL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "incident_id": {"type": "string"},
                "severity": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["investigating", "identified", "monitoring", "resolved"],
                },
                "headline": {
                    "type": "string",
                    "description": "Short title for the status page (under 80 characters).",
                },
                "body": {
                    "type": "string",
                    "description": (
                        "Three to five sentence customer-facing update. "
                        "Plain language, no internal jargon. "
                        "State what is affected, what is being done, and when the next update is."
                    ),
                },
            },
            "required": ["incident_id", "severity", "status", "headline", "body"],
        },
    },
]


def classify_incident(
    incident_id: str,
    severity: str,
    affected_systems: list[str],
    impact_summary: str,
) -> dict[str, Any]:
    return {
        "status": "classified",
        "incident_id": incident_id,
        "severity": severity,
        "affected_systems": affected_systems,
        "impact_summary": impact_summary,
    }


def lookup_runbook(system_name: str) -> dict[str, Any]:
    runbook = RUNBOOKS.get(system_name)
    if runbook is None:
        # Return a generic runbook if the specific system is not found
        return {
            "system": system_name,
            "title": f"Generic Runbook for {system_name}",
            "steps": (
                "1. Check service health endpoint\n"
                "2. Review recent deployments and configuration changes\n"
                "3. Check application logs for errors\n"
                "4. Verify downstream dependencies are healthy\n"
                "5. Page the relevant on-call engineer"
            ),
            "escalation": "Page @platform-oncall",
        }
    return {"system": system_name, **runbook}


def post_status_update(
    incident_id: str,
    severity: str,
    status: str,
    headline: str,
    body: str,
) -> dict[str, Any]:
    update_id = abs(hash(incident_id + status)) % 90000 + 10000
    return {
        "status": "posted",
        "incident_id": incident_id,
        "update_id": f"UPD-{update_id}",
        "severity": severity,
        "current_status": status,
        "headline": headline,
        "url": f"https://status.yourproduct.com/incidents/{incident_id.lower()}",
        "body_preview": body[:120] + ("..." if len(body) > 120 else ""),
    }


def dispatch_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name == "classify_incident":
        result = classify_incident(**tool_input)
    elif tool_name == "lookup_runbook":
        result = lookup_runbook(**tool_input)
    elif tool_name == "post_status_update":
        result = post_status_update(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result, indent=2)
