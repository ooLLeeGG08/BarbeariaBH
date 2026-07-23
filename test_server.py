# test_server.py
import io
import unittest
from unittest.mock import patch

import server


class StaticFileAllowlistTest(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_serves_index_at_root(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_serves_allowlisted_top_level_files(self):
        for path in ('/style.css', '/app.js'):
            with self.client.get(path) as response:
                self.assertEqual(response.status_code, 200, path)

    def test_blocks_non_allowlisted_top_level_files(self):
        for path in ('/server.py', '/booking.py', '/hairstyle.py', '/config.py',
                     '/requirements.txt', '/.gitignore', '/README.md', '/.env', '/credentials.json'):
            self.assertEqual(self.client.get(path).status_code, 404, path)

    def test_blocks_directory_traversal_out_of_images(self):
        response = self.client.get('/images/../server.py')
        self.assertEqual(response.status_code, 404)

    def test_blocks_files_in_non_allowlisted_directories(self):
        response = self.client.get('/does-not-exist/whatever.txt')
        self.assertEqual(response.status_code, 404)


class ServicesRouteTest(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_returns_configured_services(self):
        response = self.client.get('/api/services')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('services', data)
        self.assertGreater(len(data['services']), 0)
        self.assertIn('name', data['services'][0])
        self.assertIn('price', data['services'][0])


class BookingRouteValidationTest(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_slots_requires_date_param(self):
        response = self.client.get('/api/slots')
        self.assertEqual(response.status_code, 400)

    def test_book_requires_date_time_and_service(self):
        response = self.client.post('/api/book', json={'date': '2026-07-21'})
        self.assertEqual(response.status_code, 400)


class HairstyleRouteValidationTest(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()
        server.hairstyle_limiter._hits.clear()

    def test_requires_a_photo(self):
        response = self.client.post('/api/hairstyle', data={})
        self.assertEqual(response.status_code, 400)

    def test_rejects_file_that_is_not_really_an_image(self):
        response = self.client.post(
            '/api/hairstyle',
            data={'photo': (io.BytesIO(b'not an image'), 'notes.txt')},
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 400)

    def test_accepts_real_jpeg_bytes_and_forwards_to_analyze(self):
        jpeg_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * 32
        with patch.object(server, 'analyze_hairstyle',
                           return_value={'status': 'ok', 'recommendations': []}) as mock_analyze:
            response = self.client.post(
                '/api/hairstyle',
                data={'photo': (io.BytesIO(jpeg_bytes), 'photo.jpg'), 'language': 'en'},
                content_type='multipart/form-data',
            )
        self.assertEqual(response.status_code, 200)
        mock_analyze.assert_called_once()
        _, kwargs = mock_analyze.call_args
        self.assertEqual(kwargs['language'], 'en')

    def test_rate_limits_after_five_requests_per_ip(self):
        jpeg_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * 32
        with patch.object(server, 'analyze_hairstyle', return_value={'status': 'ok', 'recommendations': []}):
            for _ in range(5):
                response = self.client.post(
                    '/api/hairstyle',
                    data={'photo': (io.BytesIO(jpeg_bytes), 'photo.jpg')},
                    content_type='multipart/form-data',
                )
                self.assertEqual(response.status_code, 200)
            blocked = self.client.post(
                '/api/hairstyle',
                data={'photo': (io.BytesIO(jpeg_bytes), 'photo.jpg')},
                content_type='multipart/form-data',
            )
        self.assertEqual(blocked.status_code, 429)


if __name__ == '__main__':
    unittest.main()
