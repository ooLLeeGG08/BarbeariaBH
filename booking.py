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
