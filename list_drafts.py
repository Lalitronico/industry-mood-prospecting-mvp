#!/usr/bin/env python3
"""CLI: list pending drafts in the approval queue.

Usage:
    python list_drafts.py                          # default DB
    python list_drafts.py --db queue.db            # custom DB
    python list_drafts.py --all                    # show all statuses
"""

import argparse
import sys

from queue_db import _connect, list_pending


DEFAULT_DB = "drafts_queue.db"
STATUS_LABELS = {
    "pending_review": "PENDING",
    "approved": "APPROVED",
    "rejected": "REJECTED",
    "sent": "SENT",
    "suppressed": "SUPPRESSED",
    "replied": "REPLIED",
    "bounced": "BOUNCED",
}


def _list_all(db_path: str) -> list[dict]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM drafts ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _print_draft(d: dict, show_body: bool = True):
    status_label = STATUS_LABELS.get(d["status"], "?")
    print(f"--- Draft #{d['id']} [{status_label}] ---")
    print(f"  To:       {d['contact_name']} <{d['email']}>")
    print(f"  Company:  {d['company']}")
    print(f"  Template: {d['template_key']}")
    print(f"  Subject:  {d['subject']}")
    if show_body:
        print("  Body:")
        for line in d["body_text"].split("\n"):
            print(f"    {line}")
    print()


def main():
    parser = argparse.ArgumentParser(description="List drafts in the approval queue.")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Queue DB path (default: {DEFAULT_DB})")
    parser.add_argument("--all", action="store_true", help="Show all drafts, not just pending")
    parser.add_argument("--short", action="store_true", help="One-line summary per draft")
    args = parser.parse_args()

    try:
        drafts = _list_all(args.db) if args.all else list_pending(args.db)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Hint: run generate_drafts.py first to create the queue DB.", file=sys.stderr)
        sys.exit(1)

    if not drafts:
        label = "drafts" if args.all else "pending drafts"
        print(f"No {label} in {args.db}")
        sys.exit(0)

    if args.short:
        for d in drafts:
            label = STATUS_LABELS.get(d["status"], "?")
            print(
                f"  {label:8} #{d['id']:3} | {d['template_key']:3} | "
                f"{d['company'][:35]:<35} | {d['email']:<35} | {d['status']}"
            )
        print(f"\n{len(drafts)} draft(s)")
    else:
        for d in drafts:
            _print_draft(d)
        print(f"{len(drafts)} draft(s)")


if __name__ == "__main__":
    main()
