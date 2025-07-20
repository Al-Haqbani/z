import os
import sqlite3
from contextlib import contextmanager
from typing import Iterable, Dict

DB_PATH = os.environ.get("EMPLOLEAKS_DB", os.path.join("reports", "scan_results.db"))

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                keyword TEXT,
                started TIMESTAMP,
                finished TIMESTAMP
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS leaks (
                scan_id TEXT,
                source TEXT,
                file TEXT,
                leak_type TEXT,
                value TEXT,
                severity TEXT,
                active INTEGER,
                FOREIGN KEY(scan_id) REFERENCES scans(id)
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS bounties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL,
                day TEXT,
                note TEXT
            )
            """
        )


def record_scan(scan_id: str, keyword: str, started: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO scans(id, keyword, started) VALUES(?,?,?)",
            (scan_id, keyword, started),
        )


def finish_scan(scan_id: str, finished: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE scans SET finished=? WHERE id=?",
            (finished, scan_id),
        )


def insert_leaks(scan_id: str, leaks: Iterable[Dict]):
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO leaks(scan_id, source, file, leak_type, value, severity, active) "
            "VALUES(?,?,?,?,?,?,?)",
            [
                (
                    scan_id,
                    leak.get("source"),
                    leak.get("file"),
                    leak.get("leak_type"),
                    leak.get("value"),
                    leak.get("severity"),
                    int(bool(leak.get("active"))) if leak.get("active") is not None else None,
                )
                for leak in leaks
            ],
        )


def add_bounty(amount: float, day: str, note: str | None = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO bounties(amount, day, note) VALUES(?,?,?)",
            (amount, day, note),
        )


def get_bounties():
    with get_conn() as conn:
        cur = conn.execute("SELECT id, amount, day, note FROM bounties ORDER BY day")
        return [dict(id=row[0], amount=row[1], day=row[2], note=row[3]) for row in cur.fetchall()]


def total_bounty():
    with get_conn() as conn:
        cur = conn.execute("SELECT SUM(amount) FROM bounties")
        row = cur.fetchone()
        return row[0] or 0
