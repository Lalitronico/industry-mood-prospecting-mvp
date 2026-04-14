#!/usr/bin/env python3
"""CLI: send approved drafts via a controlled sender backend.

Usage:
    python send_drafts.py --db drafts_queue.db --mode dry-run
    python send_drafts.py --db drafts_queue.db --mode file-outbox --outbox outbox/
"""

import argparse
import sys

from sender import send_approved, DryRunBackend, FileOutboxBackend


DEFAULT_DB = "drafts_queue.db"


def main():
    parser = argparse.ArgumentParser(description="Send approved drafts.")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Queue DB path (default: {DEFAULT_DB})")
    parser.add_argument(
        "--mode", choices=["dry-run", "file-outbox"], default="dry-run",
        help="Send mode (default: dry-run)",
    )
    parser.add_argument("--outbox", default="outbox/", help="Outbox directory for file-outbox mode")
    args = parser.parse_args()

    if args.mode == "dry-run":
        backend = DryRunBackend()
    elif args.mode == "file-outbox":
        backend = FileOutboxBackend(args.outbox)
    else:
        print(f"Unknown mode: {args.mode}", file=sys.stderr)
        sys.exit(1)

    count = send_approved(args.db, backend)
    print(f"\nSent {count} draft(s) via {args.mode}.")


if __name__ == "__main__":
    main()
