"""
Unit tests for modules/prayer_times/core/calculations.py

Tests based on salat v1.1.1 upstream tests (MIT license):
  https://github.com/zainhussaini/salat
Adapted for Islam Mate API's calculations module.

Reference values:
  - Equation of time: http://www.ppowers.com/EoT.htm
  - Kepler solver: http://www.jgiesen.de/kepler/kepler.html
"""

import datetime as dt
import math
import pytest

from modules.prayer_times.core.calculations import (
    eot_decl,
    kepler_solve,
    calc_altitude,
    timedelta_at_altitude,
    time_zenith,
    time_altitude,
    time_shadow_factor,
)

# ── Tolerances ─────────────────────────────────────────────────────────────────
EOT_MARGIN_SECONDS    = 1      # abs tolerance: equation of time
KEPLER_REL_TOLERANCE  = 1e-3   # relative tolerance: Kepler solution
ALTITUDE_REL_TOLERANCE = 1e-5  # relative tolerance: altitude calculations
TIME_ABS_TOLERANCE    = 1e-3   # seconds: time convergence checks


# ════════════════════════════════════════════════════════════════════════════════
# Equation of Time & Declination
# ════════════════════════════════════════════════════════════════════════════════

class TestEquationOfTime:

    def test_eot_january(self):
        """Jan 1 2023: EoT ≈ -3m27s."""
        time = dt.datetime(2023, 1, 1, hour=12, tzinfo=dt.timezone.utc)
        expected = dt.timedelta(minutes=-3, seconds=-27)
        eot, decl = eot_decl(time)
        assert math.isclose(
            eot.total_seconds(), expected.total_seconds(), abs_tol=EOT_MARGIN_SECONDS
        )

    def test_eot_may(self):
        """May 1 2023: EoT ≈ +2m52s."""
        time = dt.datetime(2023, 5, 1, hour=12, tzinfo=dt.timezone.utc)
        expected = dt.timedelta(minutes=2, seconds=52)
        eot, decl = eot_decl(time)
        assert math.isclose(
            eot.total_seconds(), expected.total_seconds(), abs_tol=EOT_MARGIN_SECONDS
        )

    def test_eot_september(self):
        """Sep 1 2023: EoT ≈ -6s."""
        time = dt.datetime(2023, 9, 1, hour=12, tzinfo=dt.timezone.utc)
        expected = dt.timedelta(seconds=-6)
        eot, decl = eot_decl(time)
        assert math.isclose(
            eot.total_seconds(), expected.total_seconds(), abs_tol=EOT_MARGIN_SECONDS
        )

    def test_eot_returns_timedelta(self):
        time = dt.datetime(2023, 6, 15, hour=12, tzinfo=dt.timezone.utc)
        eot, decl = eot_decl(time)
        assert isinstance(eot, dt.timedelta)

    def test_decl_returns_float_radians(self):
        time = dt.datetime(2023, 6, 15, hour=12, tzinfo=dt.timezone.utc)
        eot, decl = eot_decl(time)
        assert isinstance(decl, float)
        # declination must be in [-π/2, π/2]
        assert -math.pi / 2 <= decl <= math.pi / 2

    def test_decl_june_solstice_positive(self):
        """Near June solstice: declination should be near +23.4°."""
        time = dt.datetime(2023, 6, 21, hour=12, tzinfo=dt.timezone.utc)
        _, decl = eot_decl(time)
        assert math.isclose(decl, math.radians(23.4), abs_tol=0.01)

    def test_decl_december_solstice_negative(self):
        """Near December solstice: declination near -23.4°."""
        time = dt.datetime(2023, 12, 21, hour=12, tzinfo=dt.timezone.utc)
        _, decl = eot_decl(time)
        assert math.isclose(decl, math.radians(-23.4), abs_tol=0.01)

    def test_decl_equinox_near_zero(self):
        """Near March equinox: declination near 0°."""
        time = dt.datetime(2023, 3, 20, hour=12, tzinfo=dt.timezone.utc)
        _, decl = eot_decl(time)
        assert abs(decl) < math.radians(2)


