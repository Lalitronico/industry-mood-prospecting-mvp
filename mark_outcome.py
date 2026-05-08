#!/usr/bin/env python3
"""CLI: mark a sent draft outcome.

Usage:
    python mark_outcome.py replied 12
    python mark_outcome.py positive_reply 12
    python mark_outcome.py demo_booked 12
    python mark_outcome.py not_interested 12
    python mark_outcome.py bounced 12
"""

import argparse

from queue_db import (
    init_queue,
    mark_bounced,
    mark_demo_booked,
    mark_not_interested,
    mark_positive_reply,
    mark_replied,
)


DEFAULT_DB = "drafts_queue.db"


def main():
    parser = argparse.ArgumentParser(description="Mark commercial outcomes.")
    parser.add_argument(
        "outcome",
        choices=["replied", "positive_reply", "demo_booked", "not_interested", "bounced"],
        help="Outcome to record",
    )
    parser.add_argument("ids", nargs="+", type=int, help="Draft id(s)")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Queue DB path (default: {DEFAULT_DB})")
    args = parser.parse_args()

    init_queue(args.db)
    markers = {
        "replied": mark_replied,
        "positive_reply": mark_positive_reply,
        "demo_booked": mark_demo_booked,
        "not_interested": mark_not_interested,
        "bounced": mark_bounced,
    }
    marker = markers[args.outcome]

    for draft_id in args.ids:
        marker(args.db, draft_id)
        print(f"Marked #{draft_id} as {args.outcome}.")


if __name__ == "__main__":
    main()
