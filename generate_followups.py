#!/usr/bin/env python3
"""CLI: generate due follow-up drafts for the 3-step sequence.

Usage:
    python generate_followups.py --db drafts_queue.db
    python generate_followups.py --step 2 --as-of 2026-04-23T00:00:00+00:00
"""

import argparse

from drafts import generate_draft
from queue_db import (
    DEFAULT_CAMPAIGN,
    enqueue_draft_once,
    init_queue,
    list_due_followup_sources,
)


DEFAULT_DB = "drafts_queue.db"


def _generate_step(db_path: str, step_number: int, as_of: str | None, campaign_name: str) -> tuple[int, int]:
    sources = list_due_followup_sources(
        db_path,
        step_number,
        as_of=as_of,
        campaign_name=campaign_name,
    )
    created_count = 0
    skipped_count = 0

    for source in sources:
        draft = generate_draft(source, step_number=step_number)
        draft["campaign_name"] = campaign_name
        draft["lead_key"] = source.get("lead_key") or source["email"].lower()
        draft_id, created = enqueue_draft_once(db_path, draft)
        if created:
            created_count += 1
            status = "new"
        else:
            skipped_count += 1
            status = "existing"
        print(
            f"  [{draft_id:3}] step {step_number} | {status:8} | "
            f"{source['company'][:40]:<40} | {source['email']}"
        )

    return created_count, skipped_count


def main():
    parser = argparse.ArgumentParser(description="Generate due follow-up drafts.")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Queue DB path (default: {DEFAULT_DB})")
    parser.add_argument("--step", type=int, choices=[2, 3], help="Only generate one sequence step")
    parser.add_argument("--as-of", help="ISO datetime used as the due-date reference")
    parser.add_argument("--campaign", default=DEFAULT_CAMPAIGN, help=f"Campaign name (default: {DEFAULT_CAMPAIGN})")
    args = parser.parse_args()

    init_queue(args.db)
    steps = [args.step] if args.step else [2, 3]

    total_created = 0
    total_skipped = 0
    for step_number in steps:
        created, skipped = _generate_step(args.db, step_number, args.as_of, args.campaign)
        total_created += created
        total_skipped += skipped

    print(
        f"\nGenerated {total_created} follow-up draft(s); "
        f"skipped {total_skipped} existing draft(s)."
    )


if __name__ == "__main__":
    main()
