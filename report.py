#!/usr/bin/env python3
"""CLI: print a simple commercial funnel report for the draft queue."""

import argparse

from queue_db import init_queue
from reports import campaign_summary

DEFAULT_DB = "drafts_queue.db"


def _rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.0%"
    return f"{(numerator / denominator) * 100:.1f}%"


def main():
    parser = argparse.ArgumentParser(description="Report commercial funnel metrics.")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Queue DB path (default: {DEFAULT_DB})")
    parser.add_argument("--campaign", help="Optional campaign_name filter")
    args = parser.parse_args()

    init_queue(args.db)
    summary = campaign_summary(args.db, campaign_name=args.campaign)
    sent = summary["sent_or_later"]

    print("Industry Mood Prospecting Report")
    print("================================")
    print(f"Total drafts:      {summary['total_drafts']}")
    print(f"Sent or later:     {sent}")
    print(f"Replies:           {summary['replied']} ({_rate(summary['replied'], sent)})")
    print(f"Positive replies:  {summary['positive_reply']} ({_rate(summary['positive_reply'], sent)})")
    print(f"Demos booked:      {summary['demo_booked']} ({_rate(summary['demo_booked'], sent)})")
    print(f"Not interested:    {summary['not_interested']} ({_rate(summary['not_interested'], sent)})")
    print(f"Bounced:           {summary['bounced']} ({_rate(summary['bounced'], sent)})")

    if summary["by_role"]:
        print("\nBy role")
        print("-------")
        for role, row in sorted(summary["by_role"].items()):
            print(
                f"{role:8} sent+ {row['sent_or_later']:3} | "
                f"replies {row['replied']:3} | "
                f"positive {row['positive_reply']:3} | "
                f"demos {row['demo_booked']:3}"
            )


if __name__ == "__main__":
    main()
