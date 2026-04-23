"""Controlled sender abstraction — stdlib only.

Backends:
  - DryRunBackend: prints what would be sent (no side effects)
  - FileOutboxBackend: writes one .txt file per draft into an outbox directory

Future backends (Resend, SMTP) can be added by implementing the same interface:
  .send(draft_dict) -> bool
"""

import os


class DryRunBackend:
    """Logs the send action to stdout. No real sending."""

    def send(self, draft: dict) -> bool:
        print(f"[DRY RUN] To: {draft['email']} | Subject: {draft['subject']}")
        return True


class FileOutboxBackend:
    """Writes one .txt file per draft into an outbox directory."""

    def __init__(self, outbox_dir: str):
        self.outbox_dir = outbox_dir

    def send(self, draft: dict) -> bool:
        os.makedirs(self.outbox_dir, exist_ok=True)
        filename = f"draft_{draft.get('id', 'unknown')}.txt"
        path = os.path.join(self.outbox_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"To: {draft.get('contact_name', '')} <{draft['email']}>\n")
            f.write(f"Subject: {draft['subject']}\n")
            f.write(f"\n{draft['body_text']}\n")
        return True


def send_approved(db_path: str, backend) -> int:
    """Send all approved drafts using the given backend. Returns count sent."""
    from queue_db import has_terminal_status, is_suppressed, list_approved, mark_sent, update_status

    drafts = list_approved(db_path)
    count = 0
    for draft in drafts:
        if is_suppressed(db_path, draft["email"]) or has_terminal_status(
            db_path,
            draft["email"],
            draft.get("campaign_name", "first_wave_local"),
        ):
            update_status(db_path, draft["id"], "suppressed")
            continue
        ok = backend.send(draft)
        if ok:
            mark_sent(db_path, draft["id"])
            count += 1
    return count
