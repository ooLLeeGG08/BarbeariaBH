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
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = '{"status": "ok", "recommendations": []}'
        mock_response = MagicMock()
        mock_response.content = [mock_block]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch.object(hairstyle, '_get_client', return_value=mock_client):
            result = hairstyle.analyze_hairstyle(
                b'fake-bytes', 'image/jpeg', preferences={'maintenance': 'low'}, language='pt'
            )

        self.assertEqual(result, {"status": "ok", "recommendations": []})
        _, kwargs = mock_client.messages.create.call_args
        self.assertEqual(kwargs['model'], hairstyle.MODEL)
        image_block = kwargs['messages'][0]['content'][0]
        self.assertEqual(image_block['type'], 'image')
        self.assertEqual(image_block['source']['media_type'], 'image/jpeg')
        self.assertEqual(image_block['source']['data'], 'ZmFrZS1ieXRlcw==')  # base64 of b'fake-bytes'


if __name__ == '__main__':
    unittest.main()
