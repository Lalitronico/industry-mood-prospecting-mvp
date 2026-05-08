"""Controlled sender abstraction — stdlib only.

Backends:
  - DryRunBackend: prints what would be sent (no side effects)
  - FileOutboxBackend: writes one .txt file per draft into an outbox directory

Future backends (Resend, SMTP) can be added by implementing the same interface:
  .send(draft_dict) -> bool
"""

import json
import os
import urllib.request


class DryRunBackend:
    """Logs the send action to stdout. No real sending."""

    def send(self, draft: dict) -> bool:
        print(f"[DRY RUN] To: {draft['email']} | Subject: {draft['subject']}")
        return True


class ResendBackend:
    """Send approved drafts through the Resend email API."""

    api_url = "https://api.resend.com/emails"

    def __init__(self, api_key: str | None = None, from_email: str | None = None):
        self.api_key = api_key or os.getenv("RESEND_API_KEY", "")
        self.from_email = from_email or os.getenv("OUTREACH_FROM_EMAIL", "")
        if not self.api_key:
            raise ValueError("RESEND_API_KEY is required for ResendBackend")
        if not self.from_email:
            raise ValueError("OUTREACH_FROM_EMAIL is required for ResendBackend")

    def send(self, draft: dict) -> bool:
        payload = {
            "from": self.from_email,
            "to": [draft["email"]],
            "subject": draft["subject"],
            "text": draft["body_text"],
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.api_url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response.read()
                return 200 <= response.status < 300
        except Exception as exc:
            print(f"[RESEND ERROR] To: {draft.get('email')} | {exc}")
            return False


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
