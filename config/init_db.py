#!/usr/bin/env python3
"""Initialize the wealth-guide SQLite database."""

import sqlite3
import sys


def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            age INTEGER,
            annual_income REAL,
            monthly_expense REAL,
            savings TEXT,
            investment_assets TEXT,
            debt_credit_card TEXT DEFAULT 'None',
            debt_personal_student TEXT DEFAULT 'None',
            debt_mortgage TEXT DEFAULT 'None',
            risk_tolerance TEXT,
            experience TEXT,
            goal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER,
            user_level TEXT,
            selected_strategy TEXT,
            matched_strategies TEXT,
            selected_workflows TEXT,
            roadmap_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES profiles(id)
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <db_path>")
        sys.exit(1)
    init_db(sys.argv[1])
