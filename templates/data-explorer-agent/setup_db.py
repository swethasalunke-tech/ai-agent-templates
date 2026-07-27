"""
Creates the sample SQLite database used by the data explorer agent.

Run this once before running agent.py:
    python setup_db.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sample.db"


def create_database() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS events;
        DROP TABLE IF EXISTS revenue;
        DROP TABLE IF EXISTS features;

        CREATE TABLE users (
            user_id     INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            email       TEXT NOT NULL,
            plan        TEXT NOT NULL,  -- free, starter, pro, enterprise
            country     TEXT NOT NULL,
            signed_up   TEXT NOT NULL,  -- ISO date string
            is_active   INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE events (
            event_id    INTEGER PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            event_name  TEXT NOT NULL,
            occurred_at TEXT NOT NULL,  -- ISO datetime string
            properties  TEXT            -- JSON blob
        );

        CREATE TABLE revenue (
            record_id   INTEGER PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            amount_usd  REAL NOT NULL,
            plan        TEXT NOT NULL,
            period_start TEXT NOT NULL,
            period_end   TEXT NOT NULL
        );

        CREATE TABLE features (
            feature_id   INTEGER PRIMARY KEY,
            name         TEXT NOT NULL,
            launched_at  TEXT NOT NULL,
            status       TEXT NOT NULL,  -- alpha, beta, ga, deprecated
            owner_team   TEXT NOT NULL
        );
    """)

    # Users
    users = [
        (1, "Alice Chen",      "alice@example.com",   pro",        "US",  "2023-01-15", 1),
        (2, "Bob Martins",     "bob@example.com",     "starter",    "BR",  "2023-03-22", 1),
        (3, "Cate Liu",        "cate@example.com",    "enterprise", "SG",  "2022-11-01", 1),
        (4, "David Park",      "david@example.com",   "free",       "KR",  "2024-01-10", 1),
        (5, "Eva Rossi",       "eva@example.com",     "pro",        "IT",  "2023-06-05", 0),
        (6, "Frank Müller",    "frank@example.com",   "enterprise", "DE",  "2022-08-14", 1),
        (7, "Grace Okonkwo",   "grace@example.com",   "starter",    "NG",  "2023-09-30", 1),
        (8, "Hiro Tanaka",     "hiro@example.com",    "pro",        "JP",  "2023-12-01", 1),
        (9, "Iris Dupont",     "iris@example.com",    "free",       "FR",  "2024-02-20", 1),
        (10,"Jake Thompson",   "jake@example.com",    "enterprise", "US",  "2022-05-19", 1),
        (11,"Kim Nakamura",    "kim@example.com",     "pro",        "US",  "2023-07-11", 1),
        (12,"Lena Kovač",      "lena@example.com",    "starter",    "HR",  "2024-03-05", 1),
        (13,"Marco Silva",     "marco@example.com",   "free",       "PT",  "2024-04-01", 0),
        (14,"Nina Patel",      "nina@example.com",    "pro",        "IN",  "2023-02-28", 1),
        (15,"Omar Hassan",     "omar@example.com",    "enterprise", "EG",  "2022-12-10", 1),
    ]
    cur.executemany(
        "INSERT INTO users VALUES (?,?,?,?,?,?,?)", users
    )

    # Events
    events = [
        (1,  1,  "page_view",       "2024-04-01T08:00:00", '{"page":"/dashboard"}'),
        (2,  1,  "export_pdf",      "2024-04-01T08:05:00", '{"file":"report_q1"}'),
        (3,  2,  "page_view",       "2024-04-01T09:00:00", '{"page":"/projects"}'),
        (4,  3,  "api_call",        "2024-04-01T09:15:00", '{"endpoint":"/v2/tasks"}'),
        (5,  3,  "api_call",        "2024-04-01T09:16:00", '{"endpoint":"/v2/tasks"}'),
        (6,  4,  "signup",          "2024-04-01T10:00:00", '{"referrer":"google"}'),
        (7,  5,  "page_view",       "2024-04-02T11:00:00", '{"page":"/settings"}'),
        (8,  6,  "feature_used",    "2024-04-02T11:30:00", '{"feature":"bulk_assign"}'),
        (9,  7,  "page_view",       "2024-04-02T12:00:00", '{"page":"/dashboard"}'),
        (10, 8,  "export_pdf",      "2024-04-02T13:00:00", '{"file":"sprint_16"}'),
        (11, 9,  "signup",          "2024-04-03T08:00:00", '{"referrer":"linkedin"}'),
        (12, 10, "api_call",        "2024-04-03T09:00:00", '{"endpoint":"/v2/webhooks"}'),
        (13, 11, "feature_used",    "2024-04-03T10:00:00", '{"feature":"dark_mode"}'),
        (14, 12, "page_view",       "2024-04-03T11:00:00", '{"page":"/billing"}'),
        (15, 1,  "upgrade_plan",    "2024-04-04T09:00:00", '{"from":"starter","to":"pro"}'),
        (16, 14, "feature_used",    "2024-04-04T10:30:00", '{"feature":"bulk_assign"}'),
        (17, 15, "api_call",        "2024-04-04T11:00:00", '{"endpoint":"/v2/reports"}'),
        (18, 2,  "upgrade_plan",    "2024-04-05T08:45:00", '{"from":"free","to":"starter"}'),
        (19, 3,  "feature_used",    "2024-04-05T09:30:00", '{"feature":"dark_mode"}'),
        (20, 6,  "export_pdf",      "2024-04-05T14:00:00", '{"file":"annual_review"}'),
    ]
    cur.executemany(
        "INSERT INTO events VALUES (?,?,?,?,?)", events
    )

    # Revenue
    revenue = [
        (1,  1,  29.00, "pro",        "2024-01-01", "2024-01-31"),
        (2,  1,  29.00, "pro",        "2024-02-01", "2024-02-29"),
        (3,  1,  29.00, "pro",        "2024-03-01", "2024-03-31"),
        (4,  3,  299.00,"enterprise", "2024-01-01", "2024-01-31"),
        (5,  3,  299.00,"enterprise", "2024-02-01", "2024-02-29"),
        (6,  3,  299.00,"enterprise", "2024-03-01", "2024-03-31"),
        (7,  5,  29.00, "pro",        "2024-01-01", "2024-01-31"),
        (8,  6,  299.00,"enterprise", "2024-01-01", "2024-01-31"),
        (9,  6,  299.00,"enterprise", "2024-02-01", "2024-02-29"),
        (10, 6,  299.00,"enterprise", "2024-03-01", "2024-03-31"),
        (11, 8,  29.00, "pro",        "2024-02-01", "2024-02-29"),
        (12, 8,  29.00, "pro",        "2024-03-01", "2024-03-31"),
        (13, 10, 299.00,"enterprise", "2024-01-01", "2024-01-31"),
        (14, 10, 299.00,"enterprise", "2024-02-01", "2024-02-29"),
        (15, 10, 299.00,"enterprise", "2024-03-01", "2024-03-31"),
        (16, 11, 29.00, "pro",        "2024-01-01", "2024-01-31"),
        (17, 11, 29.00, "pro",        "2024-02-01", "2024-02-29"),
        (18, 14, 29.00, "pro",        "2024-01-01", "2024-01-31"),
        (19, 15, 299.00,"enterprise", "2024-01-01", "2024-01-31"),
        (20, 2,  9.00,  "starter",    "2024-03-01", "2024-03-31"),
    ]
    cur.executemany(
        "INSERT INTO revenue VALUES (?,?,?,?,?,?)", revenue
    )

    # Features
    features = [
        (1, "bulk_assign",       "2023-06-01", "ga",         "product"),
        (2, "dark_mode",         "2023-10-15", "ga",         "design"),
        (3, "api_v2",            "2022-12-01", "ga",         "engineering"),
        (4, "ai_summaries",      "2024-01-20", "beta",       "product"),
        (5, "offline_mode",      "2024-03-10", "alpha",      "engineering"),
        (6, "pdf_export",        "2022-09-01", "ga",         "engineering"),
        (7, "webhooks",          "2023-08-20", "ga",         "engineering"),
        (8, "custom_themes",     "2023-12-05", "beta",       "design"),
        (9, "time_tracking",     "2021-05-01", "deprecated", "product"),
        (10,"sso_saml",          "2023-03-15", "ga",         "engineering"),
    ]
    cur.executemany(
        "INSERT INTO features VALUES (?,?,?,?,?)", features
    )

    conn.commit()
    conn.close()
    print(f"Database created at: {DB_PATH}")
    print("Tables: users, events, revenue, features")


if __name__ == "__main__":
    create_database()
