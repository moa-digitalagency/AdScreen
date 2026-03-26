#!/usr/bin/env python3
"""Quick test to verify booking page works"""
import sys
import os
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, '.env'))
sys.path.insert(0, project_root)

from app import app, db
from models import Screen

def test_booking_page():
    """Test that screens have content types available"""
    with app.app_context():
        screens = Screen.query.limit(5).all()

        if not screens:
            print("❌ No screens found in database")
            return False

        print(f"Found {len(screens)} screen(s)\n")

        for screen in screens:
            print(f"Screen: {screen.name} ({screen.unique_code})")
            print(f"  TimeSlots: {len(screen.time_slots)}")

            content_types = set()
            for slot in screen.time_slots:
                if slot.content_type:
                    content_types.add(slot.content_type.lower())

            if not content_types:
                print(f"  ⚠️  NO CONTENT TYPES FOUND")
            else:
                print(f"  ✓ Available: {', '.join(sorted(content_types))}")

            for slot in screen.time_slots[:3]:
                print(f"    - {slot.content_type} {slot.duration_seconds}s @ {slot.price_per_play}€")

            print()

        return True


if __name__ == '__main__':
    success = test_booking_page()
    sys.exit(0 if success else 1)
