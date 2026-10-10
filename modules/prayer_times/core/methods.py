"""
Prayer Times calculation — PrayTimes.org algorithm (Python port)
Author: Hamid Zarrabi-Zadeh (original JS), ported to Python for Islam-Mate
"""
import math
from datetime import datetime, timedelta, date as _date
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class CalculationMethod(Enum):
    MWL = "MWL"      # Muslim World League
    ISNA = "ISNA"     # Islamic Society of North America
    EGYPT = "EGYPT"    # Egyptian General Authority of Survey
    MAKKAH = "MAKKAH"   # Umm al-Qura, Makkah
    KARACHI = "KARACHI"  # University of Islamic Sciences, Karachi
    TEHRAN = "TEHRAN"   # Institute of Geophysics, Tehran
    JAFARI = "JAFARI"   # Shia Ithna-Ashari, Leva Research Institute, Qum


class AsrMethod(Enum):
    STANDARD = "STANDARD"   # Shafi'i, Maliki, Hanbali — shadow factor 1
    HANAFI = "HANAFI"     # Hanafi — shadow factor 2


# ── Method parameters: (fajr_angle, isha_param, isha_is_minutes) ──────────────
_METHOD_PARAMS = {
    "MWL":     (18.0,  17.0,  False),
    "ISNA":    (15.0,  15.0,  False),
    "EGYPT":   (19.5,  17.5,  False),
    "MAKKAH":  (18.5,  90,    True),   # 90 min after Maghrib
    "KARACHI": (18.0,  18.0,  False),
    "TEHRAN":  (17.7,  14.0,  False),
    "JAFARI":  (16.0,  14.0,  False),
}


# ── Degree-based trig helpers ─────────────────────────────────────────────────

def _sind(x): return math.sin(math.radians(x))
def _cosd(x): return math.cos(math.radians(x))
def _tand(x): return math.tan(math.radians(x))
def _asind(x): return math.degrees(math.asin(max(-1.0, min(1.0, x))))
def _acosd(x): return math.degrees(math.acos(max(-1.0, min(1.0, x))))
def _atan2d(y, x): return math.degrees(math.atan2(y, x))


def _fix_angle(a):
    a = a % 360
    return a + 360 if a < 0 else a


def _fix_hour(h):
    h = h % 24
    return h + 24 if h < 0 else h


# ── Julian date ───────────────────────────────────────────────────────────────

def _julian_date(year: int, month: int, day: int) -> float:
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5


# ── Sun position ──────────────────────────────────────────────────────────────

def _sun_position(jd: float):
    """Return (declination_deg, equation_of_time_hours)."""
    D = jd - 2451545.0
    g = _fix_angle(357.529 + 0.98560028 * D)
    q = _fix_angle(280.459 + 0.98564736 * D)
    L = _fix_angle(q + 1.915 * _sind(g) + 0.020 * _sind(2 * g))
    e = 23.439 - 0.00000036 * D
    RA = _atan2d(_cosd(e) * _sind(L), _cosd(L)) / 15.0
    dec = _asind(_sind(e) * _sind(L))
    EqT = q / 15.0 - _fix_hour(RA)
    return dec, EqT


# ── Core time functions (times are fractions of a day: 0.5 = noon) ───────────

def _mid_day(t: float, jd: float) -> float:
    """Return Dhuhr time as fraction-of-day (local solar time)."""
    _, EqT = _sun_position(jd + t)
    return _fix_hour(12 - EqT) / 24.0


def _sun_angle_time(angle: float, t: float, jd: float, lat: float, ccw: bool = False) -> float:
    """
    Return time (fraction of day) when sun crosses the given elevation angle.
    angle < 0 means below horizon (e.g. -19.5 for Fajr, -0.8333 for sunrise).
    ccw=True for morning (before noon), False for afternoon/evening.

    Standard formula:  cos(H) = (sin(alt) − sin(lat)·sin(dec)) / (cos(lat)·cos(dec))
    """
    dec, _ = _sun_position(jd + t)
    noon = _mid_day(t, jd)
    cos_val = (_sind(angle) - _sind(dec) * _sind(lat)) / \
        (_cosd(dec) * _cosd(lat))
    ha = _acosd(cos_val) / 15.0 / 24.0   # day fraction
    return noon + (-ha if ccw else ha)


def _asr_time(shadow_factor: float, t: float, jd: float, lat: float) -> float:
    """Return Asr time as fraction of day.
    Asr elevation = arctan(1 / (shadow_factor + tan(|lat - dec|))).
    This is a positive angle (sun above horizon).
    """
    dec, _ = _sun_position(jd + t)
    target_angle = math.degrees(
        math.atan(1.0 / (shadow_factor + _tand(abs(lat - dec)))))
    return _sun_angle_time(target_angle, t, jd, lat)


# ── Main public class ─────────────────────────────────────────────────────────

