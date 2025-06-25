import unittest
from unittest.mock import patch, Mock

from core import token_verifier

class TestTokenVerifier(unittest.TestCase):
    def mock_response(self, status=200, json=None):
        resp = Mock()
        resp.status_code = status
        resp.json.return_value = json or {}
        return resp

    @patch('core.token_verifier.requests.get')
    def test_verify_github_token(self, mock_get):
        mock_get.return_value = self.mock_response(200)
        self.assertTrue(token_verifier.verify_github_token('ghp_valid'))
        mock_get.return_value = self.mock_response(401)
        self.assertFalse(token_verifier.verify_github_token('ghp_bad'))

    @patch('core.token_verifier.requests.post')
    def test_verify_slack_token(self, mock_post):
        mock_post.return_value = self.mock_response(200, {'ok': True})
        self.assertTrue(token_verifier.verify_slack_token('xoxb-valid'))
        mock_post.return_value = self.mock_response(200, {'ok': False})
        self.assertFalse(token_verifier.verify_slack_token('xoxb-invalid'))

if __name__ == '__main__':
    unittest.main()
