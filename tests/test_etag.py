import unittest
import os
from unittest.mock import patch, MagicMock
from flask import session

# Set env vars before importing app
os.environ['DATABASE_URL'] = 'sqlite:///test_etag.db'
os.environ['INIT_DB_MODE'] = 'false'
os.environ['SESSION_SECRET'] = 'testsecret'

from app import app, db
from models import Screen, Organization

class TestETag(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Create dummy data
        org = Organization(name="Test Org", email="test@test.com")
        db.session.add(org)
        db.session.commit()

        self.screen = Screen(name="Test Screen", organization_id=org.id)
        db.session.add(self.screen)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        try:
            os.remove('test_etag.db')
        except OSError:
            pass

    def test_playlist_etag(self):
        with self.client.session_transaction() as sess:
            sess['screen_id'] = self.screen.id

        # First request: 200 OK and ETag
        response = self.client.get('/player/api/playlist')
        if response.status_code != 200:
            print(f"Response: {response.data}")
            print(f"Screen ID: {self.screen.id}")
        self.assertEqual(response.status_code, 200)
        etag = response.headers.get('ETag')
        self.assertIsNotNone(etag)

        # Second request with ETag: 304 Not Modified
        response2 = self.client.get('/player/api/playlist', headers={'If-None-Match': etag})
        self.assertEqual(response2.status_code, 304)

    def test_screen_mode_etag(self):
        with self.client.session_transaction() as sess:
            sess['screen_id'] = self.screen.id

        response = self.client.get('/player/api/screen-mode')
        self.assertEqual(response.status_code, 200)
        etag = response.headers.get('ETag')

        response2 = self.client.get('/player/api/screen-mode', headers={'If-None-Match': etag})
        self.assertEqual(response2.status_code, 304)

if __name__ == '__main__':
    unittest.main()
