#!/usr/bin/env python3
"""CLI: approve or reject a draft by id.

Usage:
    python review_draft.py approve 1
    python review_draft.py reject 2
    python review_draft.py approve 1 2 3           # batch
    python review_draft.py reject 4 --db queue.db
"""

import argparse
import sys

from queue_db import update_status, get_draft


DEFAULT_DB = "drafts_queue.db"


def main():
    parser = argparse.ArgumentParser(description="Approve or reject drafts by id.")
    parser.add_argument("action", choices=["approve", "reject"], help="Action to take")
    parser.add_argument("ids", nargs="+", type=int, help="Draft id(s)")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Queue DB path (default: {DEFAULT_DB})")
    args = parser.parse_args()

    status = "approved" if args.action == "approve" else "rejected"
    icon = "✅" if args.action == "approve" else "❌"

    for draft_id in args.ids:
        try:
            update_status(args.db, draft_id, status)
            draft = get_draft(args.db, draft_id)
            print(f"  {icon} #{draft_id} {status} — {draft['company']} ({draft['email']})")
        except ValueError as e:
            print(f"  ⚠ #{draft_id}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
