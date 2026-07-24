import base64
import unittest
from unittest.mock import MagicMock, patch

import hairstyle


class ParseResultTest(unittest.TestCase):
    def test_parses_plain_json(self):
        text = '{"status": "ok", "recommendations": []}'
        self.assertEqual(hairstyle._parse_result(text), {"status": "ok", "recommendations": []})

    def test_strips_markdown_fences(self):
        text = '```json\n{"status": "ok", "recommendations": []}\n```'
        self.assertEqual(hairstyle._parse_result(text), {"status": "ok", "recommendations": []})

    def test_falls_back_gracefully_on_invalid_json(self):
        result = hairstyle._parse_result('not json at all')
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["recommendations"], [])

    def test_falls_back_when_required_keys_missing(self):
        result = hairstyle._parse_result('{"unexpected": "shape"}')
        self.assertEqual(result["status"], "error")


class AnalyzeHairstyleTest(unittest.TestCase):
    def test_sends_image_and_returns_parsed_result(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': '{"status": "ok", "recommendations": []}'}]}}]
        }
        mock_response.raise_for_status.return_value = None

        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            with patch('hairstyle.requests.post', return_value=mock_response) as mock_post:
                result = hairstyle.analyze_hairstyle(
                    b'fake-bytes', 'image/jpeg', preferences={'maintenance': 'low'}, language='pt'
                )

        self.assertEqual(result, {"status": "ok", "recommendations": []})
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs['timeout'], 30)
        self.assertEqual(kwargs['headers']['x-goog-api-key'], 'test-key')
        image_part = kwargs['json']['contents'][0]['parts'][1]
        self.assertEqual(image_part['inline_data']['mime_type'], 'image/jpeg')
        self.assertEqual(image_part['inline_data']['data'], base64.b64encode(b'fake-bytes').decode('utf-8'))

    def test_raises_when_api_key_missing(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                hairstyle.analyze_hairstyle(b'fake-bytes', 'image/jpeg')

    def test_falls_back_gracefully_when_response_has_no_candidates(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {'promptFeedback': {'blockReason': 'SAFETY'}}
        mock_response.raise_for_status.return_value = None

        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            with patch('hairstyle.requests.post', return_value=mock_response):
                result = hairstyle.analyze_hairstyle(b'fake-bytes', 'image/jpeg')

        self.assertEqual(result, {"status": "error", "recommendations": []})


if __name__ == '__main__':
    unittest.main()
