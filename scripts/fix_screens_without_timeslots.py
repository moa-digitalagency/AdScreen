#!/usr/bin/env python3
"""
Migration script to add default TimeSlots to screens that don't have any.
Run from project root: python scripts/fix_screens_without_timeslots.py
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables before importing app
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, '.env'))

sys.path.insert(0, project_root)

from app import app, db
from models import Screen, TimeSlot

def add_default_timeslots_to_screens():
    """Add default TimeSlots to screens that have none"""
    with app.app_context():
        # Find screens with no time_slots
        screens_without_slots = db.session.query(Screen).outerjoin(TimeSlot).filter(
            TimeSlot.id == None
        ).distinct().all()

        if not screens_without_slots:
            print("✓ All screens already have TimeSlots configured")
            return True

        print(f"Found {len(screens_without_slots)} screen(s) without TimeSlots\n")

        default_slots = [
            ('image', 10),
            ('image', 15),
            ('image', 30),
            ('video', 10),
            ('video', 15),
            ('video', 30),
        ]

        for screen in screens_without_slots:
            print(f"Adding default TimeSlots to screen: {screen.name} (ID: {screen.id})")

            for content_type, duration in default_slots:
                try:
                    calculated_price = screen.calculate_slot_price(duration)
                    slot = TimeSlot(
                        screen_id=screen.id,
                        content_type=content_type,
                        duration_seconds=duration,
                        price_per_play=calculated_price
                    )
                    db.session.add(slot)
                    print(f"  ✓ Added {content_type} slot: {duration}s @ {calculated_price}€")
                except Exception as e:
                    print(f"  ✗ Error adding {content_type} slot: {e}")
                    return False

            try:
                db.session.commit()
                print(f"  ✓ Successfully saved 6 TimeSlots\n")
            except Exception as e:
                db.session.rollback()
                print(f"  ✗ Error saving TimeSlots: {e}")
                return False

        print(f"✓ Migration complete - {len(screens_without_slots)} screen(s) updated")
        return True


if __name__ == '__main__':
    success = add_default_timeslots_to_screens()
    sys.exit(0 if success else 1)
