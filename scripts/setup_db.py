#!/usr/bin/env python3
"""
Setup script for Industry Mood Prospecting MVP database.
Run this to initialize the SQLite database.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, engine
from app import models


def main():
    print("🗄️  Industry Mood Prospecting MVP - Database Setup")
    print("=" * 50)
    
    try:
        print("\n📦 Creating tables...")
        init_db()
        print("✅ Database initialized successfully!")
        print(f"📍 Database file: {engine.url}")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")
        
        print("\n🚀 Ready to start the application!")
        print("   Run: uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()