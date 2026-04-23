#!/usr/bin/env python3
"""CLI: mark a sent draft outcome.

Usage:
    python mark_outcome.py replied 12
    python mark_outcome.py bounced 12
"""

import argparse

from queue_db import init_queue, mark_bounced, mark_replied


DEFAULT_DB = "drafts_queue.db"


def main():
    parser = argparse.ArgumentParser(description="Mark replied or bounced outcomes.")
    parser.add_argument("outcome", choices=["replied", "bounced"], help="Outcome to record")
    parser.add_argument("ids", nargs="+", type=int, help="Draft id(s)")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Queue DB path (default: {DEFAULT_DB})")
    args = parser.parse_args()

    init_queue(args.db)
    marker = mark_replied if args.outcome == "replied" else mark_bounced

    for draft_id in args.ids:
        marker(args.db, draft_id)
        print(f"Marked #{draft_id} as {args.outcome}.")


if __name__ == "__main__":
    main()
