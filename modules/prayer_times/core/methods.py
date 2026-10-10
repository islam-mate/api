from enum import Enum, auto, unique
import datetime as dt
import math

from .calculations import time_zenith, time_altitude, time_shadow_factor


@unique
class CalculationMethod(Enum):
    ISNA = auto()
    MWL = auto()
    EGYPT = auto()
    TEHRAN = auto()
    JAFARI = auto()
    MAKKAH = auto()
    KARACHI = auto()


@unique
class AsrMethod(Enum):
    STANDARD = auto()
    HANAFI = auto()


class GeneralMethod:
    def __init__(self, fajr_altitude_deg: float, isha_altitude_deg: float, asr_method: AsrMethod = AsrMethod.STANDARD):
        self.asr_method = asr_method
        if self.asr_method == AsrMethod.STANDARD:
            self.shadow_factor = 1
        elif self.asr_method == AsrMethod.HANAFI:
            self.shadow_factor = 2
        else:
            raise ValueError(f"Unknown AsrMethod {self.asr_method}")
        self.fajr_altitude = -math.radians(fajr_altitude_deg)
        self.isha_altitude = -math.radians(isha_altitude_deg)
        self.sunset_altitude = -math.radians(0.833)

    def calc_times(self, date: dt.date, timezone: dt.tzinfo, longitude: float, latitude: float) -> "dict[str, dt.datetime]":
        zenith = time_zenith(date, longitude)
        fajr = time_altitude(zenith, self.fajr_altitude, latitude, True)
        sunrise = time_altitude(zenith, self.sunset_altitude, latitude, True)
        asr = time_shadow_factor(zenith, self.shadow_factor, latitude, False)
        maghrib = time_altitude(zenith, self.sunset_altitude, latitude, False)
        isha = time_altitude(zenith, self.isha_altitude, latitude, False)
        times = {"fajr": fajr, "sunrise": sunrise, "dhuhr": zenith, "asr": asr, "maghrib": maghrib, "isha": isha}
        for name in times:
            times[name] = times[name].astimezone(timezone)
        return times


class TehranMethod(GeneralMethod):
    def __init__(self, asr_method: AsrMethod = AsrMethod.STANDARD):
        super().__init__(17.7, 14, asr_method=asr_method)

    def calc_times(self, date: dt.date, timezone: dt.tzinfo, longitude: float, latitude: float):
        times = super().calc_times(date, timezone, longitude, latitude)
        zenith = time_zenith(date, longitude)
        times["maghrib"] = time_altitude(zenith, -math.radians(4.5), latitude, rising=False).astimezone(timezone)
        return times


class JafariMethod(GeneralMethod):
    def __init__(self, asr_method: AsrMethod = AsrMethod.STANDARD):
        super().__init__(16, 14, asr_method=asr_method)

    def calc_times(self, date: dt.date, timezone: dt.tzinfo, longitude: float, latitude: float):
        times = super().calc_times(date, timezone, longitude, latitude)
        zenith = time_zenith(date, longitude)
        times["maghrib"] = time_altitude(zenith, -math.radians(4), latitude, rising=False).astimezone(timezone)
        return times


class MakkahMethod(GeneralMethod):
    def __init__(self, asr_method: AsrMethod = AsrMethod.STANDARD):
        try:
            import hijri_converter
        except ImportError:
            raise ImportError("Install hijri-converter to use MakkahMethod")
        super().__init__(18.5, 18.5, asr_method=asr_method)

    def calc_times(self, date: dt.date, timezone: dt.tzinfo, longitude: float, latitude: float):
        from hijri_converter import Gregorian
        times = super().calc_times(date, timezone, longitude, latitude)
        hijri_date = Gregorian(date.year, date.month, date.day).to_hijri()
        if hijri_date.month == 9:
            times["isha"] = times["maghrib"] + dt.timedelta(minutes=120)
        else:
            times["isha"] = times["maghrib"] + dt.timedelta(minutes=90)
        return times


def PrayerTimes(method=CalculationMethod.MWL, asr=AsrMethod.STANDARD) -> GeneralMethod:
    if method == CalculationMethod.ISNA:
        return GeneralMethod(15, 15, asr)
    elif method == CalculationMethod.MWL:
        return GeneralMethod(18, 17, asr)
    elif method == CalculationMethod.EGYPT:
        return GeneralMethod(19.5, 17.5, asr)
    elif method == CalculationMethod.KARACHI:
        return GeneralMethod(18, 18, asr)
    elif method == CalculationMethod.TEHRAN:
        return TehranMethod(asr)
    elif method == CalculationMethod.JAFARI:
        return JafariMethod(asr)
    elif method == CalculationMethod.MAKKAH:
        return MakkahMethod(asr)
    else:
        raise ValueError(f"Unknown CalculationMethod {method}")
