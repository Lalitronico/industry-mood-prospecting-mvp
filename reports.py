"""Simple commercial reporting for the approval queue."""

import sqlite3
from collections import defaultdict

COMMERCIAL_STATUSES = {
    "sent",
    "replied",
    "positive_reply",
    "demo_booked",
    "not_interested",
    "bounced",
}


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _empty_bucket() -> dict:
    return {
        "total_drafts": 0,
        "sent_or_later": 0,
        "replied": 0,
        "positive_reply": 0,
        "demo_booked": 0,
        "not_interested": 0,
        "bounced": 0,
    }


def _add_row(bucket: dict, row: dict) -> None:
    status = row["status"]
    bucket["total_drafts"] += 1
    if status in COMMERCIAL_STATUSES:
        bucket["sent_or_later"] += 1
    if status in bucket:
        bucket[status] += 1


def campaign_summary(db_path: str, campaign_name: str | None = None) -> dict:
    """Return funnel counts overall and by role bucket."""
    conn = _connect(db_path)
    try:
        if campaign_name:
            rows = conn.execute(
                "SELECT * FROM drafts WHERE campaign_name = ? ORDER BY id",
                (campaign_name,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM drafts ORDER BY id").fetchall()
    finally:
        conn.close()

    summary = _empty_bucket()
    by_role = defaultdict(_empty_bucket)

    for sqlite_row in rows:
        row = dict(sqlite_row)
        _add_row(summary, row)
        _add_row(by_role[row.get("role_bucket") or "UNKNOWN"], row)

    summary["by_role"] = dict(by_role)
    return summary