# ════════════════════════════════════════════════════════════════════════════════
# Kepler Solver
# ════════════════════════════════════════════════════════════════════════════════

class TestKeplerSolve:

    def test_reference_value(self):
        """M=27°, e=0.5 → E≈48.43° (reference: jgiesen.de/kepler)."""
        M = math.radians(27)
        e = 0.5
        E_expected = math.radians(48.43)
        E = kepler_solve(M, e)
        assert math.isclose(E, E_expected, rel_tol=KEPLER_REL_TOLERANCE)

    def test_earth_eccentricity(self):
        """Earth's eccentricity (e ≈ 0.0167) must converge."""
        M = math.radians(45)
        e = 0.0167
        E = kepler_solve(M, e)
        # Check Kepler's equation: M = E - e*sin(E)
        assert math.isclose(M, E - e * math.sin(E), abs_tol=1e-9)

    def test_kepler_equation_satisfied(self):
        """For any valid M and e, E - e*sin(E) must equal M."""
        test_cases = [
            (math.radians(10), 0.1),
            (math.radians(90), 0.3),
            (math.radians(180), 0.5),
            (math.radians(270), 0.2),
        ]
        for M, e in test_cases:
            E = kepler_solve(M, e)
            assert math.isclose(E - e * math.sin(E), M, abs_tol=1e-9), \
                f"Kepler's equation not satisfied for M={M}, e={e}"

    def test_eccentricity_zero_invalid(self):
        with pytest.raises(ValueError):
            kepler_solve(math.radians(30), 0)

    def test_eccentricity_one_invalid(self):
        with pytest.raises(ValueError):
            kepler_solve(math.radians(30), 1)

    def test_eccentricity_above_one_invalid(self):
        with pytest.raises(ValueError):
            kepler_solve(math.radians(30), 1.5)

    def test_eccentricity_negative_invalid(self):
        with pytest.raises(ValueError):
            kepler_solve(math.radians(30), -0.1)

    def test_returns_float(self):
        E = kepler_solve(math.radians(45), 0.1)
        assert isinstance(E, float)


# ════════════════════════════════════════════════════════════════════════════════
# Altitude Calculations
# ════════════════════════════════════════════════════════════════════════════════

class TestCalcAltitude:

    def test_latitude_0_declination_0_shadow_1(self):
        """At equator with sun at equinox, shadow_factor=1 → alt = 45°."""
        alt = calc_altitude(1, 0, 0)
        assert math.isclose(alt, math.pi / 4, rel_tol=ALTITUDE_REL_TOLERANCE)

    def test_latitude_0_declination_0_shadow_2(self):
        """shadow_factor=2 at equator/equinox → alt = atan(1/2) ≈ 0.4636 rad."""
        alt = calc_altitude(2, 0, 0)
        assert math.isclose(alt, 0.463648, rel_tol=ALTITUDE_REL_TOLERANCE)

    def test_latitude_equals_declination_shadow_1(self):
        """When latitude == declination, sun at zenith → shadow at lat=20°, decl=20° same as lat=0."""
        lat = 20
        decl = math.radians(lat)
        alt = calc_altitude(1, decl, lat)
        assert math.isclose(alt, math.pi / 4, rel_tol=ALTITUDE_REL_TOLERANCE)

    def test_shadow_factor_adds_to_zenith(self):
        """Total shadow = zenith_shadow + shadow_factor."""
        latitude = 20
        declination = 0
        phi = math.radians(latitude)
        shadow_factor_zenith = abs(math.tan(phi - declination))
        for sf in (1, 2):
            alt = calc_altitude(sf, declination, latitude)
            total = 1 / math.tan(alt)
            assert math.isclose(total, shadow_factor_zenith + sf, rel_tol=ALTITUDE_REL_TOLERANCE)

    def test_negative_latitude(self):
        """Southern hemisphere: should still compute valid altitude."""
        latitude = -20
        declination = 0
        phi = math.radians(latitude)
        shadow_factor_zenith = abs(math.tan(phi - declination))
        alt = calc_altitude(1, declination, latitude)
        total = 1 / math.tan(alt)
        assert math.isclose(total, shadow_factor_zenith + 1, rel_tol=ALTITUDE_REL_TOLERANCE)

    def test_returns_positive_altitude(self):
        """calc_altitude always returns a positive value (above horizon)."""
        for lat in (-30, 0, 30, 60):
            for sf in (1, 2):
                alt = calc_altitude(sf, math.radians(lat * 0.3), lat)
                assert alt > 0


