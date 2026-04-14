#!/usr/bin/env python3
"""CLI entrypoint: import leads from Excel, score, and optionally export CSV.

Usage:
    python import_leads.py <xlsx_path>                 # dry-run summary
    python import_leads.py <xlsx_path> -o leads.csv    # write recommended leads to CSV
    python import_leads.py <xlsx_path> --all -o all.csv # write ALL leads (not just recommended)
"""

import argparse
import csv
import sys

from importer import import_leads

CSV_FIELDS = [
    "company", "contact_name", "role", "email", "company_type",
    "size", "city", "score", "recommended",
]


def main():
    parser = argparse.ArgumentParser(
        description="Import & score leads from Industry Mood Excel file."
    )
    parser.add_argument("xlsx", help="Path to .xlsx file")
    parser.add_argument("-o", "--output", help="Write CSV to this path")
    parser.add_argument(
        "--all", action="store_true",
        help="Include all leads in CSV, not just recommended",
    )
    args = parser.parse_args()

    leads = import_leads(args.xlsx)
    recommended = [l for l in leads if l["recommended"]]

    # --- Summary ---
    print(f"Total leads parsed (deduplicated): {len(leads)}")
    print(f"Recommended (score >= 65):          {len(recommended)}")
    print(f"Unique companies (recommended):     {len(set(l['company'] for l in recommended))}")
    print()

    # Score distribution
    brackets = {"90-100": 0, "80-89": 0, "70-79": 0, "65-69": 0, "<65": 0}
    for l in leads:
        s = l["score"]
        if s >= 90:
            brackets["90-100"] += 1
        elif s >= 80:
            brackets["80-89"] += 1
        elif s >= 70:
            brackets["70-79"] += 1
        elif s >= 65:
            brackets["65-69"] += 1
        else:
            brackets["<65"] += 1
    print("Score distribution:")
    for bracket, count in brackets.items():
        print(f"  {bracket:>7}: {count}")
    print()

    # Top 10 recommended
    top = sorted(recommended, key=lambda l: l["score"], reverse=True)[:10]
    if top:
        print("Top 10 recommended leads:")
        for i, l in enumerate(top, 1):
            print(f"  {i:2}. [{l['score']:3}] {l['company'][:40]:<40} | {l['role'][:30]:<30} | {l['email']}")
    print()

    # --- CSV export ---
    if args.output:
        to_write = leads if args.all else recommended
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(to_write)
        print(f"Wrote {len(to_write)} leads to {args.output}")


if __name__ == "__main__":
    main()
