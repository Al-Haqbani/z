import unittest
from unittest.mock import patch, Mock

try:
    import requests  # noqa: F401
except Exception:  # pragma: no cover - requests may be missing
    requests = None

from core import token_verifier

@unittest.skipIf(requests is None, "requests not installed")
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

    @patch('core.token_verifier.requests.get')
    def test_verify_kaggle_key(self, mock_get):
        mock_get.return_value = self.mock_response(200)
        self.assertTrue(token_verifier.verify_kaggle_key('kaggle_token'))
        mock_get.return_value = self.mock_response(403)
        self.assertFalse(token_verifier.verify_kaggle_key('bad'))

    @patch('core.token_verifier.requests.get')
    def test_verify_anthropic_key(self, mock_get):
        mock_get.return_value = self.mock_response(200)
        self.assertTrue(token_verifier.verify_anthropic_key('anthropic'))
        mock_get.return_value = self.mock_response(401)
        self.assertFalse(token_verifier.verify_anthropic_key('bad'))

    @patch('core.token_verifier.requests.get')
    def test_verify_gemini_key(self, mock_get):
        mock_get.return_value = self.mock_response(200, {'models': []})
        self.assertTrue(token_verifier.verify_gemini_key('gemini'))
        mock_get.return_value = self.mock_response(403)
        self.assertFalse(token_verifier.verify_gemini_key('bad'))

    @patch('core.token_verifier.requests.get')
    def test_verify_replicate_key(self, mock_get):
        mock_get.return_value = self.mock_response(200)
        self.assertTrue(token_verifier.verify_replicate_key('r8_valid'))
        mock_get.return_value = self.mock_response(401)
        self.assertFalse(token_verifier.verify_replicate_key('bad'))

    @patch('core.token_verifier.requests.get')
    def test_verify_stability_key(self, mock_get):
        mock_get.return_value = self.mock_response(200)
        self.assertTrue(token_verifier.verify_stability_key('sk_valid'))
        mock_get.return_value = self.mock_response(403)
        self.assertFalse(token_verifier.verify_stability_key('bad'))

    @patch('core.token_verifier.requests.get')
    def test_verify_salesforce_token(self, mock_get):
        mock_get.return_value = self.mock_response(200)
        self.assertTrue(token_verifier.verify_salesforce_token('00Dxxx!tok'))
        mock_get.return_value = self.mock_response(401)
        self.assertFalse(token_verifier.verify_salesforce_token('bad'))

    def test_get_poc_command(self):
        cmd = token_verifier.get_poc_command('GitHub Token', 'ghp_test')
        self.assertIn('ghp_test', cmd)
        self.assertIn('api.github.com', cmd)

if __name__ == '__main__':
    unittest.main()
