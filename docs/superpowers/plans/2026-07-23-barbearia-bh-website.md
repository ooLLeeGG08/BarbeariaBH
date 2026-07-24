# Barbearia BH Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Barbearia BH marketing site (Porto) — a Flask backend mirroring the kultiv/noble architecture, a single static frontend page with client-side view switching, a booking flow synced to Google Calendar, and the signature "Encontra o Teu Corte" AI hairstyle recommender backed by the Anthropic Messages API.

**Architecture:** Flask app (`server.py`) serves one static `index.html` via an allowlisted static-file route (no template engine, no Jinja — matches kultiv/noble exactly) plus a small JSON API (`/api/slots`, `/api/book`, `/api/hairstyle`, `/api/services`). `booking.py` wraps the Google Calendar API via a service account. `hairstyle.py` wraps the Anthropic Messages API using the official `anthropic` Python SDK (vision input + `output_config.format` for guaranteed JSON). `config.py` holds all business data (services, hours, contact info) so nothing is hardcoded into the HTML. The frontend (`index.html` + `style.css` + `app.js`) is a single-page app: `.page` divs toggled by `goTo()`/`goHome()`, i18n via `data-i18n` attributes swapped by a JS dictionary, exactly like kultiv/noble.

**Tech Stack:** Python 3.14, Flask 3.1.3, gunicorn, `anthropic` SDK (Claude Opus 4.8, vision + structured outputs), google-api-python-client (Calendar), vanilla HTML/CSS/JS frontend, `unittest` for backend tests.

## Global Constraints

