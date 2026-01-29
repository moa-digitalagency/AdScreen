import unittest
import os
from unittest.mock import patch, MagicMock

# Setup env
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['INIT_DB_MODE'] = 'true' # Skip init logic
os.environ['SESSION_SECRET'] = 'test'

from services.input_validator import is_safe_url

class TestSSRF(unittest.TestCase):
    @patch('socket.gethostbyname')
    def test_is_safe_url(self, mock_gethostbyname):
        # Safe public IP
        mock_gethostbyname.return_value = '8.8.8.8'
        self.assertTrue(is_safe_url('http://google.com'))

        # Private IP
        mock_gethostbyname.return_value = '192.168.1.1'
        self.assertFalse(is_safe_url('http://internal-router'))

        # Localhost
        mock_gethostbyname.return_value = '127.0.0.1'
        self.assertFalse(is_safe_url('http://localhost:5000'))

        # Direct IP usage (bypass DNS mock if logic parses IP first)
        self.assertTrue(is_safe_url('http://8.8.8.8'))
        self.assertFalse(is_safe_url('http://127.0.0.1'))
        self.assertFalse(is_safe_url('http://10.0.0.1'))

        # Invalid URL
        self.assertFalse(is_safe_url('not_a_url'))

    def test_schemes(self):
        # Test that allowed schemes are not part of is_safe_url default (it focuses on http/https by default)
        with patch('socket.gethostbyname', return_value='8.8.8.8'):
            # Should fail by default
            self.assertFalse(is_safe_url('rtsp://8.8.8.8/stream'))

            # Should pass if allowed
            self.assertTrue(is_safe_url('rtsp://8.8.8.8/stream', allowed_protocols=('rtsp',)))
            self.assertTrue(is_safe_url('udp://8.8.8.8:1234', allowed_protocols=('udp',)))

if __name__ == '__main__':
    unittest.main()
