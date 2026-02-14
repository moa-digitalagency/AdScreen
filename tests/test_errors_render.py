import unittest
from app import app
from flask import abort

# Define routes once at module level to avoid "setup method 'route' can no longer be called"
# if defined in setUp() which runs for each test.
@app.route('/test/400')
def test_400():
    abort(400)

@app.route('/test/403')
def test_403():
    abort(403)

@app.route('/test/451')
def test_451():
    abort(451)

class ErrorPagesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing
        self.client = self.app.test_client()

    def test_404_page(self):
        response = self.client.get('/non-existent-page-xyz')
        self.assertEqual(response.status_code, 404)
        # Check for French content (default)
        self.assertIn(b'Page non trouv', response.data)
        self.assertIn(b'tidycal.com', response.data) # Lead magnet
        self.assertIn(b'wa.me', response.data) # WhatsApp

    def test_400_page(self):
        response = self.client.get('/test/400')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Mauvaise requ', response.data)

    def test_403_page(self):
        response = self.client.get('/test/403')
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Acc', response.data) # Accès interdit

    def test_451_page(self):
        response = self.client.get('/test/451')
        self.assertEqual(response.status_code, 451)
        self.assertIn(b'Fahrenheit 451', response.data)
        self.assertIn(b'Classified', response.data)

if __name__ == '__main__':
    unittest.main()