- Same Python framework/version and routing/static conventions as kultiv/noble: Flask, no templating, `send_from_directory` + an explicit allowlist for static files, root-level modules (no `src/` layout).
- Mobile-first CSS; single breakpoint at `min-width: 720px` (matches both reference repos).
- Portuguese is the primary language; English is the secondary toggle (matches reference repos' PT/EN pattern). Placeholder copy is marked `TODO` wherever real client content is missing.
- No CSS framework (reference repos use none).
- Secrets (`ANTHROPIC_API_KEY`, `GOOGLE_CREDENTIALS_JSON`, `CALENDAR_ID`) come from environment variables only — never hardcoded, never committed. `.env` and `credentials.json` stay gitignored.
- The AI hairstyle feature uses the Anthropic Messages API via the official `anthropic` Python SDK — never raw `requests` — per this project's tooling rules for Python.
- Model: `claude-opus-4-8`. Vision input via base64 image content blocks. `output_config.format` (`json_schema`) constrains the response to structured JSON; response parsing still defensively strips markdown fences and catches decode failures, per spec.
- Image uploads: hard cap 8 MB (`MAX_CONTENT_LENGTH`), MIME validated by magic bytes (not file extension or `Content-Type` header), held in memory only — no disk writes, no logging of image bytes.
- Rate limit on `/api/hairstyle`: 5 requests/hour per IP, returning 429 with a clear JSON message.
- Timeout on the Anthropic call: 30s, with a distinct, user-facing recovery message per failure mode (timeout / upstream rate limit / API error / connection failure).
- Full keyboard path through consent → upload → results; loading state is descriptive text, not a bare spinner; results announced via a live region; `prefers-reduced-motion` respected.
- Colour tokens (from the approved design review): `--ink:#141414`, `--paper:#FAFAF8`, `--sienna:#96633D`, `--wood:#4A3626`, `--tan:#A08D78`. Display face: Fraunces. Body face: Work Sans. Single full-bleed hero photo carries all photography; every section below is typography/data only (approved correction — no per-section photo strips like kultiv/noble). Persistent booking CTA is a bottom bar (mobile) / pill (desktop) — explicitly not noble's circular treatment. Dotted-circle icon + dotted hairline row divider replaces the reference repos' bare `(01)(02)` numeric markers, since BH's price list is flat, not sequential.

---

## File Structure

```
barbearia-bh-website/
├── server.py              # Flask: static allowlist route + all API routes
├── booking.py             # Google Calendar slot lookup + booking creation
├── hairstyle.py           # Anthropic Messages API call, prompt, defensive JSON parsing
├── config.py              # Services, business hours, contact info (TODO placeholders)
├── image_validation.py    # Magic-byte MIME sniffing (no python-magic dependency)
├── ratelimit.py           # In-memory sliding-window rate limiter
├── index.html             # Single static page: marketing sections + booking flow pages
├── style.css              # :root token block + component styles
├── app.js                 # Page routing, i18n, hairstyle finder, booking flow, reviews
├── images/
│   └── hero.jpg                # Real photo of the shop interior, supplied by the client
├── requirements.txt
├── render.yaml
├── .env.example
├── test_booking.py
├── test_hairstyle.py
├── test_image_validation.py
├── test_ratelimit.py
├── test_server.py
└── README.md
```

---

### Task 1: Project scaffold + `config.py`

**Files:**
- Create: `barbearia-bh-website/config.py`
- Create: `barbearia-bh-website/.gitignore`

**Interfaces:**
- Produces: `config.SERVICES` (list of dicts, keys `id`, `name`, `description`, `price`, `duration_minutes`), `config.BUSINESS_HOURS` (dict keyed by weekday int `0`-`6`, Monday=0; each value is `{"open": "HH:MM", "close": "HH:MM"}` or `None` if closed that day), `config.BUSINESS_INFO` (dict, keys `name`, `address`, `phone`, `instagram`, `whatsapp` — the last three are `None` until the client supplies them). Every downstream task (`booking.py`, `server.py`, `app.js` via `/api/services`) reads from these.

- [ ] **Step 1: Create the project directory and `.gitignore`**

```bash
mkdir -p /Users/test/PycharmProjects/barbearia-bh-website/images
cd /Users/test/PycharmProjects/barbearia-bh-website
git init
```

`.gitignore`:

```
.env
credentials.json
__pycache__/
*.pyc
.venv/
.idea/
.DS_Store
```

- [ ] **Step 2: Write `config.py`**

```python
"""Static content and business data for Barbearia BH, Porto.

TODO: confirm the business name with the client — the reviews and the only
logo asset supplied so far read "Donk / Donk — The Barbearshop", but the
client asked to keep "Barbearia BH" until they confirm tomorrow. Phone,
Instagram, and WhatsApp are still missing and marked TODO below. Service
descriptions and durations are placeholders: the service list itself
(names and prices) was confirmed by the client as "same as noble website
for now", but noble's site only ever had names and prices — no
descriptions or durations — so those two fields are estimates pending
real client input.
"""

SERVICES = [
    {"id": "classic-haircut", "name": "Corte clássico", "description": "", "price": 12, "duration_minutes": 30},
    {"id": "clipper-haircut", "name": "Corte máquina", "description": "", "price": 10, "duration_minutes": 20},
    {"id": "fade-haircut", "name": "Corte degradê", "description": "", "price": 14, "duration_minutes": 30},
    {"id": "haircut-beard", "name": "Corte e barba", "description": "", "price": 20, "duration_minutes": 45},
    {"id": "beard", "name": "Barba", "description": "", "price": 7, "duration_minutes": 15},
    {"id": "premium-beard", "name": "Barba premium", "description": "", "price": 10, "duration_minutes": 20},
]

# Confirmed by the client. Monday=0 ... Sunday=6.
BUSINESS_HOURS = {
    0: {"open": "10:00", "close": "20:00"},  # Monday
    1: {"open": "10:00", "close": "20:00"},  # Tuesday
    2: {"open": "10:00", "close": "20:00"},  # Wednesday
    3: {"open": "10:00", "close": "20:00"},  # Thursday
    4: {"open": "10:00", "close": "20:00"},  # Friday
    5: {"open": "09:00", "close": "20:00"},  # Saturday
    6: None,  # Sunday — closed
}

BUSINESS_INFO = {
    "name": "Barbearia BH",
    "address": "Rua de Costa Cabral 82, 4200-129 Porto, Portugal",
    # TODO: get phone, Instagram, and WhatsApp from the client.
    "phone": None,
    "instagram": None,
    "whatsapp": None,
}
```

- [ ] **Step 3: Verify it imports cleanly**

Run: `cd /Users/test/PycharmProjects/barbearia-bh-website && python3 -c "import config; print(len(config.SERVICES), config.BUSINESS_HOURS[6])"`
Expected: `6 None`

- [ ] **Step 4: Commit**

```bash
git add config.py .gitignore
git commit -m "Add project scaffold and business config"
```

---

### Task 2: `image_validation.py` — magic-byte MIME sniffing

**Files:**
- Create: `barbearia-bh-website/image_validation.py`
- Test: `barbearia-bh-website/test_image_validation.py`

**Interfaces:**
- Produces: `detect_image_mime(data: bytes) -> str | None` — returns `'image/jpeg'`, `'image/png'`, `'image/webp'`, or `None`. Consumed by `server.py`'s `/api/hairstyle` route.

- [ ] **Step 1: Write the failing tests**

```python
# test_image_validation.py
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /Users/test/PycharmProjects/barbearia-bh-website && python3 -m pytest test_image_validation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'image_validation'`

- [ ] **Step 3: Write `image_validation.py`**

```python
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m pytest test_image_validation.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add image_validation.py test_image_validation.py
git commit -m "Add magic-byte image MIME validation"
```

---

### Task 3: `ratelimit.py` — in-memory sliding-window limiter

**Files:**
- Create: `barbearia-bh-website/ratelimit.py`
- Test: `barbearia-bh-website/test_ratelimit.py`

**Interfaces:**
- Produces: `RateLimiter(max_requests: int, window_seconds: int, clock=time.monotonic)` with method `.allow(key: str) -> bool`. Consumed by `server.py` to gate `/api/hairstyle` at 5 requests/hour per client IP.

- [ ] **Step 1: Write the failing tests**

```python
# test_ratelimit.py
import unittest

from ratelimit import RateLimiter


class RateLimiterTest(unittest.TestCase):
    def test_allows_up_to_the_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=3600)
        self.assertTrue(limiter.allow('1.2.3.4'))
        self.assertTrue(limiter.allow('1.2.3.4'))
        self.assertTrue(limiter.allow('1.2.3.4'))

    def test_blocks_after_the_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=3600)
        limiter.allow('1.2.3.4')
        limiter.allow('1.2.3.4')
        self.assertFalse(limiter.allow('1.2.3.4'))

    def test_tracks_keys_independently(self):
        limiter = RateLimiter(max_requests=1, window_seconds=3600)
        self.assertTrue(limiter.allow('1.2.3.4'))
        self.assertTrue(limiter.allow('5.6.7.8'))
        self.assertFalse(limiter.allow('1.2.3.4'))

    def test_old_hits_expire_out_of_the_window(self):
        clock = {'t': 0.0}
        limiter = RateLimiter(max_requests=1, window_seconds=60, clock=lambda: clock['t'])
        self.assertTrue(limiter.allow('1.2.3.4'))
        self.assertFalse(limiter.allow('1.2.3.4'))
        clock['t'] += 61
        self.assertTrue(limiter.allow('1.2.3.4'))


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest test_ratelimit.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ratelimit'`

- [ ] **Step 3: Write `ratelimit.py`**

```python
"""In-memory sliding-window rate limiter, keyed by client identifier.

Single-process only — correct for a single gunicorn worker (the default,
and what render.yaml's startCommand runs). A multi-worker deployment would
need a shared store (e.g. Redis) instead; not needed at this scale.
"""

import threading
import time


class RateLimiter:
    def __init__(self, max_requests, window_seconds, clock=time.monotonic):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._clock = clock
        self._hits = {}
        self._lock = threading.Lock()

    def allow(self, key):
        now = self._clock()
        cutoff = now - self._window_seconds
        with self._lock:
            timestamps = [t for t in self._hits.get(key, []) if t > cutoff]
            if len(timestamps) >= self._max_requests:
                self._hits[key] = timestamps
                return False
            timestamps.append(now)
            self._hits[key] = timestamps
            return True
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m pytest test_ratelimit.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add ratelimit.py test_ratelimit.py
git commit -m "Add in-memory rate limiter for the hairstyle endpoint"
```

---

### Task 4: `booking.py` — Google Calendar slots and booking

**Files:**
- Create: `barbearia-bh-website/booking.py`
- Test: `barbearia-bh-website/test_booking.py`

**Interfaces:**
- Consumes: `config.BUSINESS_HOURS` (dict keyed by weekday int, see Task 1)
- Produces: `booking.TIMEZONE` (str), `booking.CALENDAR_ID` (str), `booking.get_available_slots(date_str: str) -> list[str]`, `booking.create_booking(date_str, time_str, service_type, client_name='') -> str`. Consumed by `server.py`'s `/api/slots` and `/api/book` routes.

- [ ] **Step 1: Write the failing tests**

```python
# test_booking.py
import datetime
import unittest
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import booking


class GetAvailableSlotsTest(unittest.TestCase):
    def test_excludes_slot_already_booked(self):
        """Client booked 15:00 on a weekday. That slot should no longer show as available."""
        tz = ZoneInfo(booking.TIMEZONE)
        busy_start = datetime.datetime(2026, 7, 21, 15, 0, tzinfo=tz)
        busy_end = busy_start + datetime.timedelta(minutes=30)

        with patch.object(booking, '_get_busy_periods', return_value=[(busy_start, busy_end)]):
            slots = booking.get_available_slots('2026-07-21')

        self.assertNotIn('15:00', slots)
        self.assertIn('14:30', slots)
        self.assertIn('15:30', slots)

    def test_parses_zulu_suffixed_busy_periods_from_google_api(self):
        """Google's freebusy API returns 'Z'-suffixed timestamps, which
        datetime.fromisoformat() can't parse on Python < 3.11. Lisbon is
        UTC+1 in July (DST), so 14:00Z is 15:00 local."""
        raw_busy = [{'start': '2026-07-21T14:00:00Z', 'end': '2026-07-21T14:30:00Z'}]
        service = MagicMock()
        service.freebusy.return_value.query.return_value.execute.return_value = {
            'calendars': {booking.CALENDAR_ID: {'busy': raw_busy}}
        }

        with patch.object(booking, '_get_service', return_value=service):
            slots = booking.get_available_slots('2026-07-21')

        self.assertNotIn('15:00', slots)

    def test_no_slot_before_opening_at_ten_on_weekdays(self):
        """Monday-Friday open at 10:00."""
        with patch.object(booking, '_get_busy_periods', return_value=[]):
            slots = booking.get_available_slots('2026-07-21')  # Tuesday

        self.assertNotIn('09:00', slots)
        self.assertNotIn('09:30', slots)
        self.assertIn('10:00', slots)

    def test_last_slot_starts_at_nineteen_thirty_on_weekdays(self):
        """Hours run until 20:00, so the last bookable 30-minute slot
        starts at 19:30 and there is no 20:00 slot."""
        with patch.object(booking, '_get_busy_periods', return_value=[]):
            slots = booking.get_available_slots('2026-07-21')  # Tuesday

        self.assertIn('19:30', slots)
        self.assertNotIn('20:00', slots)

    def test_saturday_opens_an_hour_earlier_at_nine(self):
        """Saturday opens at 09:00 (an hour earlier than weekdays), still closes at 20:00."""
        with patch.object(booking, '_get_busy_periods', return_value=[]):
            slots = booking.get_available_slots('2026-07-25')  # Saturday

        self.assertIn('09:00', slots)
        self.assertNotIn('08:30', slots)
        self.assertIn('19:30', slots)
        self.assertNotIn('20:00', slots)

    def test_closed_on_sunday(self):
        with patch.object(booking, '_get_busy_periods', return_value=[]):
            slots = booking.get_available_slots('2026-07-26')  # Sunday

        self.assertEqual(slots, [])


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest test_booking.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'booking'`

- [ ] **Step 3: Write `booking.py`**

```python
import datetime
import json
import os
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build

import config

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.environ.get('CALENDAR_ID', 'primary')
TIMEZONE = os.environ.get('TIMEZONE', 'Europe/Lisbon')


def _get_service():
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(creds_json), scopes=SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_file(
            'credentials.json', scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)


def _business_hours(date):
    """Returns (open_time, close_time) from config.BUSINESS_HOURS, or None if closed."""
    hours = config.BUSINESS_HOURS.get(date.weekday())
    if hours is None:
        return None
    open_hour, open_minute = map(int, hours['open'].split(':'))
    close_hour, close_minute = map(int, hours['close'].split(':'))
    return (datetime.time(open_hour, open_minute), datetime.time(close_hour, close_minute))


def get_available_slots(date_str):
    date = datetime.date.fromisoformat(date_str)
    tz = ZoneInfo(TIMEZONE)

    hours = _business_hours(date)
    if hours is None:
        return []

    open_time, close_time = hours
    day_start = datetime.datetime.combine(date, open_time, tzinfo=tz)
    day_end = datetime.datetime.combine(date, close_time, tzinfo=tz)

    busy_periods = _get_busy_periods(day_start, day_end)

    slots = []
    current = day_start
    while current < day_end:
        slot_end = current + datetime.timedelta(minutes=30)
        if not _overlaps_busy(current, slot_end, busy_periods):
            slots.append(current.strftime('%H:%M'))
        current = slot_end
    return slots


def _get_busy_periods(day_start, day_end):
    service = _get_service()
    body = {
        'timeMin': day_start.isoformat(),
        'timeMax': day_end.isoformat(),
        'items': [{'id': CALENDAR_ID}],
    }
    result = service.freebusy().query(body=body).execute()
    busy = result['calendars'][CALENDAR_ID]['busy']
    return [
        (_parse_rfc3339(period['start']), _parse_rfc3339(period['end']))
        for period in busy
    ]


def _parse_rfc3339(value):
    # datetime.fromisoformat() only accepts 'Z' as a UTC suffix from Python 3.11+;
    # Google's API returns 'Z'-suffixed timestamps regardless of Python version.
    return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))


def _overlaps_busy(start, end, busy_periods):
    return any(start < busy_end and end > busy_start for busy_start, busy_end in busy_periods)


def create_booking(date_str, time_str, service_type, client_name=''):
    service = _get_service()

    tz = ZoneInfo(TIMEZONE)
    date = datetime.date.fromisoformat(date_str)
    hour, minute = map(int, time_str.split(':'))
    start = datetime.datetime(date.year, date.month, date.day, hour, minute, tzinfo=tz)
    end = start + datetime.timedelta(minutes=30)

    summary = f"{service_type} — {client_name}" if client_name else service_type

    event = {
        'summary': summary,
        'start': {'dateTime': start.isoformat(), 'timeZone': TIMEZONE},
        'end':   {'dateTime': end.isoformat(),   'timeZone': TIMEZONE},
    }

    result = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return result.get('id')
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m pytest test_booking.py -v`
Expected: PASS (6 tests) — note this needs `google-auth`, `google-auth-httplib2`, and `google-api-python-client` installed; install them now if not already available: `pip install google-auth google-auth-httplib2 google-api-python-client`

- [ ] **Step 5: Commit**

```bash
git add booking.py test_booking.py
git commit -m "Add Google Calendar booking module"
```

---

### Task 5: `hairstyle.py` — Anthropic Messages API integration

**Files:**
- Create: `barbearia-bh-website/hairstyle.py`
- Test: `barbearia-bh-website/test_hairstyle.py`

**Interfaces:**
- Produces: `hairstyle.MODEL` (str, `"claude-opus-4-8"`), `hairstyle._parse_result(text: str) -> dict`, `hairstyle._get_client() -> anthropic.Anthropic`, `hairstyle.analyze_hairstyle(image_bytes: bytes, mime_type: str, preferences: dict | None = None, language: str = "pt") -> dict` returning `{"status": "ok" | "no_face" | "multiple_faces" | "error", "recommendations": [{"style_name", "why", "upkeep", "closest_service"}]}`. Consumed by `server.py`'s `/api/hairstyle` route.

- [ ] **Step 1: Install the Anthropic SDK**

```bash
pip install anthropic==0.118.0
```

- [ ] **Step 2: Write the failing tests**

```python
# test_hairstyle.py
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
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python3 -m pytest test_hairstyle.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hairstyle'`

- [ ] **Step 4: Write `hairstyle.py`**

```python
import base64
import json

import anthropic

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """You are a hairstyle consultant helping a barbershop client find a new haircut.

Analyse the uploaded photo strictly for: face shape, hair type and texture, and visible hair growth pattern. Recommend haircuts based only on those factors.

You must not comment on attractiveness, age, weight, ethnicity, or anything unrelated to hair and styling. You must not attempt to identify who the person is.

If the image contains no clearly visible face, respond with status "no_face" and an empty recommendations list.
If the image contains more than one person, respond with status "multiple_faces" and an empty recommendations list.
Otherwise respond with status "ok" and 2 to 3 recommendations.

Respond only via the structured output schema. No prose, no markdown."""

RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "no_face", "multiple_faces"]},
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "style_name": {"type": "string"},
                    "why": {"type": "string"},
                    "upkeep": {"type": "string"},
                    "closest_service": {"type": "string"},
                },
                "required": ["style_name", "why", "upkeep", "closest_service"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["status", "recommendations"],
    "additionalProperties": False,
}

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(timeout=30.0)
    return _client


def _build_user_text(preferences, language):
    instruction = "Respond in Portuguese." if language == "pt" else "Respond in English."
    parts = [instruction]
    if preferences:
        if preferences.get("maintenance"):
            parts.append(f"Preferred maintenance level: {preferences['maintenance']}.")
        if preferences.get("beard"):
            parts.append(f"Beard preference: {preferences['beard']}.")
        if preferences.get("length_goal"):
            parts.append(f"Hair length goal: {preferences['length_goal']}.")
    return " ".join(parts)


def analyze_hairstyle(image_bytes, mime_type, preferences=None, language="pt"):
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": RECOMMENDATION_SCHEMA}},
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": mime_type, "data": image_b64},
                },
                {"type": "text", "text": _build_user_text(preferences, language)},
            ],
        }],
    )

    text = next(block.text for block in response.content if block.type == "text")
    return _parse_result(text)


def _parse_result(text):
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.strip()
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return {"status": "error", "recommendations": []}
    if not isinstance(data, dict) or "status" not in data or "recommendations" not in data:
        return {"status": "error", "recommendations": []}
    return data
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python3 -m pytest test_hairstyle.py -v`
Expected: PASS (5 tests) — no `ANTHROPIC_API_KEY` needed, since `_get_client` is patched out and never actually constructs a real client.

- [ ] **Step 6: Commit**

```bash
git add hairstyle.py test_hairstyle.py
git commit -m "Add Anthropic-backed hairstyle recommendation module"
```

---

### Task 6: `server.py` — Flask routes, static allowlist, rate limiting

**Files:**
- Create: `barbearia-bh-website/server.py`
- Test: `barbearia-bh-website/test_server.py`

**Interfaces:**
- Consumes: `config.SERVICES`, `booking.get_available_slots`, `booking.create_booking`, `hairstyle.analyze_hairstyle`, `image_validation.detect_image_mime`, `ratelimit.RateLimiter`.
- Produces: `server.app` (Flask app, importable by gunicorn as `server:app`), `server.hairstyle_limiter` (RateLimiter instance, used directly by tests to reset state between test cases).

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest test_server.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'server'`

- [ ] **Step 3: Create a placeholder `index.html`, `style.css`, `app.js` so the static-file tests can pass**

(These are replaced with real content in Tasks 7–9. For now, minimal stand-ins so `test_server.py` can run.)

```bash
cd /Users/test/PycharmProjects/barbearia-bh-website
echo '<!doctype html><title>Barbearia BH</title>' > index.html
echo '/* placeholder */' > style.css
echo '// placeholder' > app.js
```

- [ ] **Step 4: Write `server.py`**

```python
from flask import Flask, request, jsonify, send_from_directory
import os
import traceback
from dotenv import load_dotenv
load_dotenv()

import anthropic

import config
from booking import get_available_slots, create_booking
from hairstyle import analyze_hairstyle
from image_validation import detect_image_mime
from ratelimit import RateLimiter

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024

ALLOWED_STATIC_FILES = {'style.css', 'app.js'}
ALLOWED_STATIC_DIRS = {'images'}

hairstyle_limiter = RateLimiter(max_requests=5, window_seconds=3600)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html', max_age=0)


@app.route('/<path:filename>')
def static_files(filename):
    if filename in ALLOWED_STATIC_FILES:
        return send_from_directory('.', filename, max_age=0)

    parts = filename.split('/')
    if len(parts) == 2 and parts[0] in ALLOWED_STATIC_DIRS:
        return send_from_directory(parts[0], parts[1], max_age=0)

    return jsonify({'error': 'Not found'}), 404


@app.route('/api/services', methods=['GET'])
def services():
    return jsonify({'services': config.SERVICES})


@app.route('/api/slots', methods=['GET'])
def slots():
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'date parameter required'}), 400
    try:
        available = get_available_slots(date)
        return jsonify({'slots': available})
    except Exception as e:
        print(f"Slots error: {e}")
        return jsonify({'error': 'Could not load available slots'}), 500