# ════════════════════════════════════════════════════════════════════════════════
# Timedelta at Altitude
# ════════════════════════════════════════════════════════════════════════════════

class TestTimedeltaAtAltitude:

    def test_returns_timedelta(self):
        T = timedelta_at_altitude(math.pi / 4, 0, 0)
        assert isinstance(T, dt.timedelta)

    def test_non_negative(self):
        T = timedelta_at_altitude(math.pi / 4, 0, 0)
        assert T >= dt.timedelta()

    def test_at_most_12_hours(self):
        """Offset from zenith must be ≤ 12 hours."""
        T = timedelta_at_altitude(math.pi / 4, 0, 0)
        assert T <= dt.timedelta(hours=12)

    def test_higher_altitude_less_time(self):
        """Higher sun → closer to zenith → smaller timedelta."""
        T_high = timedelta_at_altitude(math.pi / 3, 0, 0)   # 60°
        T_low  = timedelta_at_altitude(math.pi / 6, 0, 0)   # 30°
        assert T_high < T_low

    def test_sun_never_reaches_altitude_raises(self):
        """If numerically impossible (cos > 1), ValueError raised."""
        with pytest.raises(ValueError, match="Sun does not reach altitude"):
            # Near-polar latitude, steep altitude in winter: sun can't reach π/2
            timedelta_at_altitude(math.pi / 2, math.radians(-23), 80)


# ════════════════════════════════════════════════════════════════════════════════
# Zenith Time
# ════════════════════════════════════════════════════════════════════════════════

class TestTimeZenith:

    def _verify_zenith(self, date_val: dt.date, longitude: float):
        """Helper: check Kepler's equation is satisfied at the found zenith."""
        zenith = time_zenith(date_val, longitude)
        utc_noon = dt.datetime(date_val.year, date_val.month, date_val.day, 12, tzinfo=dt.timezone.utc)
        eot, _ = eot_decl(zenith)
        zenith_calc = utc_noon - dt.timedelta(hours=longitude / 15) - eot
        assert math.isclose((zenith_calc - zenith).total_seconds(), 0, abs_tol=TIME_ABS_TOLERANCE)

    def _verify_same_day(self, date_val: dt.date, longitude: float):
        zenith = time_zenith(date_val, longitude)
        utc_noon = dt.datetime(date_val.year, date_val.month, date_val.day, 12, tzinfo=dt.timezone.utc)
        offset_hours = (zenith - utc_noon).total_seconds() / 3600
        assert -12 < offset_hours < 12

    def test_greenwich_meridian(self):
        date_val = dt.date(2000, 1, 1)
        self._verify_zenith(date_val, 0)
        self._verify_same_day(date_val, 0)

    def test_longitude_179_east(self):
        date_val = dt.date(2000, 1, 1)
        self._verify_zenith(date_val, 179)
        self._verify_same_day(date_val, 179)

    def test_longitude_179_west(self):
        date_val = dt.date(2000, 1, 1)
        self._verify_zenith(date_val, -179)
        self._verify_same_day(date_val, -179)

    def test_cairo_longitude(self):
        """Cairo (31.2357° E) should have zenith near 11:53 UTC."""
        date_val = dt.date(2025, 1, 1)
        self._verify_zenith(date_val, 31.2357)
        self._verify_same_day(date_val, 31.2357)

    def test_returns_utc_aware_datetime(self):
        zenith = time_zenith(dt.date(2023, 6, 15), 0)
        assert zenith.tzinfo == dt.timezone.utc


# ════════════════════════════════════════════════════════════════════════════════
# Time at Altitude
# ════════════════════════════════════════════════════════════════════════════════

