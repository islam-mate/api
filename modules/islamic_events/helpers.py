"""
modules/islamic_events/helpers.py
===================================
Pure standalone helpers for Hijri/Gregorian date conversion and
recurring Islamic calendar events.

No self.translate() here — all functions are stateless and importable anywhere.

Imported by module.py:
  from .helpers import hijri_to_gregorian, gregorian_to_hijri, get_all_fridays, get_white_days
"""

from datetime import date, timedelta
from hijridate import Gregorian, Hijri


def hijri_to_gregorian(year: int, month: int, day: int) -> date | None:
    """Convert a Hijri date to a Gregorian date. Returns None on invalid input."""
    try:
        g = Hijri(year, month, day).to_gregorian()
        return date(g.year, g.month, g.day)
    except Exception:
        return None


def gregorian_to_hijri(d: date) -> tuple[int, int, int]:
    """Convert a Gregorian date to a Hijri (year, month, day) tuple.
    Returns (None, None, None) on error."""
    try:
        h = Gregorian(d.year, d.month, d.day).to_hijri()
        return h.year, h.month, h.day
    except Exception:
        return None, None, None


def get_all_fridays(year: int) -> list[date]:
    """Return a list of all Fridays in the given Gregorian year."""
    fridays = []
    d = date(year, 1, 1)
    # Advance to the first Friday (weekday 4)
    while d.weekday() != 4:
        d += timedelta(days=1)
    while d.year == year:
        fridays.append(d)
        d += timedelta(days=7)
    return fridays


def get_white_days(hijri_year: int) -> list[dict]:
    """Return White Days (13th, 14th, 15th) for every Hijri month in the given year.

    Each entry: {"hijri_day": int, "hijri_month": int, "gregorian_date": str}
    Entries where the conversion fails are silently skipped.
    """
    white_days = []
    for month in range(1, 13):
        for day in [13, 14, 15]:
            g_date = hijri_to_gregorian(hijri_year, month, day)
            if g_date:
                white_days.append({
                    "hijri_day": day,
                    "hijri_month": month,
                    "gregorian_date": str(g_date),
                })
    return white_days