@app.route('/api/book', methods=['POST'])
def book():
    try:
        data = request.get_json()
        date = data.get('date')
        time = data.get('time')
        service = data.get('service')
        name = data.get('name', '')

        if not all([date, time, service]):
            return jsonify({'error': 'date, time and service are required'}), 400

        event_id = create_booking(date, time, service, name)
        return jsonify({'status': 'success', 'event_id': event_id})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Could not complete booking'}), 500


@app.route('/api/hairstyle', methods=['POST'])
def hairstyle():
    client_ip = request.remote_addr
    if not hairstyle_limiter.allow(client_ip):
        return jsonify({
            'error': 'rate_limited',
            'message': 'Demasiados pedidos. Tenta novamente dentro de uma hora.',
        }), 429

    if 'photo' not in request.files:
        return jsonify({'error': 'No photo uploaded'}), 400

    file = request.files['photo']
    image_bytes = file.read()

    mime_type = detect_image_mime(image_bytes)
    if mime_type is None:
        return jsonify({'error': 'File must be a JPEG, PNG, or WebP image'}), 400

    language = request.form.get('language', 'pt')
    preferences = {
        'maintenance': request.form.get('maintenance'),
        'beard': request.form.get('beard'),
        'length_goal': request.form.get('length_goal'),
    }

    try:
        result = analyze_hairstyle(image_bytes, mime_type, preferences=preferences, language=language)
        return jsonify({'status': 'success', 'analysis': result})
    except anthropic.APITimeoutError:
        return jsonify({'error': 'timeout', 'message': 'A análise demorou demasiado tempo.'}), 504
    except anthropic.RateLimitError:
        return jsonify({
            'error': 'upstream_rate_limited',
            'message': 'Serviço de análise sobrecarregado. Tenta novamente.',
        }), 503
    except anthropic.APIStatusError as e:
        print(f"Hairstyle API error: {e}")
        return jsonify({'error': 'analysis_failed', 'message': 'Não foi possível analisar a foto.'}), 502
    except anthropic.APIConnectionError:
        return jsonify({
            'error': 'connection_failed',
            'message': 'Falha de ligação ao serviço de análise.',
        }), 502


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'Photo exceeds 8 MB limit'}), 413


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python3 -m pytest test_server.py -v`
Expected: PASS (10 tests) — install `flask`, `flask-cors` (unused but harmless to skip), `python-dotenv` if not already present: `pip install Flask python-dotenv`

- [ ] **Step 6: Commit**

```bash
git add server.py test_server.py index.html style.css app.js
git commit -m "Add Flask server with static allowlist and API routes"
```

---

### Task 7: `index.html` — full markup

**Files:**
- Modify: `barbearia-bh-website/index.html` (replace placeholder from Task 6)

- [ ] **Step 1: Write the full `index.html`**

```html
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Barbearia BH — Porto</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Work+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="style.css">
</head>
<body>

<div class="lang-toggle" role="group" aria-label="Idioma">
    <button type="button" class="lang-option" data-lang="pt" onclick="setLanguage('pt')">PT</button>
    <button type="button" class="lang-option" data-lang="en" onclick="setLanguage('en')">EN</button>
</div>

<header class="topbar">
    <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="nav-overlay" onclick="toggleNav()">
        <span class="nav-toggle-bars" aria-hidden="true"></span>
        <span class="sr-only" data-i18n="menu">Menu</span>
    </button>
</header>

<nav id="nav-overlay" class="nav-overlay" hidden>
    <button type="button" class="nav-close" onclick="toggleNav()" data-i18n-aria-label="closeMenu" aria-label="Fechar menu">✕</button>
    <ul class="nav-links">
        <li><a href="#hero" onclick="closeNavTo('hero')" data-i18n="navHome">Início</a></li>
        <li><a href="#services" onclick="closeNavTo('services')" data-i18n="navServices">Serviços</a></li>
        <li><a href="#hairstyle-finder" onclick="closeNavTo('hairstyle-finder')" data-i18n="navHairstyle">Encontra o Teu Corte</a></li>
        <li><a href="#reviews" onclick="closeNavTo('reviews')" data-i18n="navReviews">Avaliações</a></li>
        <li><a href="#location" onclick="closeNavTo('location')" data-i18n="navLocation">Onde Estamos</a></li>
        <li><button type="button" class="nav-book-btn" onclick="closeNavAndBook()" data-i18n="navBook">Marcar</button></li>
    </ul>
</nav>

<button type="button" class="booking-cta" onclick="goTo('page-service')" data-i18n-aria-label="bookOnline" aria-label="Marcar online">
    <span data-i18n="floatingBook">Marcar</span>
</button>

