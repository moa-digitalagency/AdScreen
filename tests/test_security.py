"""
 * Nom de l'application : Shabaka AdScreen
 * Description : Security tests for audit verification
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""
import unittest
import os
import sys

# Ensure we can import from root
sys.path.append(os.getcwd())

# Mock DB URL before import
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SESSION_SECRET'] = 'test_secret'
os.environ['INIT_DB_MODE'] = 'true' # Prevent superadmin creation logic which might trigger other imports

# Import app first to resolve circular deps
from app import app
from routes.player_routes import is_safe_url

class TestSecurity(unittest.TestCase):
    def test_is_safe_url(self):
        print("\nTesting is_safe_url...")
        # Public IPs should be safe
        self.assertTrue(is_safe_url('http://8.8.8.8'), "Public IP should be safe")

        # Private IPs should be unsafe
        self.assertFalse(is_safe_url('http://127.0.0.1'), "Localhost IP should be unsafe")
        self.assertFalse(is_safe_url('http://localhost'), "Localhost domain should be unsafe")
        self.assertFalse(is_safe_url('http://192.168.1.1'), "Private IP should be unsafe")
        self.assertFalse(is_safe_url('http://10.0.0.1'), "Private IP should be unsafe")
        self.assertFalse(is_safe_url('http://[::1]'), "IPv6 Loopback should be unsafe")

        # Schemes
        self.assertTrue(is_safe_url('rtsp://8.8.8.8/stream'), "RTSP Public should be safe")
        self.assertFalse(is_safe_url('rtsp://127.0.0.1/stream'), "RTSP Local should be unsafe")

if __name__ == '__main__':
    unittest.main()
