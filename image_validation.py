"""MIME sniffing by magic bytes — never trust a file extension or the
client-supplied Content-Type header for security-relevant decisions."""

_JPEG_MAGIC = b'\xff\xd8\xff'
_PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
_WEBP_RIFF = b'RIFF'
_WEBP_MARKER = b'WEBP'


def detect_image_mime(data):
    if data.startswith(_JPEG_MAGIC):
        return 'image/jpeg'
    if data.startswith(_PNG_MAGIC):
        return 'image/png'
    if len(data) >= 12 and data[:4] == _WEBP_RIFF and data[8:12] == _WEBP_MARKER:
        return 'image/webp'
    return None