<main id="page-home" class="page active">

    <section id="hero" class="hero">
        <img class="hero-photo" src="images/hero.jpg" alt="Interior da Barbearia BH, Porto" loading="eager">
        <div class="hero-mark">
            <p class="hero-wordmark">Barbearia BH</p>
            <p class="hero-tagline" data-i18n="heroTagline">Cortes · Barba · Estilo — Porto</p>
        </div>
    </section>

    <section id="services" class="section section--paper">
        <h2 data-i18n="servicesTitle">Serviços</h2>
        <div class="section-divider" aria-hidden="true"></div>
        <ul id="service-list" class="service-list">
            <li class="service-row-loading" data-i18n="loadingServices">A carregar serviços...</li>
        </ul>
    </section>

    <section id="hairstyle-finder" class="section section--ink hairstyle-section">
        <h2 data-i18n="findStyleTitle">Encontra o Teu Corte</h2>
        <div class="section-divider" aria-hidden="true"></div>

        <div class="hairstyle-card">

            <div id="hairstyle-consent-view" class="hairstyle-view">
                <p class="consent-text" data-i18n="consentText">
                    A tua foto é enviada a um modelo de terceiros para análise, não é guardada no
                    nosso servidor e é descartada assim que recebemos a resposta.
                </p>
                <button type="button" class="next-btn" onclick="acceptConsent()" data-i18n="consentAccept">
                    Aceito, continuar
                </button>
            </div>

            <div id="hairstyle-upload-view" class="hairstyle-view hidden">
                <p class="upload-subtitle" data-i18n="uploadSubtitle">Carrega uma foto nítida do teu rosto.</p>
                <label class="upload-zone">
                    <input type="file" id="photoInput" accept="image/jpeg,image/png,image/webp" capture="environment" onchange="photoSelected(event)">
                    <div id="uploadPlaceholder" class="upload-placeholder">
                        <span class="upload-icon" aria-hidden="true">📷</span>
                        <p data-i18n="tapToUpload">Toca para carregar uma foto</p>
                        <small data-i18n="uploadHint">JPG, PNG ou WebP · Máx. 8 MB</small>
                    </div>
                    <img id="photoPreview" class="photo-preview hidden" alt="">
                </label>

                <div class="preference-fields">
                    <div class="preference-field">
                        <label for="maintenanceInput" data-i18n="maintenanceLabel">Manutenção</label>
                        <select id="maintenanceInput">
                            <option value="" data-i18n="preferNoAnswer">Sem preferência</option>
                            <option value="low" data-i18n="maintenanceLow">Baixa</option>
                            <option value="medium" data-i18n="maintenanceMedium">Média</option>
                            <option value="high" data-i18n="maintenanceHigh">Alta</option>
                        </select>
                    </div>
                    <div class="preference-field">
                        <label for="beardInput" data-i18n="beardLabel">Barba</label>
                        <select id="beardInput">
                            <option value="" data-i18n="preferNoAnswer">Sem preferência</option>
                            <option value="yes" data-i18n="beardYes">Sim</option>
                            <option value="no" data-i18n="beardNo">Não</option>
                            <option value="trimmed" data-i18n="beardTrimmed">Aparada</option>
                        </select>
                    </div>
                    <div class="preference-field">
                        <label for="lengthInput" data-i18n="lengthLabel">Comprimento</label>
                        <select id="lengthInput">
                            <option value="" data-i18n="preferNoAnswer">Sem preferência</option>
                            <option value="shorter" data-i18n="lengthShorter">Mais curto</option>
                            <option value="similar" data-i18n="lengthSimilar">Semelhante</option>
                            <option value="longer" data-i18n="lengthLonger">Mais comprido</option>
                        </select>
                    </div>
                </div>

                <button id="analyseBtn" class="next-btn" onclick="analysePhoto()" disabled data-i18n="analyseBtn">
                    Analisar Foto
                </button>
            </div>

            <div id="hairstyle-loading-view" class="hairstyle-view hidden">
                <p class="loading" role="status" aria-live="polite" data-i18n="analysingPhoto">
                    A analisar a tua foto — isto pode demorar alguns segundos...
                </p>
            </div>

            <div id="hairstyle-results-view" class="hairstyle-view hidden">
                <h3 data-i18n="hairstyleReport">O Teu Relatório de Estilo</h3>
                <div id="resultsContent" class="results-content" role="status" aria-live="polite"></div>
                <button type="button" class="try-again-link" onclick="resetHairstyleFinder()" data-i18n="tryAnotherPhoto">
                    Analisar outra foto
                </button>
            </div>

            <div id="hairstyle-error-view" class="hairstyle-view hidden">
                <p id="hairstyleErrorText" class="error-text" role="status" aria-live="assertive"></p>
                <button type="button" class="next-btn" onclick="resetHairstyleFinder()" data-i18n="tryAgain">
                    Tentar novamente
                </button>
                <button type="button" class="try-again-link" onclick="closeNavTo('services')" data-i18n="seeServicesInstead">
                    Ver lista de serviços
                </button>
            </div>

        </div>
    </section>

    <section id="reviews" class="section section--paper">
        <h2 data-i18n="reviewsTitle">Avaliações</h2>
        <div class="section-divider" aria-hidden="true"></div>
        <div class="review-carousel">
            <div id="review-0" class="client-review-card active">
                <div class="stars" aria-hidden="true">★★★★★</div>
                <p class="review-text">I really enjoyed having my hair cut at Barbershop Donk. It's fairly-priced and the barbers know what they are doing. Even though it was my first visit to this particular shop, I felt comfortable and trusted them to do a good job, and they did!</p>
                <p class="review-author">James Briscoe</p>
            </div>
            <div id="review-1" class="client-review-card">
                <div class="stars" aria-hidden="true">★★★★★</div>
                <p class="review-text">I'm a tourist visiting from New York and had a great experience at this barbershop. The barber gave me an excellent cut and was very friendly and professional. Communication was easy since he speaks both Portuguese and English, which I really appreciated.</p>
                <p class="review-author">E.</p>
            </div>
            <div id="review-2" class="client-review-card">
                <div class="stars" aria-hidden="true">★★★★★</div>
                <p class="review-text">The best barbershop in Marquês and one of the best in the whole city! 👌 Thank you so much, Paulo and Danila, for the excellent service and friendliness as always.</p>
                <p class="review-author">Matheus Troche</p>
            </div>
            <!-- NOTE: these quotes name "Barbershop Donk" / barbers Paulo and Danila — real
                 customer testimonials, kept verbatim. Revisit once the client confirms whether
                 the site's public name is "Barbearia BH" or "Donk". -->
            <div class="review-nav">
                <button type="button" class="review-nav-btn" onclick="changeReview(-1)" data-i18n-aria-label="prevReview" aria-label="Avaliação anterior">←</button>
                <button type="button" class="review-nav-btn" onclick="changeReview(1)" data-i18n-aria-label="nextReview" aria-label="Avaliação seguinte">→</button>
            </div>
        </div>
    </section>

    <section id="location" class="section section--ink">
        <h2 data-i18n="locationTitle">Onde Estamos</h2>
        <div class="section-divider" aria-hidden="true"></div>
        <div class="location-details">
            <div class="contact-block">
                <span class="contact-label" data-i18n="addressLabel">Morada</span>
                <a class="contact-value contact-value--link" id="addressLink"
                   href="https://www.google.com/maps?q=Rua+de+Costa+Cabral+82,+4200-129+Porto,+Portugal"
                   target="_blank" rel="noopener">Rua de Costa Cabral 82, 4200-129 Porto</a>
            </div>
            <div class="contact-block">
                <span class="contact-label" data-i18n="phoneLabel">Telefone</span>
                <a class="contact-value contact-value--link" id="phoneLink" href="#">TODO telefone</a>
            </div>
            <div class="contact-block">
                <span class="contact-label" data-i18n="hoursLabel">Horário</span>
                <span class="contact-value" data-i18n="hoursLine">Segunda–Sexta, 10h–20h · Sábado, 9h–20h · Encerrado ao domingo</span>
            </div>
            <div class="location-links">
                <a id="instagramLink" href="#" target="_blank" rel="noopener">Instagram (TODO)</a>
                <a id="whatsappLink" href="#" target="_blank" rel="noopener">WhatsApp (TODO)</a>
            </div>
        </div>
    </section>

    <footer class="site-footer">
        <p class="footer-wordmark">Barbearia BH</p>
        <p class="footer-copy">© 2026 Barbearia BH — <span data-i18n="footerRights">Todos os direitos reservados.</span></p>
    </footer>
</main>

<div id="page-service" class="page">
    <div class="page-card">
        <button type="button" class="back-btn" onclick="goHome()" data-i18n="back">← Voltar</button>
        <p class="progress" data-i18n="progressStep1">Passo 1 de 4</p>
        <h2 data-i18n="chooseService">Escolher um Serviço</h2>
        <div id="service-grid" class="service-grid">
            <p data-i18n="loadingServices">A carregar serviços...</p>
        </div>
    </div>
</div>

<div id="page-date" class="page">
    <div class="page-card">
        <button type="button" class="back-btn" onclick="goTo('page-service')" data-i18n="back">← Voltar</button>
        <p class="progress" data-i18n="progressStep2">Passo 2 de 4</p>
        <h2 data-i18n="pickDate">Escolher uma Data</h2>
        <div class="date-picker-wrapper">
            <input type="date" id="dateInput" class="date-input" onchange="dateSelected(this.value)">
        </div>
        <button id="dateNextBtn" class="next-btn" onclick="goToTime()" disabled data-i18n="next">Seguinte →</button>
    </div>
</div>

<div id="page-time" class="page">
    <div class="page-card">
        <button type="button" class="back-btn" onclick="goTo('page-date')" data-i18n="back">← Voltar</button>
        <p class="progress" data-i18n="progressStep3">Passo 3 de 4</p>
        <h2 data-i18n="pickTime">Escolher uma Hora</h2>
        <div id="slotsContainer" class="slots-grid">
            <div class="loading" data-i18n="loadingSlots">A carregar horários disponíveis...</div>
        </div>
    </div>
</div>

<div id="page-review" class="page">
    <div class="page-card">
        <button type="button" class="back-btn" onclick="goTo('page-time')" data-i18n="back">← Voltar</button>
        <p class="progress" data-i18n="progressStep4">Passo 4 de 4</p>
        <h2 data-i18n="reviewConfirm">Rever e Confirmar</h2>
        <div class="review-card">
            <div class="review-row">
                <span class="review-label" data-i18n="labelService">Serviço</span>
                <span class="review-value" id="review-service"></span>
            </div>
            <div class="review-row">
                <span class="review-label" data-i18n="labelDate">Data</span>
                <span class="review-value" id="review-date"></span>
            </div>
            <div class="review-row">
                <span class="review-label" data-i18n="labelTime">Hora</span>
                <span class="review-value" id="review-time"></span>
            </div>
            <div class="review-row">
                <span class="review-label" data-i18n="labelPrice">Preço</span>
                <span class="review-value" id="review-price"></span>
            </div>
        </div>
        <div class="name-field">
            <label for="nameInput"><span data-i18n="yourName">O teu nome</span> <span class="optional" data-i18n="optional">(opcional)</span></label>
            <input type="text" id="nameInput" class="name-input" placeholder="ex.: João Silva" data-i18n-placeholder="namePlaceholder">
        </div>
        <div class="review-actions">
            <button type="button" class="change-btn" onclick="goTo('page-service')" data-i18n="change">Alterar</button>
            <button id="confirmBtn" type="button" class="confirm-btn" onclick="confirmBooking()" data-i18n="confirm">Confirmar</button>
        </div>
    </div>
