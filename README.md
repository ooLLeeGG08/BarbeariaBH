# Barbearia BH Website

Marketing site for Barbearia BH, a barbershop in Porto, Portugal: browse services, book an
appointment (synced to Google Calendar), and get an AI-powered haircut recommendation from a
selfie via the Google Gemini API.

## Stack

- Backend: Flask (`server.py`)
- Calendar sync: Google Calendar API via a service account (`booking.py`)
- Hairstyle analysis: Google Gemini API, `gemini-flash-latest` (`hairstyle.py`)
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
GEMINI_API_KEY=your-gemini-api-key
CALENDAR_ID=the-calendar-id-to-book-into
TIMEZONE=Europe/Lisbon
```

- **GEMINI_API_KEY** — get one from [Google AI Studio](https://aistudio.google.com/apikey).
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
| `/api/hairstyle` | POST | Upload a photo (`photo` form field, plus optional `language`, `maintenance`, `beard`, `length_goal`) for a Gemini-powered haircut recommendation. Rate-limited to 5 requests/hour per IP. |

## TODO before launch

- Confirm service descriptions and durations — the current list reuses noble's names/prices as instructed, but has no real descriptions or durations yet.
- WhatsApp number (`config.py`'s `BUSINESS_INFO.whatsapp`) is assumed to be the same as the phone number — confirm with the client.
- `.env` and `credentials.json` are already set up locally with real `GEMINI_API_KEY`, `CALENDAR_ID` (`alexgondar08@gmail.com`), and Google service-account credentials — both real integrations (Calendar availability, Gemini hairstyle analysis) have been verified working end-to-end.

## Deploying to Render

The repo includes a `render.yaml` blueprint that defines the web service (`gunicorn server:app`).

1. On [Render](https://dashboard.render.com/), **New > Blueprint**, and connect this repo.
2. Render reads `render.yaml` and creates the service, prompting for the env vars marked `sync: false`:
   - `GEMINI_API_KEY`
   - `CALENDAR_ID`
   - `GOOGLE_CREDENTIALS_JSON` — since `credentials.json` isn't in the repo, paste its **entire file contents** as the value of this env var instead. `booking.py` reads this var first and falls back to a local `credentials.json` file if it's not set, so local dev is unaffected.
3. Deploy. Render builds with `pip install -r requirements.txt` and starts with `gunicorn server:app --bind 0.0.0.0:$PORT`.
