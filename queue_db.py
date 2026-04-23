"""Minimal SQLite-based approval queue for outreach drafts - stdlib only.

Statuses: pending_review -> approved | rejected | suppressed -> sent.
"""

import sqlite3
from datetime import datetime, timedelta, timezone

DEFAULT_CAMPAIGN = "first_wave_local"
DEFAULT_STEP_NUMBER = 1

FOLLOW_UP_DELAYS_DAYS = {2: 4, 3: 7}
TERMINAL_STATUSES = {"replied", "bounced", "suppressed"}
VALID_STATUSES = {
    "pending_review",
    "approved",
    "rejected",
    "sent",
    "suppressed",
    "replied",
    "bounced",
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS drafts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    subject       TEXT    NOT NULL,
    body_text     TEXT    NOT NULL,
    template_key  TEXT    NOT NULL,
    role_bucket   TEXT    NOT NULL,
    company       TEXT    NOT NULL,
    email         TEXT    NOT NULL,
    contact_name  TEXT    NOT NULL,
    campaign_name TEXT    NOT NULL DEFAULT 'first_wave_local',
    step_number   INTEGER NOT NULL DEFAULT 1,
    lead_key      TEXT,
    scheduled_at  TEXT,
    status        TEXT    NOT NULL DEFAULT 'pending_review',
    created_at    TEXT    NOT NULL,
    updated_at    TEXT    NOT NULL,
    sent_at       TEXT
);