</div>

<div id="page-confirmed" class="page">
    <div class="page-card centered">
        <div class="success-icon" aria-hidden="true">✅</div>
        <h2 data-i18n="youreBooked">Está marcado!</h2>
        <p class="confirm-text">
            <strong id="confirm-service"></strong><br>
            <span id="confirm-date"></span> <span data-i18n="at">às</span> <span id="confirm-time"></span>
        </p>
        <button type="button" class="next-btn" onclick="goHome()" data-i18n="backToHome">Voltar ao Início</button>
    </div>
</div>

<script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Verify the static route still serves it**

Run: `python3 -m pytest test_server.py::StaticFileAllowlistTest -v`
Expected: PASS (still 5 tests) — the markup change doesn't affect the allowlist logic

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Write full site markup"
```

---

### Task 8: `style.css` — design tokens and component styles

**Files:**
- Modify: `barbearia-bh-website/style.css` (replace placeholder)

- [ ] **Step 1: Write the full `style.css`**

```css
:root {
    --ink:    #141414;
    --paper:  #FAFAF8;
    --sienna: #96633D;
    --wood:   #4A3626;
    --tan:    #A08D78;
    --white:  #fff;

    --font-display: 'Fraunces', serif;
    --font-body: 'Work Sans', sans-serif;

    --container-max: 640px;
    --section-pad-y: clamp(48px, 10vw, 96px);
    --section-pad-x: clamp(20px, 6vw, 48px);
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

@media (prefers-reduced-motion: reduce) {
    html {
        scroll-behavior: auto;
    }
    *, *::before, *::after {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.001ms !important;
    }
}

body {
    margin: 0;
    font-family: var(--font-body);
    color: var(--ink);
    background: var(--paper);
    -webkit-font-smoothing: antialiased;
}

h1, h2, h3 {
    font-family: var(--font-display);
    font-weight: 600;
    letter-spacing: -0.01em;
    margin: 0 0 0.4em;
}

h2 {
    font-size: clamp(1.6rem, 4vw, 2.2rem);
    text-align: center;
}

a {
    color: inherit;
}

button {
    font-family: var(--font-body);
    cursor: pointer;
}

:focus-visible {
    outline: 3px solid var(--sienna);
    outline-offset: 2px;
}

.hidden {
    display: none !important;
}

.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0,0,0,0);
    white-space: nowrap;
    border: 0;
}

/* ===== LANGUAGE TOGGLE ===== */
.lang-toggle {
    position: fixed;
    top: 12px;
    right: 12px;
    z-index: 60;
    display: flex;
    gap: 2px;
    background: rgba(20, 20, 20, 0.55);
    border-radius: 999px;
    padding: 4px;
}

.lang-option {
    border: none;
    background: transparent;
    color: var(--white);
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
}

.lang-option[aria-current="true"] {
    background: var(--sienna);
}

/* ===== TOP BAR / HAMBURGER ===== */
.topbar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 60;
    padding: 12px;
}