class PrayerTimes:
    """
    Calculate Islamic prayer times for a given date and location.

    Usage::

        from datetime import date
        import pytz

        pt = PrayerTimes(CalculationMethod.EGYPT, AsrMethod.STANDARD)
        tz = pytz.timezone("Africa/Cairo")
        times = pt.calc_times(date.today(), tz, longitude=31.23, latitude=30.04)
        # → dict: fajr, sunrise, dhuhr, asr, maghrib, isha → aware datetime
    """

    def __init__(
        self,
        method: CalculationMethod = CalculationMethod.EGYPT,
        asr: AsrMethod = AsrMethod.STANDARD,
    ):
        self.method = method
        self.asr = asr
        params = _METHOD_PARAMS[method.value]
        self.fajr_angle: float = params[0]
        self.isha_param: float = params[1]
        self.isha_is_minutes: bool = params[2]
        self.shadow_factor: float = 1.0 if asr == AsrMethod.STANDARD else 2.0

    # ── Iteration seeds (fraction of day) ────────────────────────────────────

    _SEEDS = {
        "fajr":    5 / 24.0,
        "sunrise": 6 / 24.0,
        "dhuhr":   12 / 24.0,
        "asr":     13 / 24.0,
        "maghrib": 18 / 24.0,
        "isha":    18 / 24.0,
    }

    def _compute_raw(self, t: float, name: str, jd: float, lat: float) -> float:
        """Return prayer time as fraction-of-day in local solar time."""
        if name == "dhuhr":
            return _mid_day(t, jd)
        elif name == "sunrise":
            return _sun_angle_time(-0.8333, t, jd, lat, ccw=True)
        elif name == "fajr":
            return _sun_angle_time(-self.fajr_angle, t, jd, lat, ccw=True)
        elif name == "asr":
            return _asr_time(self.shadow_factor, t, jd, lat)
        elif name == "maghrib":
            return _sun_angle_time(-0.8333, t, jd, lat)   # sunset
        elif name == "isha":
            if self.isha_is_minutes:
                # handled after loop
                return float("nan")
            return _sun_angle_time(-self.isha_param, t, jd, lat)
        return float("nan")

    def calc_times(
        self,
        day: _date,
        timezone,
        longitude: float,
        latitude: float,
    ) -> dict[str, datetime]:
        """
        Calculate prayer times.

        :param day: date to calculate for
        :param timezone: pytz timezone object OR UTC offset float
        :param longitude: degrees East (negative West)
        :param latitude: degrees North (negative South)
        :returns: dict of {name: aware datetime} for fajr, sunrise, dhuhr, asr, maghrib, isha
        """
        # ── Resolve UTC offset ────────────────────────────────────────────────
        if isinstance(timezone, (int, float)):
            tz_offset = float(timezone)
            tz_obj = None
        else:
            tz_obj = timezone
            naive_midnight = datetime(day.year, day.month, day.day, 0, 0)
            localized = tz_obj.localize(naive_midnight)
            tz_offset = localized.utcoffset().total_seconds() / 3600.0

        # ── Julian date for noon of the given day in UTC ──────────────────────
        # We anchor at UTC noon so the iteration converges properly
        jd = _julian_date(day.year, day.month, day.day) + \
            (tz_offset - longitude / 15.0) / 24.0

        # ── Iterative refinement (2 passes) ───────────────────────────────────
        names = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]
        solar = dict(self._SEEDS)

        for _ in range(2):
            for name in names:
                solar[name] = self._compute_raw(
                    solar[name], name, jd, latitude)

        # ── Isha for minute-based methods (e.g. Makkah: 90 min after Maghrib) ─
        if self.isha_is_minutes:
            solar["isha"] = solar["maghrib"] + self.isha_param / 60.0 / 24.0

        # ── Adjust from local solar time to clock time ────────────────────────
        # Correction: (tz_offset - longitude/15) / 24   (in day fractions)
        correction = (tz_offset - longitude / 15.0) / 24.0

        result: dict[str, datetime] = {}
        for name in names:
            local_frac = _fix_hour((solar[name] + correction) * 24) / 24.0
            hh_f = local_frac * 24.0
            hh = int(hh_f) % 24
            mm = int(round((hh_f - int(hh_f)) * 60))
            if mm >= 60:
                hh = (hh + 1) % 24
                mm -= 60

            naive_dt = datetime(day.year, day.month, day.day, hh, mm)
            if tz_obj is not None:
                try:
                    aware_dt = tz_obj.localize(naive_dt, is_dst=None)
                except Exception:
                    aware_dt = tz_obj.localize(naive_dt)
            else:
                from datetime import timezone as _tzmod
                aware_dt = naive_dt.replace(
                    tzinfo=_tzmod(timedelta(hours=tz_offset)))

            result[name] = aware_dt

        return result


# ── Utility ───────────────────────────────────────────────────────────────────

AVAILABLE_METHODS = list(_METHOD_PARAMS.keys())
