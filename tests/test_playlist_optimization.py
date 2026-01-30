import unittest
import os
import sys
from datetime import datetime, timedelta

# Set environment variables BEFORE importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SESSION_SECRET'] = 'test-secret'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret'
os.environ['INIT_DB_MODE'] = 'false'

from app import app, db
from models import Screen, Organization, AdContent, User, SiteSetting
from sqlalchemy import text

class TestPlaylistOptimization(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            # Ensure tables
            db.create_all()
            SiteSetting.preload_cache()

            # Create Org
            self.org = Organization(name="Test Org", email="test@org.com", country="US", city="New York")
            db.session.add(self.org)
            db.session.commit()
            self.org_id = self.org.id

            # Create Screen
            self.screen = Screen(
                name="Test Screen",
                unique_code="SCREEN1",
                organization_id=self.org.id,
                is_active=True
            )
            self.screen.set_password("password")
            db.session.add(self.screen)
            db.session.commit()
            self.screen_id = self.screen.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_playlist_inclusion(self):
        with app.app_context():
            now = datetime.utcnow()

            # Ad 1: Target Screen (Correct)
            ad1 = AdContent(name="Ad1", reference="REF1", file_path="ad1.jpg",
                            status=AdContent.STATUS_ACTIVE,
                            target_type=AdContent.TARGET_SCREEN, target_screen_id=self.screen_id)

            # Ad 2: Target Organization (Correct)
            ad2 = AdContent(name="Ad2", reference="REF2", file_path="ad2.jpg",
                            status=AdContent.STATUS_ACTIVE,
                            target_type=AdContent.TARGET_ORGANIZATION, target_organization_id=self.org_id)

            # Ad 3: Target CSV (Correct)
            ad3 = AdContent(name="Ad3", reference="REF3", file_path="ad3.jpg",
                            status=AdContent.STATUS_ACTIVE,
                            target_type=AdContent.TARGET_SCREENS, selected_screen_ids=f"{self.screen_id},999")

            # Ad 4: Target Other Screen (Incorrect)
            ad4 = AdContent(name="Ad4", reference="REF4", file_path="ad4.jpg",
                            status=AdContent.STATUS_ACTIVE,
                            target_type=AdContent.TARGET_SCREEN, target_screen_id=999)

            # Ad 5: Expired (Incorrect)
            # Make sure it targets the screen otherwise it's filtered by target first
            ad5 = AdContent(name="Ad5", reference="REF5", file_path="ad5.jpg",
                            status=AdContent.STATUS_ACTIVE,
                            target_type=AdContent.TARGET_SCREEN, target_screen_id=self.screen_id,
                            schedule_type=AdContent.SCHEDULE_PERIOD,
                            start_date=now - timedelta(days=10),
                            end_date=now - timedelta(days=1))

            # Ad 6: Scheduled but ready (Correct) - Should be updated to Active
            ad6 = AdContent(name="Ad6", reference="REF6", file_path="ad6.jpg",
                            status=AdContent.STATUS_SCHEDULED,
                            target_type=AdContent.TARGET_SCREEN, target_screen_id=self.screen_id,
                            schedule_type=AdContent.SCHEDULE_PERIOD,
                            start_date=now - timedelta(hours=1),
                            end_date=now + timedelta(days=1))

            db.session.add_all([ad1, ad2, ad3, ad4, ad5, ad6])
            db.session.commit()

            ad6_id = ad6.id

        with self.client.session_transaction() as sess:
            sess['screen_id'] = self.screen_id

        resp = self.client.get('/player/api/playlist')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        playlist = data['playlist']

        # Filter playlist for ads
        ads = [item for item in playlist if item.get('category') == 'ad_content']
        ad_names = [a['name'] for a in ads]

        self.assertIn("Ad1", ad_names)
        self.assertIn("Ad2", ad_names)
        self.assertIn("Ad3", ad_names)
        self.assertNotIn("Ad4", ad_names)
        self.assertNotIn("Ad5", ad_names)
        self.assertIn("Ad6", ad_names)

        # Verify Ad6 status update
        with app.app_context():
            ad6_db = db.session.get(AdContent, ad6_id)
            self.assertEqual(ad6_db.status, AdContent.STATUS_ACTIVE)

if __name__ == '__main__':
    unittest.main()