.nav-toggle {
    width: 44px;
    height: 44px;
    border: none;
    background: rgba(20, 20, 20, 0.55);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.nav-toggle-bars,
.nav-toggle-bars::before,
.nav-toggle-bars::after {
    content: '';
    display: block;
    width: 18px;
    height: 2px;
    background: var(--white);
}

.nav-toggle-bars::before { transform: translateY(-5px); }
.nav-toggle-bars::after { transform: translateY(3px); }

.nav-overlay {
    position: fixed;
    inset: 0;
    z-index: 70;
    background: var(--ink);
    color: var(--paper);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2rem;
}

.nav-close {
    position: absolute;
    top: 12px;
    right: 12px;
    width: 44px;
    height: 44px;
    border: none;
    background: transparent;
    color: var(--paper);
    font-size: 1.4rem;
}

.nav-links {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 1.4rem;
    text-align: center;
}

.nav-links a,
.nav-book-btn {
    font-family: var(--font-display);
    font-size: 1.4rem;
    text-decoration: none;
    color: var(--paper);
    background: none;
    border: none;
}

.nav-book-btn {
    color: var(--sienna);
    font-weight: 600;
}

/* ===== PERSISTENT BOOKING CTA ===== */
.booking-cta {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 50;
    width: 100%;
    padding: 16px;
    border: none;
    background: var(--ink);
    color: var(--paper);
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    border-top: 2px solid var(--sienna);
}

/* ===== PAGES ===== */
.page {
    display: none;
}

.page.active {
    display: block;
}

/* ===== HERO ===== */
.hero {
    position: relative;
    width: 100%;
    height: 100vh;
    min-height: 480px;
    overflow: hidden;
}

.hero-photo {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.hero-mark {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    background: linear-gradient(to bottom, rgba(20,20,20,0) 55%, rgba(20,20,20,0.55) 100%);
    color: var(--white);
    padding: 0 20px 90px;
}

.hero-wordmark {
    font-family: var(--font-display);
    font-size: clamp(2.2rem, 9vw, 3.6rem);
    margin: 0;
    letter-spacing: 0.02em;
}

.hero-tagline {
    margin: 0.6em 0 0;
    font-size: 1rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ===== SECTIONS ===== */
.section {
    padding: var(--section-pad-y) var(--section-pad-x) calc(var(--section-pad-y) + 70px);
    max-width: var(--container-max);
    margin: 0 auto;
}

.section--paper {
    background: var(--paper);
    color: var(--ink);
}

.section--ink {
    background: var(--ink);
    color: var(--paper);
    max-width: none;
}

.section--ink > * {
    max-width: var(--container-max);
    margin-left: auto;
    margin-right: auto;
}

.section-divider {
    width: 48px;
    height: 2px;
    background: var(--sienna);
    margin: 0 auto 2.4rem;
}

/* ===== SERVICES ===== */
.service-list {
    list-style: none;
    margin: 0;
    padding: 0;
}

.service-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 0;
    border-bottom: 1px dotted var(--tan);
}

.service-row-icon {
    flex: none;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    border: 1px dotted var(--sienna);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
}

.service-row-body {
    flex: 1;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 8px;
    flex-wrap: wrap;
}

.service-row-name {
    font-weight: 600;
}

.service-row-desc {
    display: block;
    font-size: 0.85rem;
    opacity: 0.7;
    margin-top: 2px;
}

.service-row-price {
    color: var(--sienna);
    font-weight: 600;
    white-space: nowrap;
}

.service-row-loading {
    text-align: center;
    opacity: 0.6;
    padding: 20px 0;
}

/* ===== HAIRSTYLE FINDER ===== */
.hairstyle-card {
    max-width: 460px;
    margin: 0 auto;
    text-align: center;
}

.hairstyle-view h3 {
    color: var(--paper);
}

.consent-text {
    line-height: 1.6;
    margin-bottom: 1.6rem;
}

.upload-subtitle {
    margin-bottom: 1.2rem;
}

.upload-zone {
    display: block;
    border: 1px dashed var(--tan);
    border-radius: 4px;
    padding: 2rem 1rem;
    cursor: pointer;
    margin-bottom: 1.2rem;
    position: relative;
}

.upload-zone input {
    position: absolute;
    width: 1px;
    height: 1px;
    opacity: 0;
}

.upload-icon {
    font-size: 2rem;
    display: block;
    margin-bottom: 0.4rem;
}

.photo-preview {
    max-width: 100%;
    max-height: 240px;
    border-radius: 4px;
}

.preference-fields {
    display: grid;
    gap: 0.8rem;
    margin-bottom: 1.4rem;
    text-align: left;
}

.preference-field label {
    display: block;
    font-size: 0.8rem;
    margin-bottom: 0.2rem;
    opacity: 0.8;
}

.preference-field select {
    width: 100%;
    padding: 10px;
    background: var(--paper);
    color: var(--ink);
    border: 1px solid var(--tan);
    border-radius: 4px;
}

.next-btn, .confirm-btn {
    display: inline-block;
    width: 100%;
    padding: 14px;
    background: var(--sienna);
    color: var(--white);
    border: none;
    border-radius: 4px;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.next-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.try-again-link {
    display: inline-block;
    margin-top: 1rem;
    background: none;
    border: none;
    color: var(--tan);
    text-decoration: underline;
}

.loading {
    padding: 2rem 0;
}

.results-content {
    text-align: left;
}

.result-card {
    border: 1px dotted var(--tan);
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.result-card h4 {
    font-family: var(--font-display);
    margin: 0 0 0.4rem;
    color: var(--sienna);
}

.result-card p {
    margin: 0.3rem 0;
    font-size: 0.9rem;
}

.result-card a {
    display: inline-block;
    margin-top: 0.6rem;
    color: var(--sienna);
    font-weight: 600;
}

.error-text {
    line-height: 1.6;
    margin-bottom: 1rem;
}

/* ===== REVIEWS ===== */
.review-carousel {
    max-width: 480px;
    margin: 0 auto;
    text-align: center;
}

.client-review-card {
    display: none;
}

.client-review-card.active {
    display: block;
}

.stars {
    color: var(--sienna);
    letter-spacing: 2px;
    margin-bottom: 0.6rem;
}

.review-text {
    font-style: italic;
    line-height: 1.6;
}

.review-author {
    margin-top: 0.8rem;
    font-weight: 600;
}

.review-nav {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-top: 1.4rem;
}

.review-nav-btn {
    border: 1px solid var(--tan);
    background: none;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    color: var(--ink);
}

/* ===== LOCATION ===== */
.location-details {
    display: grid;
    gap: 1rem;
}

.contact-block {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px dotted var(--tan);
}

.contact-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    opacity: 0.7;
}

.contact-value--link {
    text-decoration: underline;
}

.location-links {
    display: flex;
    gap: 1.4rem;
    margin-top: 0.6rem;
}

.location-links a {
    color: var(--sienna);
    font-weight: 600;
    text-decoration: none;
}

/* ===== FOOTER ===== */
.site-footer {
    text-align: center;
    padding: 2rem var(--section-pad-x) 6rem;
    background: var(--ink);
    color: var(--paper);
}

.footer-wordmark {
    font-family: var(--font-display);
    font-size: 1.3rem;
}

.footer-copy {
    font-size: 0.75rem;
    opacity: 0.7;
}

/* ===== BOOKING FLOW PAGES ===== */
.page-card {
    max-width: var(--container-max);
    margin: 0 auto;
    padding: 80px var(--section-pad-x) 100px;
}

.page-card.centered {
    text-align: center;
}

.back-btn {
    background: none;
    border: none;
    color: var(--sienna);
    font-weight: 600;
    padding: 0;
    margin-bottom: 1.2rem;
}

.progress {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    opacity: 0.6;
    margin-bottom: 0.4rem;
}

.service-grid {
    display: grid;
    gap: 0.8rem;
    margin: 1.4rem 0;
}

.service-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border: 1px solid var(--tan);
    border-radius: 4px;
    background: var(--paper);
    text-align: left;
}

.date-input, .name-input {
    width: 100%;
    padding: 12px;
    border: 1px solid var(--tan);
    border-radius: 4px;
    margin-bottom: 1.2rem;
    font-family: var(--font-body);
}

.slots-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.6rem;
    margin: 1.2rem 0;
}

.slot-btn {
    padding: 12px 0;
    border: 1px solid var(--tan);
    background: var(--paper);
    border-radius: 4px;
}

.slot-btn[aria-pressed="true"] {
    background: var(--sienna);
    color: var(--white);
    border-color: var(--sienna);
}

.review-card {
    border: 1px solid var(--tan);
    border-radius: 4px;
    padding: 1rem;
    margin: 1.2rem 0;
}

.review-row {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px dotted var(--tan);
}

.review-row:last-child {
    border-bottom: none;
}

.name-field {
    margin-bottom: 1.4rem;
}

.name-field label {
    display: block;
    font-size: 0.85rem;
    margin-bottom: 0.4rem;
}

.review-actions {
    display: flex;
    gap: 0.8rem;
}

.change-btn {
    flex: 1;
    padding: 14px;
    background: none;
    border: 1px solid var(--tan);
    border-radius: 4px;
}

.confirm-btn {
    flex: 2;
}

.success-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.confirm-text {
    line-height: 1.6;
    margin-bottom: 1.6rem;
}

/* ===== RESPONSIVE ===== */
@media (min-width: 720px) {
    :root {
        --container-max: 720px;
    }

    .service-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .booking-cta {
        left: auto;
        right: 24px;
        bottom: 24px;
        width: auto;
        padding: 16px 32px;
        border-radius: 999px;
        border-top: none;
        box-shadow: 0 6px 20px rgba(0,0,0,0.25);
    }
}
```

- [ ] **Step 2: Verify the server still serves it correctly**

Run: `python3 -m pytest test_server.py::StaticFileAllowlistTest -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add style.css
git commit -m "Add design tokens and component styles"
```

---

### Task 9: `app.js` — routing, i18n, hairstyle finder, booking flow

**Files:**
- Modify: `barbearia-bh-website/app.js` (replace placeholder)

- [ ] **Step 1: Write the full `app.js`**

```javascript
const LANG = {
    pt: {
        menu: 'Menu', closeMenu: 'Fechar menu',
        navHome: 'Início', navServices: 'Serviços', navHairstyle: 'Encontra o Teu Corte',
        navReviews: 'Avaliações', navLocation: 'Onde Estamos', navBook: 'Marcar',
        bookOnline: 'Marcar online', floatingBook: 'Marcar',
        heroTagline: 'Cortes · Barba · Estilo — Porto',
        servicesTitle: 'Serviços', loadingServices: 'A carregar serviços...',
        findStyleTitle: 'Encontra o Teu Corte',
        consentText: 'A tua foto é enviada a um modelo de terceiros para análise, não é guardada no nosso servidor e é descartada assim que recebemos a resposta.',
        consentAccept: 'Aceito, continuar',
        uploadSubtitle: 'Carrega uma foto nítida do teu rosto.',
        tapToUpload: 'Toca para carregar uma foto', uploadHint: 'JPG, PNG ou WebP · Máx. 8 MB',
        maintenanceLabel: 'Manutenção', beardLabel: 'Barba', lengthLabel: 'Comprimento',
        preferNoAnswer: 'Sem preferência',
        maintenanceLow: 'Baixa', maintenanceMedium: 'Média', maintenanceHigh: 'Alta',
        beardYes: 'Sim', beardNo: 'Não', beardTrimmed: 'Aparada',
        lengthShorter: 'Mais curto', lengthSimilar: 'Semelhante', lengthLonger: 'Mais comprido',
        analyseBtn: 'Analisar Foto',
        analysingPhoto: 'A analisar a tua foto — isto pode demorar alguns segundos...',
        hairstyleReport: 'O Teu Relatório de Estilo', tryAnotherPhoto: 'Analisar outra foto',
        tryAgain: 'Tentar novamente', seeServicesInstead: 'Ver lista de serviços', bookNow: 'Marcar agora',
        reviewsTitle: 'Avaliações', prevReview: 'Avaliação anterior', nextReview: 'Avaliação seguinte',
        locationTitle: 'Onde Estamos', addressLabel: 'Morada', phoneLabel: 'Telefone', hoursLabel: 'Horário',
        hoursLine: 'Segunda–Sexta, 10h–20h · Sábado, 9h–20h · Encerrado ao domingo',
        footerRights: 'Todos os direitos reservados.',
        back: '← Voltar',
        progressStep1: 'Passo 1 de 4', progressStep2: 'Passo 2 de 4',
        progressStep3: 'Passo 3 de 4', progressStep4: 'Passo 4 de 4',
        chooseService: 'Escolher um Serviço', pickDate: 'Escolher uma Data', next: 'Seguinte →',
        pickTime: 'Escolher uma Hora', loadingSlots: 'A carregar horários disponíveis...',
        noSlots: 'Sem horários disponíveis nesta data.',
        reviewConfirm: 'Rever e Confirmar', labelService: 'Serviço', labelDate: 'Data',
        labelTime: 'Hora', labelPrice: 'Preço', yourName: 'O teu nome', optional: '(opcional)',
        namePlaceholder: 'ex.: João Silva', change: 'Alterar', confirm: 'Confirmar',
        youreBooked: 'Está marcado!', at: 'às', backToHome: 'Voltar ao Início',
        bookingFailed: 'Não foi possível completar a marcação. Tenta novamente.',
        slotsFailed: 'Não foi possível carregar os horários.',
        servicesFailed: 'Não foi possível carregar os serviços.',
        photoTooLarge: 'A foto excede o limite de 8 MB.',
        invalidPhoto: 'O ficheiro tem de ser uma imagem JPG, PNG ou WebP.',
        photoPreviewAlt: 'Pré-visualização da foto carregada',
        rateLimited: 'Demasiados pedidos. Tenta novamente dentro de uma hora.',
        analysisTimeout: 'A análise demorou demasiado tempo.',
        analysisFailed: 'Não foi possível analisar a foto.',
        noFaceDetected: 'Não foi possível identificar um rosto nítido na foto. Tenta outra foto.',
        multipleFaces: 'A foto tem mais do que uma pessoa. Tenta uma foto só tua.',
    },
    en: {
        menu: 'Menu', closeMenu: 'Close menu',
        navHome: 'Home', navServices: 'Services', navHairstyle: 'Find My Hairstyle',
        navReviews: 'Reviews', navLocation: 'Find Us', navBook: 'Book',
        bookOnline: 'Book online', floatingBook: 'Book',
        heroTagline: 'Haircuts · Beards · Style — Porto',
        servicesTitle: 'Services', loadingServices: 'Loading services...',
        findStyleTitle: 'Find My Hairstyle',
        consentText: 'Your photo is sent to a third-party model for analysis, is not stored on our server, and is discarded once we receive the response.',
        consentAccept: 'I accept, continue',
        uploadSubtitle: 'Upload a clear photo of your face.',
        tapToUpload: 'Tap to upload a photo', uploadHint: 'JPG, PNG or WebP · Max 8 MB',
        maintenanceLabel: 'Maintenance', beardLabel: 'Beard', lengthLabel: 'Length',
        preferNoAnswer: 'No preference',
        maintenanceLow: 'Low', maintenanceMedium: 'Medium', maintenanceHigh: 'High',
        beardYes: 'Yes', beardNo: 'No', beardTrimmed: 'Trimmed',
        lengthShorter: 'Shorter', lengthSimilar: 'Similar', lengthLonger: 'Longer',
        analyseBtn: 'Analyse My Photo',
        analysingPhoto: 'Analysing your photo — this can take a few seconds...',
        hairstyleReport: 'Your Style Report', tryAnotherPhoto: 'Try another photo',
        tryAgain: 'Try again', seeServicesInstead: 'See the service list', bookNow: 'Book now',
        reviewsTitle: 'Reviews', prevReview: 'Previous review', nextReview: 'Next review',
        locationTitle: 'Find Us', addressLabel: 'Address', phoneLabel: 'Phone', hoursLabel: 'Hours',
        hoursLine: 'Monday–Friday, 10am–8pm · Saturday, 9am–8pm · Closed Sunday',
        footerRights: 'All rights reserved.',
        back: '← Back',
        progressStep1: 'Step 1 of 4', progressStep2: 'Step 2 of 4',
        progressStep3: 'Step 3 of 4', progressStep4: 'Step 4 of 4',
        chooseService: 'Choose a Service', pickDate: 'Pick a Date', next: 'Next →',
        pickTime: 'Pick a Time', loadingSlots: 'Loading available times...',
        noSlots: 'No available times on this date.',
        reviewConfirm: 'Review and Confirm', labelService: 'Service', labelDate: 'Date',
        labelTime: 'Time', labelPrice: 'Price', yourName: 'Your name', optional: '(optional)',
        namePlaceholder: 'e.g. John Smith', change: 'Change', confirm: 'Confirm',
        youreBooked: "You're booked!", at: 'at', backToHome: 'Back to Home',
        bookingFailed: 'Could not complete the booking. Please try again.',
        slotsFailed: 'Could not load available times.',
        servicesFailed: 'Could not load services.',
        photoTooLarge: 'The photo exceeds the 8 MB limit.',
        invalidPhoto: 'The file must be a JPG, PNG or WebP image.',
        photoPreviewAlt: 'Uploaded photo preview',
        rateLimited: 'Too many requests. Please try again in an hour.',
        analysisTimeout: 'The analysis took too long.',
        analysisFailed: 'Could not analyse the photo.',
        noFaceDetected: "We couldn't find a clear face in the photo. Try another one.",
        multipleFaces: 'The photo has more than one person. Try a photo of just you.',
    },
};

let currentLanguage = localStorage.getItem('lang') || 'pt';
let services = [];
let selectedService = null;
let selectedDate = null;
let selectedTime = null;
let selectedPhotoBlob = null;
let currentReviewIndex = 0;
const TOTAL_REVIEWS = 3;

function t(key) {
    return LANG[currentLanguage][key] || key;
}

function setLanguage(lang) {
    currentLanguage = lang;
    localStorage.setItem('lang', lang);
    document.querySelectorAll('[data-i18n]').forEach((el) => {
        el.textContent = t(el.getAttribute('data-i18n'));
    });
    document.querySelectorAll('[data-i18n-aria-label]').forEach((el) => {
        el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria-label')));
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
        el.setAttribute('placeholder', t(el.getAttribute('data-i18n-placeholder')));
    });
    document.querySelectorAll('.lang-option').forEach((btn) => {
        btn.setAttribute('aria-current', btn.getAttribute('data-lang') === lang ? 'true' : 'false');
    });
    document.documentElement.setAttribute('lang', lang);
}

function toggleNav() {
    const overlay = document.getElementById('nav-overlay');
    const toggle = document.querySelector('.nav-toggle');
    const isHidden = overlay.hasAttribute('hidden');
    if (isHidden) {
        overlay.removeAttribute('hidden');
        toggle.setAttribute('aria-expanded', 'true');
    } else {
        overlay.setAttribute('hidden', '');
        toggle.setAttribute('aria-expanded', 'false');
    }
}

function closeNavTo(sectionId) {
    document.getElementById('nav-overlay').setAttribute('hidden', '');
    document.querySelector('.nav-toggle').setAttribute('aria-expanded', 'false');
    goHome();
    requestAnimationFrame(() => {
        const el = document.getElementById(sectionId);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
}

function closeNavAndBook() {
    document.getElementById('nav-overlay').setAttribute('hidden', '');
    document.querySelector('.nav-toggle').setAttribute('aria-expanded', 'false');
    goTo('page-service');
}

function goTo(pageId) {
    document.querySelectorAll('.page').forEach((page) => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    window.scrollTo(0, 0);
}

function goHome() {
    goTo('page-home');
}

/* ===== SERVICES ===== */

function fetchServices() {
    fetch('/api/services')
        .then((res) => {
            if (!res.ok) {
                throw new Error('services request failed');
            }
            return res.json();
        })
        .then((data) => {
            services = data.services || [];
            renderServiceList();
            renderServiceGrid();
        })
        .catch(() => {
            document.getElementById('service-list').innerHTML = `<li class="service-row-loading">${t('servicesFailed')}</li>`;
            document.getElementById('service-grid').innerHTML = `<p>${t('servicesFailed')}</p>`;
        });
}

function renderServiceList() {
    const list = document.getElementById('service-list');
    list.innerHTML = '';
    services.forEach((service) => {
        const li = document.createElement('li');
        li.className = 'service-row';
        li.innerHTML = `
            <span class="service-row-icon" aria-hidden="true">✂</span>
            <span class="service-row-body">
                <span>
                    <span class="service-row-name">${service.name}</span>
                    <span class="service-row-desc">${service.description}</span>
                </span>
                <span class="service-row-price">€${service.price}</span>
            </span>
        `;
        list.appendChild(li);
    });
}

function renderServiceGrid() {
    const grid = document.getElementById('service-grid');
    grid.innerHTML = '';
    services.forEach((service) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'service-card';
        btn.onclick = () => selectService(service.id);
        btn.innerHTML = `<strong>${service.name}</strong><span class="price">€${service.price}</span>`;
        grid.appendChild(btn);
    });
}

function selectService(serviceId) {
    selectedService = services.find((s) => s.id === serviceId) || null;
    goTo('page-date');
}

function findServiceByName(name) {
    if (!name) return null;
    const normalized = name.trim().toLowerCase();
    return services.find((s) => s.name.trim().toLowerCase() === normalized) || null;
}

/* ===== BOOKING FLOW ===== */

function dateSelected(value) {
    selectedDate = value;
    document.getElementById('dateNextBtn').disabled = !value;
}

function goToTime() {
    goTo('page-time');
    const container = document.getElementById('slotsContainer');
    container.innerHTML = `<div class="loading">${t('loadingSlots')}</div>`;

    fetch(`/api/slots?date=${encodeURIComponent(selectedDate)}`)
        .then((res) => {
            if (!res.ok) {
                throw new Error('slots request failed');
            }
            return res.json();
        })
        .then((data) => {
            const slots = data.slots || [];
            if (slots.length === 0) {
                container.innerHTML = `<div class="loading">${t('noSlots')}</div>`;
                return;
            }
            container.innerHTML = '';
            slots.forEach((slot) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'slot-btn';
                btn.textContent = slot;
                btn.setAttribute('aria-pressed', 'false');
                btn.onclick = () => selectTime(slot, btn);
                container.appendChild(btn);
            });
        })
        .catch(() => {
            container.innerHTML = `<div class="loading">${t('slotsFailed')}</div>`;
        });
}

function selectTime(slot, button) {
    selectedTime = slot;
    document.querySelectorAll('.slot-btn').forEach((btn) => btn.setAttribute('aria-pressed', 'false'));
    button.setAttribute('aria-pressed', 'true');
    renderReview();
    goTo('page-review');
}

function renderReview() {
    document.getElementById('review-service').textContent = selectedService ? selectedService.name : '';
    document.getElementById('review-date').textContent = selectedDate || '';
    document.getElementById('review-time').textContent = selectedTime || '';
    document.getElementById('review-price').textContent = selectedService ? `€${selectedService.price}` : '';
}

function confirmBooking() {
    const confirmBtn = document.getElementById('confirmBtn');
    confirmBtn.disabled = true;

    const name = document.getElementById('nameInput').value;

    fetch('/api/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            date: selectedDate,
            time: selectedTime,
            service: selectedService ? selectedService.name : '',
            name,
        }),
    })
        .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
        .then(({ ok, data }) => {
            confirmBtn.disabled = false;
            if (!ok) {
                alert(t('bookingFailed'));
                return;
            }
            document.getElementById('confirm-service').textContent = selectedService ? selectedService.name : '';
            document.getElementById('confirm-date').textContent = selectedDate;
            document.getElementById('confirm-time').textContent = selectedTime;
            goTo('page-confirmed');
        })
        .catch(() => {
            confirmBtn.disabled = false;
            alert(t('bookingFailed'));
        });
}

