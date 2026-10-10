from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, date
from typing import Optional
import pytz

from base.base_module import BaseModule
from modules.prayer_times.core.methods import PrayerTimes, CalculationMethod, AsrMethod


class Module(BaseModule):
    name = "prayer_times"
    version = "1.0.0"
    dependencies = []

    def register_routes(self, router: APIRouter):
        router.add_api_route("/prayer-times", self.get_prayer_times, methods=["GET"])
        router.add_api_route("/prayer/next", self.get_next_prayer, methods=["GET"])
        router.add_api_route("/prayer/month", self.get_prayer_month, methods=["GET"])
        router.add_api_route("/prayer/methods", self.get_methods, methods=["GET"])

    async def get_prayer_times(
        self,
        latitude: float = Query(..., ge=-90, le=90),
        longitude: float = Query(..., ge=-180, le=180),
        date: Optional[str] = Query(None, description="YYYY-MM-DD (default: today)"),
        timezone: str = Query("Africa/Cairo"),
        method: str = Query("EGYPT"),
        lang: str = Query("en", description="Language: en or ar")
    ):
        prayer_date = self._parse_date(date)
        times = self._calculate(latitude, longitude, prayer_date, timezone, method)
        response = {
            "date": prayer_date.isoformat(),
            "location": {"lat": latitude, "lng": longitude},
            "timezone": timezone,
            "method": method,
            "sunrise": times["sunrise"].strftime("%H:%M"),
            "prayers": [
                {"name": self.translate({"en": "Fajr", "ar": "الفجر"}, lang), "time": times["fajr"].strftime("%H:%M")},
                {"name": self.translate({"en": "Dhuhr", "ar": "الظهر"}, lang), "time": times["dhuhr"].strftime("%H:%M")},
                {"name": self.translate({"en": "Asr", "ar": "العصر"}, lang), "time": times["asr"].strftime("%H:%M")},
                {"name": self.translate({"en": "Maghrib", "ar": "المغرب"}, lang), "time": times["maghrib"].strftime("%H:%M")},
                {"name": self.translate({"en": "Isha", "ar": "العشاء"}, lang), "time": times["isha"].strftime("%H:%M")},
            ]
        }
        self.logger.info(f"Prayer times requested: {latitude},{longitude} [{method}]")
        return response

    async def get_next_prayer(
        self,
        latitude: float = Query(..., ge=-90, le=90),
        longitude: float = Query(..., ge=-180, le=180),
        timezone: str = Query("Africa/Cairo"),
        method: str = Query("EGYPT"),
        lang: str = Query("en")
    ):
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        times = self._calculate(latitude, longitude, now.date(), timezone, method)
        prayer_names = {
            "fajr": {"en": "Fajr", "ar": "الفجر"},
            "dhuhr": {"en": "Dhuhr", "ar": "الظهر"},
            "asr": {"en": "Asr", "ar": "العصر"},
            "maghrib": {"en": "Maghrib", "ar": "المغرب"},
            "isha": {"en": "Isha", "ar": "العشاء"},
        }
        for prayer in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
            prayer_time = times[prayer]
            if prayer_time > now:
                diff = prayer_time - now
                minutes = int(diff.total_seconds() / 60)
                return {
                    "next_prayer": self.translate(prayer_names[prayer], lang),
                    "time": prayer_time.strftime("%H:%M"),
                    "in_minutes": minutes
                }
        return {"next_prayer": self.translate({"en": "Fajr", "ar": "الفجر"}, lang), "message": "Next prayer is tomorrow's Fajr"}

    async def get_prayer_month(
        self,
        latitude: float = Query(..., ge=-90, le=90),
        longitude: float = Query(..., ge=-180, le=180),
        month: int = Query(..., ge=1, le=12),
        year: int = Query(..., ge=2000, le=2100),
        timezone: str = Query("Africa/Cairo"),
        method: str = Query("EGYPT")
    ):
        import calendar
        num_days = calendar.monthrange(year, month)[1]
        days = []
        for day in range(1, num_days + 1):
            current_date = date(year, month, day)
            times = self._calculate(latitude, longitude, current_date, timezone, method)
            days.append({
                "date": current_date.isoformat(),
                "fajr": times["fajr"].strftime("%H:%M"),
                "sunrise": times["sunrise"].strftime("%H:%M"),
                "dhuhr": times["dhuhr"].strftime("%H:%M"),
                "asr": times["asr"].strftime("%H:%M"),
                "maghrib": times["maghrib"].strftime("%H:%M"),
                "isha": times["isha"].strftime("%H:%M"),
            })
        return {"month": month, "year": year, "location": {"lat": latitude, "lng": longitude}, "days": days}

    async def get_methods(self):
        return {
            "methods": [
                {"key": "EGYPT", "name": "Egyptian General Authority of Survey"},
                {"key": "MWL", "name": "Muslim World League"},
                {"key": "ISNA", "name": "Islamic Society of North America"},
                {"key": "MAKKAH", "name": "Umm al-Qura University, Makkah"},
                {"key": "KARACHI", "name": "University of Islamic Sciences, Karachi"},
                {"key": "TEHRAN", "name": "Institute of Geophysics, University of Tehran"},
                {"key": "JAFARI", "name": "Shia Ithna Ashari, Leva Research Institute, Qum"},
            ]
        }

    def _parse_date(self, date_str: Optional[str]):
        if date_str:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")
        return datetime.now().date()

    def _calculate(self, lat, lng, prayer_date, timezone_str, method_str):
        try:
            tz = pytz.timezone(timezone_str)
            pt = PrayerTimes(CalculationMethod[method_str], AsrMethod.STANDARD)
            return pt.calc_times(prayer_date, tz, lng, lat)
        except KeyError:
            raise HTTPException(400, f"Invalid method: {method_str}")
        except Exception as e:
            raise HTTPException(500, f"Calculation error: {str(e)}")
