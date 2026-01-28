import os
import unittest
import time

# Set env before import
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['INIT_DB_MODE'] = 'true' # Avoid creating superadmin in global scope

from app import app, db
from models.site_setting import SiteSetting

class TestSiteSetting(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_caching(self):
        # 1. Set a value
        SiteSetting.set('test_key', 'initial_value')

        # 2. Get value (should cache)
        val = SiteSetting.get('test_key')
        self.assertEqual(val, 'initial_value')

        # 3. Modify DB directly (bypassing set) to test cache
        s = SiteSetting.query.filter_by(key='test_key').first()
        s.value = 'db_changed_value'
        db.session.commit()

        # 4. Get value again - should still be 'initial_value' due to cache
        val = SiteSetting.get('test_key')
        self.assertEqual(val, 'initial_value')

        # 5. Check internal cache
        self.assertIn('test_key', SiteSetting._cache)

        # 6. Test invalidation via set
        SiteSetting.set('test_key', 'new_value')
        # Should be removed from cache (my implementation deletes it)
        self.assertNotIn('test_key', SiteSetting._cache)

        val = SiteSetting.get('test_key')
        self.assertEqual(val, 'new_value')
        self.assertIn('test_key', SiteSetting._cache)

if __name__ == '__main__':
    unittest.main()
