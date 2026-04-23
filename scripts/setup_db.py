#!/usr/bin/env python3
"""
Setup script for Industry Mood Prospecting MVP database.
Run this to initialize the SQLite database.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, init_db
from app import models


def main():
    print("Industry Mood Prospecting MVP - Database Setup")
    print("=" * 50)

    try:
        print("\nCreating tables...")
        init_db()
        print("OK: Database initialized successfully.")
        print(f"Database file: {engine.url}")

        # List created tables
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"\nCreated {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")

        print("\nReady to start the application.")
        print("   Run: uvicorn app.main:app --reload")

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
