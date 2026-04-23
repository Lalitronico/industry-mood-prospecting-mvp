#!/usr/bin/env python3
"""CLI: generate outreach drafts from Excel leads into the approval queue.

Usage:
    python generate_drafts.py <xlsx_path>                    # generate into default DB
    python generate_drafts.py <xlsx_path> --db queue.db      # custom DB path
"""

import argparse
import sys

from drafts import generate_draft
from importer import import_leads
from queue_db import enqueue_draft_once, init_queue, is_suppressed


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
    recommended = [lead for lead in leads if lead["recommended"]]

    if not recommended:
        print("No recommended leads found.")
        sys.exit(0)

    # Initialize queue and generate drafts
    init_queue(args.db)
    created_count = 0
    skipped_count = 0
    suppressed_count = 0
    for lead in recommended:
        if is_suppressed(args.db, lead.get("email", "")):
            suppressed_count += 1
            print(
                f"  [---] --- | suppressed | "
                f"{lead['company'][:40]:<40} | {lead['email']}"
            )
            continue

        draft = generate_draft(lead)
        draft_id, created = enqueue_draft_once(args.db, draft)
        if created:
            created_count += 1
            status = "new"
        else:
            skipped_count += 1
            status = "existing"
        print(
            f"  [{draft_id:3}] {draft['role_bucket']:3} | "
            f"{status:8} | {lead['company'][:40]:<40} | {lead['email']}"
        )

    print(
        f"\nGenerated {created_count} new draft(s) into {args.db}; "
        f"skipped {skipped_count} existing draft(s); "
        f"ignored {suppressed_count} suppressed lead(s)."
    )
    print(f"Next: python list_drafts.py --db {args.db}")


if __name__ == "__main__":
    main()
