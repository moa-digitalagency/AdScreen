import unittest
from datetime import datetime, timedelta
from app import app, db
from models.ad_content import AdContent
from models.user import User

class TestAdContentOptimization(unittest.TestCase):
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
            db.session.commit()
            self.admin_id = self.admin.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        with self.app.session_transaction() as sess:
            sess['_user_id'] = str(self.admin_id)
            sess['_fresh'] = True

    def test_status_update_logic(self):
        with app.app_context():
            now = datetime.utcnow()

            # 1. Scheduled -> Active
            ad1 = AdContent(
                name="To Active",
                reference="REF1",
                file_path="p1.jpg",
                status=AdContent.STATUS_SCHEDULED,
                schedule_type=AdContent.SCHEDULE_PERIOD,
                start_date=now - timedelta(days=1),
                end_date=now + timedelta(days=1)
            )

            # 2. Active -> Expired
            ad2 = AdContent(
                name="To Expired",
                reference="REF2",
                file_path="p2.jpg",
                status=AdContent.STATUS_ACTIVE,
                schedule_type=AdContent.SCHEDULE_PERIOD,
                start_date=now - timedelta(days=5),
                end_date=now - timedelta(days=1)
            )

            # 3. Scheduled -> Scheduled (Future)
            ad3 = AdContent(
                name="Stay Scheduled",
                reference="REF3",
                file_path="p3.jpg",
                status=AdContent.STATUS_SCHEDULED,
                schedule_type=AdContent.SCHEDULE_PERIOD,
                start_date=now + timedelta(days=1),
                end_date=now + timedelta(days=5)
            )

            db.session.add_all([ad1, ad2, ad3])
            db.session.commit()

            # Store IDs to fetch later
            ad1_id = ad1.id
            ad2_id = ad2.id
            ad3_id = ad3.id

            # Login
            self.login()

            # Hit the route
            response = self.app.get('/admin/ad-contents')
            if response.status_code != 200:
                print(response.data)
            self.assertEqual(response.status_code, 200)

            # Verify DB state
            ad1_db = db.session.get(AdContent, ad1_id)
            ad2_db = db.session.get(AdContent, ad2_id)
            ad3_db = db.session.get(AdContent, ad3_id)

            self.assertEqual(ad1_db.status, AdContent.STATUS_ACTIVE, "Should have become ACTIVE")
            self.assertEqual(ad2_db.status, AdContent.STATUS_EXPIRED, "Should have become EXPIRED")
            self.assertEqual(ad3_db.status, AdContent.STATUS_SCHEDULED, "Should remain SCHEDULED")

if __name__ == '__main__':
    unittest.main()
