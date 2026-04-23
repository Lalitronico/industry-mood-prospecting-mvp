#!/usr/bin/env python3
"""CLI: manage the email suppression list.

Usage:
    python suppress_email.py add someone@example.com --reason unsubscribed
    python suppress_email.py list
"""

import argparse

from queue_db import init_queue, list_suppressions, suppress_email


DEFAULT_DB = "drafts_queue.db"


def main():
    parser = argparse.ArgumentParser(description="Manage suppressed emails.")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Queue DB path (default: {DEFAULT_DB})")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Suppress one or more emails")
    add_parser.add_argument("emails", nargs="+", help="Email address(es) to suppress")
    add_parser.add_argument("--reason", default="manual", help="Suppression reason")
    add_parser.add_argument("--source", default="cli", help="Where the suppression came from")

    subparsers.add_parser("list", help="List suppressed emails")

    args = parser.parse_args()
    init_queue(args.db)

    if args.command == "add":
        for email in args.emails:
            affected = suppress_email(args.db, email, reason=args.reason, source=args.source)
            print(f"Suppressed {email} ({affected} unsent draft(s) updated).")
        return

    for row in list_suppressions(args.db):
        print(f"{row['email']} | {row['reason']} | {row['source']} | {row['created_at']}")


if __name__ == "__main__":
    main()