/* ===== HAIRSTYLE FINDER ===== */

function showHairstyleView(viewId) {
    document.querySelectorAll('.hairstyle-view').forEach((view) => view.classList.add('hidden'));
    document.getElementById(viewId).classList.remove('hidden');
}

function acceptConsent() {
    showHairstyleView('hairstyle-upload-view');
}

function downscaleImage(file, maxDimension) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const img = new Image();
            img.onload = () => {
                let { width, height } = img;
                if (width > maxDimension || height > maxDimension) {
                    if (width > height) {
                        height = Math.round((height * maxDimension) / width);
                        width = maxDimension;
                    } else {
                        width = Math.round((width * maxDimension) / height);
                        height = maxDimension;
                    }
                }
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                canvas.getContext('2d').drawImage(img, 0, 0, width, height);
                canvas.toBlob((blob) => {
                    if (blob) {
                        resolve(blob);
                    } else {
                        reject(new Error('Could not process image'));
                    }
                }, file.type || 'image/jpeg', 0.9);
            };
            img.onerror = reject;
            img.src = reader.result;
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function photoSelected(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (file.size > 8 * 1024 * 1024) {
        showHairstyleView('hairstyle-error-view');
        document.getElementById('hairstyleErrorText').textContent = t('photoTooLarge');
        return;
    }

    downscaleImage(file, 1568).then((blob) => {
        selectedPhotoBlob = blob;
        const preview = document.getElementById('photoPreview');
        preview.src = URL.createObjectURL(blob);
        preview.alt = t('photoPreviewAlt');
        preview.classList.remove('hidden');
        document.getElementById('uploadPlaceholder').classList.add('hidden');
        document.getElementById('analyseBtn').disabled = false;
    }).catch(() => {
        showHairstyleView('hairstyle-error-view');
        document.getElementById('hairstyleErrorText').textContent = t('invalidPhoto');
    });
}

function analysePhoto() {
    if (!selectedPhotoBlob) return;

    showHairstyleView('hairstyle-loading-view');

    const formData = new FormData();
    formData.append('photo', selectedPhotoBlob, 'photo.jpg');
    formData.append('language', currentLanguage);
    formData.append('maintenance', document.getElementById('maintenanceInput').value);
    formData.append('beard', document.getElementById('beardInput').value);
    formData.append('length_goal', document.getElementById('lengthInput').value);

    fetch('/api/hairstyle', { method: 'POST', body: formData })
        .then((res) => res.json().then((data) => ({ status: res.status, data })))
        .then(({ status, data }) => {
            if (status === 429) {
                showHairstyleError(t('rateLimited'));
                return;
            }
            if (status === 504) {
                showHairstyleError(t('analysisTimeout'));
                return;
            }
            if (status >= 400) {
                showHairstyleError(t('analysisFailed'));
                return;
            }
            renderHairstyleResults(data.analysis);
        })
        .catch(() => {
            showHairstyleError(t('analysisFailed'));
        });
}

function showHairstyleError(message) {
    showHairstyleView('hairstyle-error-view');
    document.getElementById('hairstyleErrorText').textContent = message;
}

function renderHairstyleResults(analysis) {
    if (!analysis || analysis.status === 'no_face') {
        showHairstyleError(t('noFaceDetected'));
        return;
    }
    if (analysis.status === 'multiple_faces') {
        showHairstyleError(t('multipleFaces'));
        return;
    }
    if (analysis.status === 'error' || !analysis.recommendations || analysis.recommendations.length === 0) {
        showHairstyleError(t('analysisFailed'));
        return;
    }

    const container = document.getElementById('resultsContent');
    container.innerHTML = '';
    analysis.recommendations.forEach((rec) => {
        const matchedService = findServiceByName(rec.closest_service);
        const card = document.createElement('div');
        card.className = 'result-card';
        card.innerHTML = `
            <h4>${rec.style_name}</h4>
            <p>${rec.why}</p>
            <p><strong>${t('maintenanceLabel')}:</strong> ${rec.upkeep}</p>
        `;
        const link = document.createElement('a');
        link.href = '#';
        link.textContent = t('bookNow');
        link.onclick = (e) => {
            e.preventDefault();
            if (matchedService) {
                selectedService = matchedService;
            }
            goTo('page-service');
        };
        card.appendChild(link);
        container.appendChild(card);
    });

    showHairstyleView('hairstyle-results-view');
}

