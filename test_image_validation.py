import unittest

from image_validation import detect_image_mime


class DetectImageMimeTest(unittest.TestCase):
    def test_detects_jpeg_by_magic_bytes(self):
        data = b'\xff\xd8\xff\xe0' + b'\x00' * 20
        self.assertEqual(detect_image_mime(data), 'image/jpeg')

    def test_detects_png_by_magic_bytes(self):
        data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 20
        self.assertEqual(detect_image_mime(data), 'image/png')

    def test_detects_webp_by_magic_bytes(self):
        data = b'RIFF' + b'\x00\x00\x00\x00' + b'WEBP' + b'\x00' * 20
        self.assertEqual(detect_image_mime(data), 'image/webp')

    def test_rejects_renamed_text_file(self):
        data = b'not an image, just text pretending to be a photo.jpg'
        self.assertIsNone(detect_image_mime(data))

    def test_rejects_empty_bytes(self):
        self.assertIsNone(detect_image_mime(b''))

    def test_rejects_truncated_riff_without_webp_marker(self):
        data = b'RIFF' + b'\x00\x00\x00\x00' + b'AVI '
        self.assertIsNone(detect_image_mime(data))


if __name__ == '__main__':
    unittest.main()
