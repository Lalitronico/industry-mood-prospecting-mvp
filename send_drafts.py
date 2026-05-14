#!/usr/bin/env python3
"""CLI: send approved drafts via a controlled sender backend.

Usage:
    python send_drafts.py --db drafts_queue.db --mode dry-run
    python send_drafts.py --db drafts_queue.db --mode file-outbox --outbox outbox/
    python send_drafts.py --db drafts_queue.db --mode resend --limit 3 --confirm-send SEND
"""

import argparse
import sys

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is in requirements.txt
    load_dotenv = None

from sender import send_approved, DryRunBackend, FileOutboxBackend, ResendBackend


DEFAULT_DB = "drafts_queue.db"


def main(argv=None):
    if load_dotenv is not None:
        load_dotenv()

    parser = argparse.ArgumentParser(description="Send approved drafts.")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Queue DB path (default: {DEFAULT_DB})")
    parser.add_argument(
        "--mode", choices=["dry-run", "file-outbox", "resend"], default="dry-run",
        help="Send mode (default: dry-run)",
    )
    parser.add_argument("--outbox", default="outbox/", help="Outbox directory for file-outbox mode")
    parser.add_argument("--limit", type=int, help="Maximum number of successful sends in this run")
    parser.add_argument("--from-email", help="Verified Resend sender, e.g. 'Industry Mood <admin@industrymood.com>'")
    parser.add_argument("--reply-to", help="Optional Reply-To address for Resend")
    parser.add_argument(
        "--confirm-send",
        help="Required for real Resend sends. Must be exactly SEND.",
    )
    args = parser.parse_args(argv)

    if args.mode == "dry-run":
        backend = DryRunBackend()
    elif args.mode == "file-outbox":
        backend = FileOutboxBackend(args.outbox)
    elif args.mode == "resend":
        if args.confirm_send != "SEND":
            print(
                "Refusing real email send. Re-run with --confirm-send SEND "
                "after verifying approved drafts, domain auth, and --limit.",
                file=sys.stderr,
            )
            sys.exit(2)
        if args.limit is None or args.limit < 1:
            print(
                "Refusing real email send. Resend mode requires --limit with a positive integer.",
                file=sys.stderr,
            )
            sys.exit(2)
        try:
            backend = ResendBackend(from_email=args.from_email, reply_to=args.reply_to)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(2)
    else:
        print(f"Unknown mode: {args.mode}", file=sys.stderr)
        sys.exit(1)

    count = send_approved(args.db, backend, limit=args.limit)
    print(f"\nSent {count} draft(s) via {args.mode}.")


if __name__ == "__main__":
    main()