CREATE TABLE IF NOT EXISTS suppressions (
    email       TEXT PRIMARY KEY COLLATE NOCASE,
    reason      TEXT NOT NULL,
    source      TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
"""

_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_drafts_campaign_step
ON drafts (campaign_name, step_number, status);

CREATE INDEX IF NOT EXISTS idx_drafts_email
ON drafts (email);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_datetime(value: str) -> datetime:
    cleaned = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _normalize_email(email: str | None) -> str:
    return (email or "").strip().lower()


def _campaign_name(draft: dict) -> str:
    return draft.get("campaign_name") or DEFAULT_CAMPAIGN


def _step_number(draft: dict) -> int:
    return int(draft.get("step_number") or DEFAULT_STEP_NUMBER)


def _lead_key(draft: dict) -> str:
    return draft.get("lead_key") or _normalize_email(draft.get("email"))


def _same_lead_clause_value(row: dict) -> str:
    return row.get("lead_key") or _normalize_email(row.get("email"))


def _migrate_drafts_table(conn: sqlite3.Connection) -> None:
    """Add queue columns when opening DBs created by older versions."""
    rows = conn.execute("PRAGMA table_info(drafts)").fetchall()
    existing = {row["name"] for row in rows}
    migrations = {
        "campaign_name": "ALTER TABLE drafts ADD COLUMN campaign_name TEXT NOT NULL DEFAULT 'first_wave_local'",
        "step_number": "ALTER TABLE drafts ADD COLUMN step_number INTEGER NOT NULL DEFAULT 1",
        "lead_key": "ALTER TABLE drafts ADD COLUMN lead_key TEXT",
        "scheduled_at": "ALTER TABLE drafts ADD COLUMN scheduled_at TEXT",
    }
    for column, statement in migrations.items():
        if column not in existing:
            conn.execute(statement)
    conn.execute(
        "UPDATE drafts SET lead_key = lower(email) WHERE lead_key IS NULL OR lead_key = ''"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_queue(db_path: str) -> None:
    """Create or migrate the queue database."""
    conn = _connect(db_path)
    try:
        conn.executescript(_SCHEMA)
        _migrate_drafts_table(conn)
        conn.executescript(_INDEXES)
        conn.commit()
    finally:
        conn.close()


def enqueue_draft(db_path: str, draft: dict) -> int:
    """Insert a draft into the queue with status=pending_review. Returns the new id."""
    now = _now()
    conn = _connect(db_path)
    cursor = conn.execute(
        """INSERT INTO drafts
           (subject, body_text, template_key, role_bucket, company, email,
            contact_name, campaign_name, step_number, lead_key, scheduled_at,
            status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_review', ?, ?)""",
        (
            draft["subject"],
            draft["body_text"],
            draft["template_key"],
            draft["role_bucket"],
            draft["company"],
            _normalize_email(draft["email"]),
            draft["contact_name"],
            _campaign_name(draft),
            _step_number(draft),
            _lead_key(draft),
            draft.get("scheduled_at"),
            now,
            now,
        ),
    )
    conn.commit()
    draft_id = cursor.lastrowid
    conn.close()
    return draft_id


def find_existing_draft(db_path: str, draft: dict) -> dict | None:
    """Return an existing draft for the same email/campaign/step, if any."""
    conn = _connect(db_path)
    row = conn.execute(
        """SELECT * FROM drafts
           WHERE lower(email) = lower(?)
             AND campaign_name = ?
             AND step_number = ?
           ORDER BY id
           LIMIT 1""",
        (_normalize_email(draft["email"]), _campaign_name(draft), _step_number(draft)),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def enqueue_draft_once(db_path: str, draft: dict) -> tuple[int, bool]:
    """Insert a draft unless it already exists.

    Returns (draft_id, created), where created=False means the existing draft id
    was reused. This keeps repeated CLI runs from duplicating the same sequence
    step for the same contact.
    """
    existing = find_existing_draft(db_path, draft)
    if existing:
        return existing["id"], False
    return enqueue_draft(db_path, draft), True


def suppress_email(
    db_path: str,
    email: str,
    reason: str = "manual",
    source: str = "cli",
) -> int:
    """Add an email to the suppression list and suppress unsent drafts.

    Returns the number of pending/approved drafts moved to status=suppressed.
    """
    normalized_email = _normalize_email(email)
    if not normalized_email:
        raise ValueError("email is required")

    now = _now()
    conn = _connect(db_path)
    conn.execute(
        """INSERT INTO suppressions (email, reason, source, created_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(email) DO UPDATE SET
             reason = excluded.reason,
             source = excluded.source""",
        (normalized_email, reason, source, now),
    )
    cursor = conn.execute(
        """UPDATE drafts
           SET status = 'suppressed', updated_at = ?
           WHERE lower(email) = lower(?)
             AND status IN ('pending_review', 'approved')""",
        (now, normalized_email),
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected


def is_suppressed(db_path: str, email: str) -> bool:
    """Return True when an email is on the suppression list."""
    conn = _connect(db_path)
    row = conn.execute(
        "SELECT 1 FROM suppressions WHERE lower(email) = lower(?) LIMIT 1",
        (_normalize_email(email),),
    ).fetchone()
    conn.close()
    return row is not None


def list_suppressions(db_path: str) -> list[dict]:
    """Return suppressed emails ordered by creation time."""
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM suppressions ORDER BY created_at, email"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def has_terminal_status(db_path: str, email: str, campaign_name: str = DEFAULT_CAMPAIGN) -> bool:
    """Return True if a contact already replied, bounced, or was suppressed."""
    conn = _connect(db_path)
    row = conn.execute(
        """SELECT 1 FROM drafts
           WHERE lower(email) = lower(?)
             AND campaign_name = ?
             AND status IN ('replied', 'bounced', 'suppressed')
           LIMIT 1""",
        (_normalize_email(email), campaign_name),
    ).fetchone()
    conn.close()
    return row is not None


def list_due_followup_sources(
    db_path: str,
    next_step_number: int,
    as_of: str | datetime | None = None,
    campaign_name: str = DEFAULT_CAMPAIGN,
    delay_days: int | None = None,
) -> list[dict]:
    """Return sent drafts that are due to receive the next sequence step."""
    if next_step_number not in FOLLOW_UP_DELAYS_DAYS:
        raise ValueError("next_step_number must be 2 or 3")

    previous_step = next_step_number - 1
    days = delay_days if delay_days is not None else FOLLOW_UP_DELAYS_DAYS[next_step_number]
    if as_of is None:
        as_of_dt = datetime.now(timezone.utc)
    elif isinstance(as_of, datetime):
        as_of_dt = as_of.astimezone(timezone.utc) if as_of.tzinfo else as_of.replace(tzinfo=timezone.utc)
    else:
        as_of_dt = _parse_datetime(as_of)

    conn = _connect(db_path)
    rows = conn.execute(
        """SELECT * FROM drafts
           WHERE campaign_name = ?
             AND step_number = ?
             AND status = 'sent'
             AND sent_at IS NOT NULL
           ORDER BY sent_at, id""",
        (campaign_name, previous_step),
    ).fetchall()

    due = []
    for row in rows:
        draft = dict(row)
        sent_at = _parse_datetime(draft["sent_at"])
        if sent_at + timedelta(days=days) > as_of_dt:
            continue

        email = _normalize_email(draft["email"])
        lead_key = _same_lead_clause_value(draft)

        suppressed = conn.execute(
            "SELECT 1 FROM suppressions WHERE lower(email) = lower(?) LIMIT 1",
            (email,),
        ).fetchone()
        if suppressed:
            continue

        terminal = conn.execute(
            """SELECT 1 FROM drafts
               WHERE campaign_name = ?
                 AND (lower(email) = lower(?) OR lead_key = ?)
                 AND status IN ('replied', 'bounced', 'suppressed')
               LIMIT 1""",
            (campaign_name, email, lead_key),
        ).fetchone()
        if terminal:
            continue

        later_step = conn.execute(
            """SELECT 1 FROM drafts
               WHERE campaign_name = ?
                 AND (lower(email) = lower(?) OR lead_key = ?)
                 AND step_number >= ?
               LIMIT 1""",
            (campaign_name, email, lead_key, next_step_number),
        ).fetchone()
        if later_step:
            continue

        due.append(draft)

    conn.close()
    return due


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


def list_approved(db_path: str) -> list[dict]:
    """Return all drafts with status=approved."""
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM drafts WHERE status = 'approved' ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_sent(db_path: str, draft_id: int, sent_at: str | None = None) -> None:
    """Mark a draft as sent and record the timestamp."""
    now = sent_at or _now()
    conn = _connect(db_path)
    cursor = conn.execute(
        "UPDATE drafts SET status = 'sent', sent_at = ?, updated_at = ? WHERE id = ?",
        (now, now, draft_id),
    )
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise ValueError(f"Draft id {draft_id} not found")
    conn.close()


def mark_replied(db_path: str, draft_id: int) -> None:
    """Mark a draft as replied so the sequence stops for that contact."""
    draft = get_draft(db_path, draft_id)
    if not draft:
        raise ValueError(f"Draft id {draft_id} not found")
    update_status(db_path, draft_id, "replied")
    conn = _connect(db_path)
    conn.execute(
        """UPDATE drafts
           SET status = 'suppressed', updated_at = ?
           WHERE lower(email) = lower(?)
             AND campaign_name = ?
             AND status IN ('pending_review', 'approved')""",
        (_now(), draft["email"], draft["campaign_name"]),
    )
    conn.commit()
    conn.close()


def mark_bounced(db_path: str, draft_id: int) -> None:
    """Mark a draft as bounced and suppress future unsent drafts for that email."""
    draft = get_draft(db_path, draft_id)
    if not draft:
        raise ValueError(f"Draft id {draft_id} not found")
    update_status(db_path, draft_id, "bounced")
    suppress_email(db_path, draft["email"], reason="bounced", source="mark_outcome")


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
