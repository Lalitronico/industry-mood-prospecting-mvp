"""Controlled sender abstraction.

Backends:
  - DryRunBackend: prints what would be sent (no real email)
  - FileOutboxBackend: writes one .txt file per draft into an outbox directory
  - ResendBackend: sends approved drafts through the Resend Email API

Backends implement:
  .send(draft_dict) -> bool
"""

import hashlib
import json
import os
import sys
import urllib.request


class DryRunBackend:
    """Logs the send action to stdout. No real sending."""

    def send(self, draft: dict) -> bool:
        print(f"[DRY RUN] To: {draft['email']} | Subject: {draft['subject']}")
        return True


class ResendBackend:
    """Send one approved draft through the Resend Email API."""

    API_URL = "https://api.resend.com/emails"

    def __init__(
        self,
        api_key: str | None = None,
        from_email: str | None = None,
        reply_to: str | None = None,
        requester=None,
        timeout: int = 30,
    ):
        self.api_key = ((os.getenv("RESEND_API_KEY") or "") if api_key is None else api_key or "").strip()
        if from_email is None:
            self.from_email = (
                os.getenv("OUTREACH_FROM_EMAIL")
                or os.getenv("RESEND_FROM_EMAIL")
                or ""
            ).strip()
        else:
            self.from_email = (from_email or "").strip()
        self.reply_to = ((os.getenv("RESEND_REPLY_TO") or "") if reply_to is None else reply_to or "").strip()
        self.requester = requester
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("RESEND_API_KEY is required for Resend sending")
        if not self.from_email:
            raise ValueError("from_email or OUTREACH_FROM_EMAIL is required for Resend sending")

    @staticmethod
    def _idempotency_key(draft: dict) -> str:
        draft_id = draft.get("id")
        if draft_id is None:
            raise ValueError("draft id is required for Resend idempotency")
        campaign = draft.get("campaign_name", "first_wave_local")
        step = draft.get("step_number", 1)
        email_hash = hashlib.sha256(draft["email"].strip().lower().encode("utf-8")).hexdigest()[:12]
        return f"industry-mood-{campaign}-s{step}-d{draft_id}-{email_hash}"

    def _payload(self, draft: dict) -> dict:
        payload = {
            "from": self.from_email,
            "to": [draft["email"]],
            "subject": draft["subject"],
            "text": draft["body_text"],
        }
        if self.reply_to:
            payload["reply_to"] = self.reply_to
        return payload

    def _headers(self, draft: dict) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": self._idempotency_key(draft),
        }

    def send(self, draft: dict) -> bool:
        draft_id = draft.get("id")
        payload = self._payload(draft)
        headers = self._headers(draft)

        if self.requester is None:
            data = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                self.API_URL,
                data=data,
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    response.read()
                    return 200 <= response.status < 300
            except Exception as exc:
                print(f"[RESEND ERROR] To: {draft.get('email')} | {exc}")
                return False

        try:
            response = self.requester.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except Exception:
            raise RuntimeError(f"Resend request failed for draft {draft_id}") from None
        if not 200 <= response.status_code < 300:
            raise RuntimeError(
                f"Resend send failed for draft {draft_id}: "
                f"HTTP {response.status_code} {response.text}"
            )
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


def send_approved(db_path: str, backend, limit: int | None = None) -> int:
    """Send approved drafts using the given backend. Returns count sent.

    `limit` caps successful sends, not skipped/suppressed drafts. This makes it
    safe to run tiny first-wave batches while still cleaning invalid approved
    drafts encountered before the limit is reached.
    """
    from queue_db import has_terminal_status, is_suppressed, list_approved, mark_sent, suppress_email, update_status
    from validators import has_valid_email_syntax

    drafts = list_approved(db_path)
    count = 0
    for draft in drafts:
        if limit is not None and count >= limit:
            break
        if not has_valid_email_syntax(draft.get("email")):
            suppress_email(db_path, draft["email"], reason="invalid_email", source="send_approved")
            continue
        if is_suppressed(db_path, draft["email"]) or has_terminal_status(
            db_path,
            draft["email"],
            draft.get("campaign_name", "first_wave_local"),
        ):
            update_status(db_path, draft["id"], "suppressed")
            continue
        try:
            ok = backend.send(draft)
        except Exception as exc:
            update_status(db_path, draft["id"], "failed")
            print(
                f"Failed draft #{draft['id']} ({draft['email']}): {exc}",
                file=sys.stderr,
            )
            continue
        if ok:
            mark_sent(db_path, draft["id"])
            count += 1
    return count
