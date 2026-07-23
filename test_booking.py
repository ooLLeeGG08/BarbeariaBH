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
