
import os
import sys
from app import app, db
from models.ad_content import AdContent
from models import Screen

def migrate():
    print("Starting migration of selected_screen_ids to association table...")

    with app.app_context():
        # Find all ads with TARGET_SCREENS
        ads = AdContent.query.filter_by(target_type=AdContent.TARGET_SCREENS).all()
        print(f"Found {len(ads)} ads targeting specific screens.")

        count = 0
        skipped = 0
        for ad in ads:
            # Check if relationship is already populated
            if ad.screens:
                skipped += 1
                continue

            if ad.selected_screen_ids:
                try:
                    screen_ids = [int(x) for x in ad.selected_screen_ids.split(',') if x.strip()]
                    if screen_ids:
                        screens = Screen.query.filter(Screen.id.in_(screen_ids)).all()
                        ad.screens = screens
                        count += 1
                        if count % 100 == 0:
                            db.session.commit()
                            print(f"Migrated {count} ads...")
                except Exception as e:
                    print(f"Error migrating ad {ad.id}: {e}")

        db.session.commit()
        print(f"Migration complete. Updated {count} ads. Skipped {skipped} already migrated ads.")

if __name__ == "__main__":
    migrate()
