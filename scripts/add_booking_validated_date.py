#!/usr/bin/env python3
"""
Migration script to add validated_date column to bookings table
Run from project root: python scripts/add_booking_validated_date.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import inspect, text

def add_validated_date_column():
    """Add validated_date column to bookings table if it doesn't exist"""
    with app.app_context():
        # Check if column already exists
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('bookings')]

        if 'validated_date' in columns:
            print("✓ Column 'validated_date' already exists in 'bookings' table")
            return True

        try:
            # Add the column
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE bookings ADD COLUMN validated_date DATETIME"))
                conn.commit()
            print("✓ Successfully added 'validated_date' column to 'bookings' table")
            return True
        except Exception as e:
            print(f"✗ Error adding column: {e}")
            return False

if __name__ == '__main__':
    success = add_validated_date_column()
    sys.exit(0 if success else 1)
