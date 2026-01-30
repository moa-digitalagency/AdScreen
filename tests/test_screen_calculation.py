import unittest
import json
import os
import sys
from datetime import datetime, timedelta

# Set environment variables before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SESSION_SECRET'] = 'test_secret'
# We need routes registered, so INIT_DB_MODE must be false (default) or not 'true'
if 'INIT_DB_MODE' in os.environ:
    del os.environ['INIT_DB_MODE']

from app import app, db
from models import Screen, Organization, TimeSlot, User, TimePeriod

class TestScreenCalculation(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()

        with app.app_context():
            db.create_all()

            # Create superadmin
            self.admin = User(
                username='superadmin',
                email='admin@test.com',
                role='superadmin',
                is_active=True
            )
            self.admin.set_password('password')
            db.session.add(self.admin)

            # Create Organization
            self.org = Organization(name="Test Org", email="test@org.com", is_active=True, is_paid=True)
            db.session.add(self.org)
            db.session.flush()

            # Create Screens
            self.screen1 = Screen(name="Screen 1", organization_id=self.org.id, unique_code="S1", is_active=True)
            self.screen2 = Screen(name="Screen 2", organization_id=self.org.id, unique_code="S2", is_active=True)
            db.session.add_all([self.screen1, self.screen2])
            db.session.flush()

            # Create TimePeriods (required for calculate_availability)
            tp1 = TimePeriod(screen_id=self.screen1.id, name="All Day", start_hour=0, end_hour=24)
            tp2 = TimePeriod(screen_id=self.screen2.id, name="All Day", start_hour=0, end_hour=24)
            db.session.add_all([tp1, tp2])
            db.session.flush()

            # Create TimeSlots
            ts1 = TimeSlot(
                screen_id=self.screen1.id,
                content_type="image",
                duration_seconds=10,
                price_per_play=1.0,
                is_active=True
            )
            ts2 = TimeSlot(
                screen_id=self.screen2.id,
                content_type="image",
                duration_seconds=10,
                price_per_play=2.0,
                is_active=True
            )
            # Add a non-matching slot (wrong duration)
            ts3 = TimeSlot(
                screen_id=self.screen1.id,
                content_type="image",
                duration_seconds=20,
                price_per_play=5.0,
                is_active=True
            )

            db.session.add_all([ts1, ts2, ts3])
            db.session.commit()

            self.admin_id = self.admin.id
            self.screen1_id = self.screen1.id
            self.screen2_id = self.screen2.id
            self.org_id = self.org.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        with self.app.session_transaction() as sess:
            sess['_user_id'] = str(self.admin_id)
            sess['_fresh'] = True
            sess['_csrf_token'] = 'test_token'

    def test_calculate_available_screens(self):
        self.login()

        start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')

        payload = {
            "target_type": "organization",
            "target_organization_id": self.org_id,
            "start_date": start_date,
            "end_date": end_date,
            "slot_duration": 10,
            "content_type": "image",
            "min_plays": 5
        }

        response = self.app.post('/admin/ad-content/calculate-screens',
                                 data=json.dumps(payload),
                                 content_type='application/json',
                                 headers={'X-CSRF-Token': 'test_token'})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        # We expect both screens to be returned if they have availability
        # (Assuming calculate_availability returns > 5 plays for new screens)
        self.assertIn('screens', data)
        screens = data['screens']
        self.assertEqual(len(screens), 2)

        # Verify prices
        s1 = next(s for s in screens if s['id'] == self.screen1_id)
        s2 = next(s for s in screens if s['id'] == self.screen2_id)

        self.assertEqual(s1['price_per_play'], 1.0)
        self.assertEqual(s2['price_per_play'], 2.0)

    def test_calculate_ad_price(self):
        self.login()

        payload = {
            "screen_ids": [self.screen1_id, self.screen2_id],
            "num_plays": 10,
            "slot_duration": 10,
            "content_type": "image",
            "commission_rate": 30
        }

        response = self.app.post('/admin/ad-content/calculate-price',
                                 data=json.dumps(payload),
                                 content_type='application/json',
                                 headers={'X-CSRF-Token': 'test_token'})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(data['num_screens'], 2)
        self.assertEqual(data['num_plays_per_screen'], 10)

        # Screen 1: 1.0 * 10 = 10.0
        # Screen 2: 2.0 * 10 = 20.0
        # Total: 30.0
        self.assertEqual(data['total_price'], 30.0)

        # Verify individual screen details
        screens = data['screens']
        s1 = next(s for s in screens if s['screen_id'] == self.screen1_id)
        self.assertEqual(s1['price_per_play'], 1.0)
        self.assertEqual(s1['total_price'], 10.0)

if __name__ == '__main__':
    unittest.main()
