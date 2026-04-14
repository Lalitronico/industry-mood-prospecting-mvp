#!/usr/bin/env python3
"""CLI: generate outreach drafts from Excel leads into the approval queue.

Usage:
    python generate_drafts.py <xlsx_path>                    # generate into default DB
    python generate_drafts.py <xlsx_path> --db queue.db      # custom DB path
"""

import argparse
import sys

from importer import import_leads
from drafts import generate_draft
from queue_db import init_queue, enqueue_draft


DEFAULT_DB = "drafts_queue.db"


def main():
    parser = argparse.ArgumentParser(
        description="Generate outreach drafts from recommended leads into the approval queue."
    )
    parser.add_argument("xlsx", help="Path to .xlsx lead file")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Queue DB path (default: {DEFAULT_DB})")
    args = parser.parse_args()

    # Import and filter recommended leads
    leads = import_leads(args.xlsx)
    recommended = [l for l in leads if l["recommended"]]

    if not recommended:
        print("No recommended leads found.")
        sys.exit(0)

    # Initialize queue and generate drafts
    init_queue(args.db)
    count = 0
    for lead in recommended:
        draft = generate_draft(lead)
        draft_id = enqueue_draft(args.db, draft)
        count += 1
        print(f"  [{draft_id:3}] {draft['role_bucket']:3} | {lead['company'][:40]:<40} | {lead['email']}")

    print(f"\nGenerated {count} drafts into {args.db}")
    print(f"Next: python list_drafts.py --db {args.db}")


if __name__ == "__main__":
    main()
