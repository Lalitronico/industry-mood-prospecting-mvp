"""Minimal SQLite-based approval queue for outreach drafts — stdlib only.

Statuses: pending_review → approved | rejected.
"""

import sqlite3
from datetime import datetime, timezone

VALID_STATUSES = {"pending_review", "approved", "rejected"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS drafts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject     TEXT    NOT NULL,
    body_text   TEXT    NOT NULL,
    template_key TEXT   NOT NULL,
    role_bucket TEXT    NOT NULL,
    company     TEXT    NOT NULL,
    email       TEXT    NOT NULL,
    contact_name TEXT   NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'pending_review',
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_queue(db_path: str) -> None:
    """Create the drafts table if it doesn't exist."""
    conn = _connect(db_path)
    conn.executescript(_SCHEMA)
    conn.close()


def enqueue_draft(db_path: str, draft: dict) -> int:
    """Insert a draft into the queue with status=pending_review. Returns the new id."""
    now = _now()
    conn = _connect(db_path)
    cursor = conn.execute(
        """INSERT INTO drafts
           (subject, body_text, template_key, role_bucket, company, email,
            contact_name, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_review', ?, ?)""",
        (
            draft["subject"],
            draft["body_text"],
            draft["template_key"],
            draft["role_bucket"],
            draft["company"],
            draft["email"],
            draft["contact_name"],
            now,
            now,
        ),
    )
    conn.commit()
    draft_id = cursor.lastrowid
    conn.close()
    return draft_id


def list_pending(db_path: str) -> list[dict]:
    """Return all drafts with status=pending_review."""
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM drafts WHERE status = 'pending_review' ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_draft(db_path: str, draft_id: int) -> dict | None:
    """Return a single draft by id, or None if not found."""
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_status(db_path: str, draft_id: int, new_status: str) -> None:
    """Update a draft's status. Raises ValueError for invalid status or missing id."""
    if new_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status '{new_status}'. Must be one of: {VALID_STATUSES}"
        )
    conn = _connect(db_path)
    cursor = conn.execute(
        "UPDATE drafts SET status = ?, updated_at = ? WHERE id = ?",
        (new_status, _now(), draft_id),
    )
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise ValueError(f"Draft id {draft_id} not found")
    conn.close()