class TestTimeAltitude:

    def _verify_time_altitude(self, date_val, latitude, longitude, altitude, rising):
        zenith = time_zenith(date_val, longitude)
        t = time_altitude(zenith, altitude, latitude, rising)
        _, declination = eot_decl(t)
        T = timedelta_at_altitude(altitude, declination, latitude)
        if rising:
            expected = zenith - T
        else:
            expected = zenith + T
        assert math.isclose((expected - t).total_seconds(), 0, abs_tol=TIME_ABS_TOLERANCE)

    def test_equator_rising(self):
        self._verify_time_altitude(dt.date(2000, 1, 1), 0, 0, math.pi / 4, True)

    def test_equator_setting(self):
        self._verify_time_altitude(dt.date(2000, 1, 1), 0, 0, math.pi / 4, False)

    def test_southern_latitude_rising(self):
        self._verify_time_altitude(dt.date(2000, 1, 1), -60, 150, math.pi / 6, True)

    def test_southern_latitude_setting(self):
        self._verify_time_altitude(dt.date(2000, 1, 1), -60, 150, math.pi / 6, False)

    def test_rising_before_zenith(self):
        """Rising time must be before zenith."""
        zenith = time_zenith(dt.date(2023, 6, 15), 31.2357)
        t_rising = time_altitude(zenith, -math.radians(0.833), 30.0444, True)
        assert t_rising < zenith

    def test_setting_after_zenith(self):
        """Setting time must be after zenith."""
        zenith = time_zenith(dt.date(2023, 6, 15), 31.2357)
        t_setting = time_altitude(zenith, -math.radians(0.833), 30.0444, False)
        assert t_setting > zenith

    def test_sunrise_before_sunset_cairo(self):
        """Sunrise must come before sunset in Cairo."""
        zenith = time_zenith(dt.date(2025, 1, 1), 31.2357)
        sunrise = time_altitude(zenith, -math.radians(0.833), 30.0444, True)
        sunset  = time_altitude(zenith, -math.radians(0.833), 30.0444, False)
        assert sunrise < sunset


# ════════════════════════════════════════════════════════════════════════════════
# Time Shadow Factor (Asr)
# ════════════════════════════════════════════════════════════════════════════════

class TestTimeShadowFactor:

    def _verify_shadow(self, date_val, latitude, longitude, shadow_factor, rising):
        zenith = time_zenith(date_val, longitude)
        t = time_shadow_factor(zenith, shadow_factor, latitude, rising)
        _, declination = eot_decl(t)
        altitude = calc_altitude(shadow_factor, declination, latitude)
        T = timedelta_at_altitude(altitude, declination, latitude)
        expected = zenith - T if rising else zenith + T
        assert math.isclose((expected - t).total_seconds(), 0, abs_tol=TIME_ABS_TOLERANCE)

    def test_standard_asr_shadow_1(self):
        self._verify_shadow(dt.date(2000, 1, 1), -60, 150, 1, False)

    def test_hanafi_asr_shadow_2(self):
        self._verify_shadow(dt.date(2000, 1, 1), -60, 150, 2, False)

    def test_hanafi_asr_after_standard_asr(self):
        """Hanafi Asr (shadow=2) must always be after Standard Asr (shadow=1)."""
        date_val = dt.date(2025, 6, 15)
        zenith = time_zenith(date_val, 31.2357)
        asr_standard = time_shadow_factor(zenith, 1, 30.0444, False)
        asr_hanafi   = time_shadow_factor(zenith, 2, 30.0444, False)
        assert asr_hanafi > asr_standard

    def test_asr_after_zenith(self):
        """Asr (rising=False) must always be after zenith."""
        zenith = time_zenith(dt.date(2025, 3, 20), 31.2357)
        asr = time_shadow_factor(zenith, 1, 30.0444, False)
        assert asr > zenith

    def test_cairo_asr_reasonable_time(self):
        """Cairo Asr should be between 12:00 and 19:00 UTC."""
        zenith = time_zenith(dt.date(2025, 6, 15), 31.2357)
        asr = time_shadow_factor(zenith, 1, 30.0444, False)
        hour_utc = asr.hour + asr.minute / 60
        assert 12 <= hour_utc <= 19