function resetHairstyleFinder() {
    selectedPhotoBlob = null;
    document.getElementById('photoInput').value = '';
    document.getElementById('photoPreview').classList.add('hidden');
    document.getElementById('uploadPlaceholder').classList.remove('hidden');
    document.getElementById('analyseBtn').disabled = true;
    showHairstyleView('hairstyle-consent-view');
}

/* ===== REVIEWS ===== */

function changeReview(delta) {
    document.getElementById(`review-${currentReviewIndex}`).classList.remove('active');
    currentReviewIndex = (currentReviewIndex + delta + TOTAL_REVIEWS) % TOTAL_REVIEWS;
    document.getElementById(`review-${currentReviewIndex}`).classList.add('active');
}

/* ===== INIT ===== */

document.addEventListener('DOMContentLoaded', () => {
    setLanguage(currentLanguage);
    fetchServices();
});
```

- [ ] **Step 2: Verify the server still serves it correctly**

Run: `python3 -m pytest test_server.py::StaticFileAllowlistTest -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add app.js
git commit -m "Add client-side routing, hairstyle finder, and booking flow logic"
```

---

### Task 10: Deployment files, README, hero image

**Files:**
- Create: `barbearia-bh-website/requirements.txt`
- Create: `barbearia-bh-website/render.yaml`
- Create: `barbearia-bh-website/.env.example`
- Create: `barbearia-bh-website/README.md`
- `barbearia-bh-website/images/hero.jpg` already exists (copied from the client-supplied shop photo at `/Users/test/Desktop/photo_2026-07-23_20-26-08.jpg` before this plan's execution began) — nothing to do for it in this task beyond the `git add` in Step 5.

- [ ] **Step 1: Write `requirements.txt`**

```
Flask==3.1.3
gunicorn==26.0.0
python-dotenv==1.2.2
google-auth==2.56.1
google-auth-httplib2==0.4.0
google-api-python-client==2.198.0
anthropic==0.118.0
```

- [ ] **Step 2: Write `render.yaml`**

```yaml
services:
  - type: web
    name: barbearia-bh
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn server:app --bind 0.0.0.0:$PORT
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: CALENDAR_ID
        sync: false
      - key: TIMEZONE
        value: Europe/Lisbon
      - key: GOOGLE_CREDENTIALS_JSON
        sync: false
```

- [ ] **Step 3: Write `.env.example`**

```
ANTHROPIC_API_KEY=your-anthropic-api-key
CALENDAR_ID=the-calendar-id-to-book-into
TIMEZONE=Europe/Lisbon
```

Note: `CALENDAR_ID` for this deployment is `alexgondar08@gmail.com` (client-supplied) — put the real value in the local `.env`, not in `.env.example`. `credentials.json` and `.env` are created by the client after the site itself is built, per their instruction — nothing to do here beyond documenting the variables.

- [ ] **Step 4: Write `README.md`**

```markdown
# Barbearia BH Website

Marketing site for Barbearia BH, a barbershop in Porto, Portugal: browse services, book an
appointment (synced to Google Calendar), and get an AI-powered haircut recommendation from a
selfie via the Anthropic Messages API.

## Stack

- Backend: Flask (`server.py`)
- Calendar sync: Google Calendar API via a service account (`booking.py`)
- Hairstyle analysis: Anthropic Messages API, `claude-opus-4-8` (`hairstyle.py`)
- Frontend: static HTML/CSS/JS (`index.html`, `style.css`, `app.js`)

## Setup

### 1. Install dependencies

```bash
cd barbearia-bh-website
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create `.env`

This file is gitignored and must be created locally (see `.env.example`):

```
ANTHROPIC_API_KEY=your-anthropic-api-key
CALENDAR_ID=the-calendar-id-to-book-into
TIMEZONE=Europe/Lisbon
```

- **ANTHROPIC_API_KEY** — get one from the [Anthropic Console](https://console.anthropic.com/).
- **CALENDAR_ID** — the Google Calendar to create bookings in (a Gmail address, or `primary` to default to the service account's own calendar).
- **TIMEZONE** — IANA timezone name used for booked events (default `Europe/Lisbon`).

### 3. Add `credentials.json`

Also gitignored. This is a Google Cloud service account key with access to the Calendar API:

1. In the [Google Cloud Console](https://console.cloud.google.com/), create (or reuse) a project and enable the **Google Calendar API**.
2. Create a service account, then generate a JSON key for it.
3. Save the downloaded key as `credentials.json` in the project root.
4. Share the target Google Calendar with the service account's email address (found in `client_email` in the JSON file), granting it "Make changes to events" access.

### 4. Run the tests

```bash
python3 -m pytest
```

### 5. Run the server

```bash
python server.py
```

Serves the site at `http://localhost:8080`.

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/services` | GET | List configured services (from `config.py`) |
| `/api/slots?date=YYYY-MM-DD` | GET | List available 30-minute slots for a date |
| `/api/book` | POST | Book a slot (`date`, `time`, `service`, optional `name`) |
| `/api/hairstyle` | POST | Upload a photo (`photo` form field, plus optional `language`, `maintenance`, `beard`, `length_goal`) for a Claude-powered haircut recommendation. Rate-limited to 5 requests/hour per IP. |

## TODO before launch

- **Confirm the business name.** The client asked to keep "Barbearia BH" for now, but the reviews and the only logo asset supplied so far read "Donk / Donk — The Barbearshop". Confirm with the client and update the wordmark, page title, footer, and `alt` text throughout if it changes.
- Get phone number, Instagram handle, and WhatsApp number from the client (`config.py`'s `BUSINESS_INFO` and the `#location` section in `index.html`).
- Confirm service descriptions and durations — the current list reuses noble's names/prices as instructed, but has no real descriptions or durations yet.
- Create `.env` and `credentials.json` (client is doing this after the site is built) — see Setup below. `CALENDAR_ID` is `alexgondar08@gmail.com`.

## Deploying to Render

The repo includes a `render.yaml` blueprint that defines the web service (`gunicorn server:app`).

1. On [Render](https://dashboard.render.com/), **New > Blueprint**, and connect this repo.
2. Render reads `render.yaml` and creates the service, prompting for the env vars marked `sync: false`:
   - `ANTHROPIC_API_KEY`
   - `CALENDAR_ID`
   - `GOOGLE_CREDENTIALS_JSON` — since `credentials.json` isn't in the repo, paste its **entire file contents** as the value of this env var instead. `booking.py` reads this var first and falls back to a local `credentials.json` file if it's not set, so local dev is unaffected.
3. Deploy. Render builds with `pip install -r requirements.txt` and starts with `gunicorn server:app --bind 0.0.0.0:$PORT`.
```

- [ ] **Step 5: Commit**

```bash
git add requirements.txt render.yaml .env.example README.md images/hero.jpg
git commit -m "Add deployment config, README, and hero image"
```

---

### Task 11: Full test suite + manual verification + self-critique

**Files:** none (verification only)

- [ ] **Step 1: Run the full backend test suite**

Run: `cd /Users/test/PycharmProjects/barbearia-bh-website && python3 -m pytest -v`
Expected: all tests across `test_booking.py`, `test_hairstyle.py`, `test_image_validation.py`, `test_ratelimit.py`, `test_server.py` PASS.

- [ ] **Step 2: Start the dev server and manually verify the golden path**

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # a real key, or skip and expect /api/hairstyle to fail gracefully
export CALENDAR_ID=primary
python3 server.py
```

Open `http://localhost:8080` in a browser and check:
- Hero photo renders full-bleed with the wordmark overlay; persistent booking CTA is visible immediately (bottom bar on mobile width, pill bottom-right above 720px).
- Services section populates from `/api/services` (no hardcoded HTML).
- Hairstyle finder: consent gate blocks the uploader until accepted; after accepting, file picker opens; after choosing a photo, a preview appears and "Analisar Foto" enables; submitting shows the descriptive loading text, then either recommendations (each linking into booking with the matched service preselected) or a graceful error with a manual fallback link to the services section.
- Reviews carousel advances with prev/next and stays keyboard-operable (Tab + Enter).
- Booking flow: service → date → time → review → confirm, all four steps reachable both from the persistent CTA and from a hairstyle recommendation's "Marcar agora" link.
- Toggle PT/EN and confirm all visible strings swap (including `aria-label`s and the date-input placeholder).
- Resize below 720px and confirm the CTA becomes a full-width bottom bar; above 720px confirm it becomes a pill.
- With OS-level "reduce motion" enabled, confirm smooth-scroll and transitions are suppressed.

- [ ] **Step 3: Self-critique against the spec**

Re-read `CLAUDE.md` sections 1–4 end to end and confirm, in a short written note (not a new file — just a summary in the final report to the user):
- Section order matches (Logo/hero → Services → Find My Hairstyle → Reviews → Information) — yes, `index.html`'s `#page-home` section order.
- Consent-gate copy names the third party, no-storage, and discard-after-response — yes, `consentText` in both languages.
- Backend requirements checklist: env-var-only API key ✅, magic-byte MIME validation ✅, size cap before OOM risk (via `MAX_CONTENT_LENGTH`) ✅, 5/hour rate limit with 429 ✅, in-memory-only image handling (no disk writes, no logging of bytes) ✅, structured JSON output via `output_config.format` with defensive fallback parsing ✅, 30s timeout with distinct recovery messages per failure mode ✅.
- Model prompt constraints: declines attractiveness/age/weight/ethnicity commentary, no identification, `no_face`/`multiple_faces` status codes ✅ — flag to the user that actual model behavior should be spot-checked with a real API key before launch, since prompt compliance can't be unit-tested.
- Accessibility: keyboard path, live regions, descriptive loading state, reduced-motion ✅.
- No copied text/imagery/assets from velhojackbarbershop, kultiv, or noble — confirm by diffing wording against the reference repos' copy.

- [ ] **Step 4: Report results to the user**

Summarize: test counts and pass/fail, what was manually verified in the browser, and the explicit TODO list from the README (placeholder services/hours/contact info, hero photo, reviews) that blocks real launch.
