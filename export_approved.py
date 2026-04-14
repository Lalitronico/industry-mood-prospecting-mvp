#!/usr/bin/env python3
"""Export approved drafts to CSV — stdlib only.

Usage:
    python export_approved.py --db drafts_queue.db -o approved.csv
    python export_approved.py                        # print to stdout
"""

import argparse
import csv
import sys

from queue_db import list_approved


CSV_FIELDS = ["id", "email", "contact_name", "company", "subject", "body_text", "status"]
DEFAULT_DB = "drafts_queue.db"


def export_approved_csv(db_path: str, output_path: str | None = None) -> list[dict]:
    """Return approved drafts as a list of dicts. Optionally write CSV to output_path."""
    rows = list_approved(db_path)
    if output_path:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Export approved drafts to CSV.")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Queue DB path (default: {DEFAULT_DB})")
    parser.add_argument("-o", "--output", help="Write CSV to this path (default: stdout)")
    args = parser.parse_args()

    rows = export_approved_csv(args.db, args.output)

    if args.output:
        print(f"Exported {len(rows)} approved draft(s) to {args.output}")
    else:
        if not rows:
            print("No approved drafts.", file=sys.stderr)
            return
        writer = csv.DictWriter(sys.stdout, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
