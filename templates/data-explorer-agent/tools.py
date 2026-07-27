"""
Tool definitions and implementations for the data explorer agent.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent / "sample.db"

TOOL_DEFINITIONS = [
    {
        "name": "run_sql_query",
        "description": (
            "Execute a read-only SQL SELECT query against the local SQLite database "
            "and return the results as a list of row objects. "
            "The database has four tables: users, events, revenue, features. "
            "Always use SELECT; never use INSERT, UPDATE, DELETE, or DROP."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A valid SQLite SELECT statement.",
                },
                "explanation": {
                    "type": "string",
                    "description": "One sentence explaining what this query is intended to answer.",
                },
            },
            "required": ["query", "explanation"],
        },
    },
    {
        "name": "get_schema",
        "description": (
            "Return the schema (column names and types) for one or all tables in the database. "
            "Call this before writing queries if you are unsure of the column names."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of a specific table, or 'all' to see every table.",
                },
            },
            "required": ["table_name"],
        },
    },
]


def run_sql_query(query: str, explanation: str) -> dict[str, Any]:
    """Run a SELECT query and return rows as a list of dicts."""
    query_upper = query.strip().upper()
    for forbidden in ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "ATTACH"):
        if forbidden in query_upper:
            return {"error": f"Write operations are not permitted. Found keyword: {forbidden}"}

    if not DB_PATH.exists():
        return {
            "error": (
                "Database file not found. Run 'python setup_db.py' first to create it."
            )
        }

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query)
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return {
            "row_count": len(rows),
            "rows": rows[:100],  # cap output to 100 rows
            "explanation": explanation,
        }
    except sqlite3.Error as exc:
        return {"error": str(exc)}


def get_schema(table_name: str) -> dict[str, Any]:
    """Return column info for one or all tables."""
    if not DB_PATH.exists():
        return {"error": "Database file not found. Run 'python setup_db.py' first."}

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if table_name.lower() == "all":
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        table_names = [row[0] for row in cur.fetchall()]
    else:
        table_names = [table_name]

    schema: dict[str, Any] = {}
    for tname in table_names:
        cur.execute(f"PRAGMA table_info({tname})")
        columns = [
            {"name": row[1], "type": row[2], "not_null": bool(row[3]), "pk": bool(row[5])}
            for row in cur.fetchall()
        ]
        schema[tname] = columns

    conn.close()
    return {"schema": schema}


def dispatch_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name == "run_sql_query":
        result = run_sql_query(**tool_input)
    elif tool_name == "get_schema":
        result = get_schema(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result, indent=2)
