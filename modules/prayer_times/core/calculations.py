import datetime as dt
from typing import Callable
import math


def eot_decl(time: dt.datetime) -> "tuple[dt.timedelta, float]":
    utc = dt.timezone.utc
    epoch = dt.datetime(2000, 1, 1, 12, tzinfo=utc)
    days_since_epoch = (time - epoch).total_seconds() / 60 / 60 / 24
    y100 = days_since_epoch / 36525
    e = 1.6709e-2 - 4.193e-5 * y100 - 1.26e-7 * y100 ** 2
    lam_p = math.radians(282.93807 + 1.7195 * y100 + 3.025e-4 * y100 ** 2)
    epsilon = math.radians(23.4393 - 0.013 * y100 - 2e-7 * y100 ** 2 + 5e-7 * y100 ** 3)
    MD = 6.24004077
    TY = 365.2596358
    D = days_since_epoch % TY
    M = MD + 2 * math.pi * D / TY
    M = M % (2 * math.pi)
    E = kepler_solve(M, e)
    nu = math.acos((math.cos(E) - e) / (1 - e * math.cos(E)))
    if E > math.pi:
        nu = 2 * math.pi - nu
    lam = nu + lam_p
    lam = lam % (2 * math.pi)
    if math.isclose(math.cos(lam), 0):
        alpha = lam
    else:
        alpha = math.atan(math.cos(epsilon) * math.tan(lam))
        if lam < math.pi / 2:
            assert 0 <= alpha < math.pi / 2
        elif lam < math.pi * 3 / 2:
            alpha += math.pi
            assert math.pi / 2 <= alpha < math.pi * 3 / 2
        else:
            alpha += 2 * math.pi
            assert math.pi * 3 / 2 <= alpha < 2 * math.pi
    eot_rad = M + lam_p - alpha
    if eot_rad > math.pi:
        eot_rad -= 2 * math.pi
    eot_min = eot_rad / (2 * math.pi) * 60 * 24
    eot = dt.timedelta(minutes=eot_min)
    decl = math.asin(math.sin(epsilon) * math.sin(lam))
    return eot, decl


def kepler_solve(M: float, e: float) -> float:
    if not 0 < e < 1:
        raise ValueError("Eccentricity of elliptical orbit required in range (0, 1)")
    E = M
    while not math.isclose(M, E - e * math.sin(E)):
        E = E - (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
    return E


def calc_altitude(shadow_factor: float, declination: float, latitude: float) -> float:
    phi = math.radians(latitude)
    delta = declination
    shadow_factor_zenith = abs(math.tan(phi - delta))
    alt = math.atan(1 / (shadow_factor + shadow_factor_zenith))
    return alt


def timedelta_at_altitude(altitude: float, declination: float, latitude: float) -> dt.timedelta:
    alpha = altitude
    phi = math.radians(latitude)
    delta = declination
    numerator = math.sin(alpha) - math.sin(phi) * math.sin(delta)
    denominator = math.cos(phi) * math.cos(delta)
    cos_hour_rad = numerator / denominator
    if cos_hour_rad < -1 or cos_hour_rad > 1:
        raise ValueError("Sun does not reach altitude")
    hour_rad = math.acos(cos_hour_rad)
    hours = hour_rad / (2 * math.pi) * 24
    T = dt.timedelta(hours=hours)
    return T


def linear_interpolation(diff_function: Callable[[dt.datetime], dt.timedelta], guess1: dt.datetime, guess2: dt.datetime):
    if math.isclose((guess1 - guess2).total_seconds(), 0):
        raise ValueError("guess1 and guess2 need to be different")
    if guess2 < guess1:
        guess1, guess2 = guess2, guess1
    diff1 = diff_function(guess1)
    diff2 = diff_function(guess2)
    while not math.isclose((guess1 - guess2).total_seconds(), 0):
        guess3 = guess1 - diff1 * ((guess2 - guess1) / (diff2 - diff1))
        diff3 = diff_function(guess3)
        guess1, diff1 = guess2, diff2
        guess2, diff2 = guess3, diff3
    return guess1


def time_zenith(date: dt.date, longitude: float) -> dt.datetime:
    utc_noon = dt.datetime(date.year, date.month, date.day, 12, tzinfo=dt.timezone.utc)
    time_zenith_approx = utc_noon - dt.timedelta(hours=longitude/15)
    def calc_difference(guess: dt.datetime) -> dt.timedelta:
        eot, _ = eot_decl(guess)
        actual = utc_noon - dt.timedelta(hours=longitude/15) - eot
        return actual - guess
    guess1 = time_zenith_approx - dt.timedelta(minutes=20)
    guess2 = time_zenith_approx + dt.timedelta(minutes=20)
    return linear_interpolation(calc_difference, guess1, guess2)


def time_altitude(zenith: dt.datetime, altitude: float, latitude: float, rising: bool) -> dt.datetime:
    def calc_difference(guess: dt.datetime) -> dt.timedelta:
        _, declination = eot_decl(guess)
        T = timedelta_at_altitude(altitude, declination, latitude)
        actual = zenith - T if rising else zenith + T
        return actual - guess
    if rising:
        guess1 = zenith - dt.timedelta(hours=12)
        guess2 = zenith
    else:
        guess1 = zenith
        guess2 = zenith + dt.timedelta(hours=12)
    return linear_interpolation(calc_difference, guess1, guess2)


def time_shadow_factor(zenith: dt.datetime, shadow_factor: float, latitude: float, rising: bool) -> dt.datetime:
    def calc_difference(guess: dt.datetime) -> dt.timedelta:
        _, declination = eot_decl(guess)
        altitude = calc_altitude(shadow_factor, declination, latitude)
        T = timedelta_at_altitude(altitude, declination, latitude)
        actual = zenith - T if rising else zenith + T
        return actual - guess
    if rising:
        guess1 = zenith - dt.timedelta(hours=12)
        guess2 = zenith
    else:
        guess1 = zenith
        guess2 = zenith + dt.timedelta(hours=12)
    return linear_interpolation(calc_difference, guess1, guess2)
