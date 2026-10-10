from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, date
from typing import Optional
import pytz

from base.base_module import BaseModule
from modules.prayer_times.core.methods import PrayerTimes, CalculationMethod, AsrMethod


class Module(BaseModule):
    name = "ramadan"
    version = "1.0.0"
    dependencies = ["prayer_times"]

    def register_routes(self, router: APIRouter):
        router.add_api_route("/ramadan", self.get_ramadan_times, methods=["GET"])
        router.add_api_route("/ramadan/calendar", self.get_ramadan_calendar, methods=["GET"])

    async def get_ramadan_times(
        self,
        latitude: float = Query(..., ge=-90, le=90),
        longitude: float = Query(..., ge=-180, le=180),
        year: int = Query(None, description="Hijri year (default: current)"),
        timezone: str = Query("Africa/Cairo"),
        method: str = Query("EGYPT"),
        lang: str = Query("en")
    ):
        try:
            hijri_year = year or self._get_current_hijri_year()
            ramadan_days = self._get_ramadan_days(hijri_year)

            if not ramadan_days:
                raise HTTPException(404, "Could not calculate Ramadan dates")

            first_day = ramadan_days[0]
            last_day = ramadan_days[-1]

            first_times = self._calculate(latitude, longitude, first_day, timezone, method)
            last_times = self._calculate(latitude, longitude, last_day, timezone, method)

            return {
                "hijri_year": hijri_year,
                "ramadan": {
                    "start": first_day.isoformat(),
                    "end": last_day.isoformat(),
                    "total_days": len(ramadan_days),
                },
                "first_day": {
                    "date": first_day.isoformat(),
                    "suhoor": self.translate({"en": "Suhoor ends", "ar": "نهاية السحور"}, lang),
                    "suhoor_time": first_times["fajr"].strftime("%H:%M"),
                    "iftar": self.translate({"en": "Iftar", "ar": "الإفطار"}, lang),
                    "iftar_time": first_times["maghrib"].strftime("%H:%M"),
                },
                "last_day": {
                    "date": last_day.isoformat(),
                    "suhoor_time": last_times["fajr"].strftime("%H:%M"),
                    "iftar_time": last_times["maghrib"].strftime("%H:%M"),
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Error: {str(e)}")

    async def get_ramadan_calendar(
        self,
        latitude: float = Query(..., ge=-90, le=90),
        longitude: float = Query(..., ge=-180, le=180),
        year: int = Query(None, description="Hijri year (default: current)"),
        timezone: str = Query("Africa/Cairo"),
        method: str = Query("EGYPT"),
        lang: str = Query("en")
    ):
        try:
            hijri_year = year or self._get_current_hijri_year()
            ramadan_days = self._get_ramadan_days(hijri_year)

            if not ramadan_days:
                raise HTTPException(404, "Could not calculate Ramadan dates")

            calendar = []
            for i, day in enumerate(ramadan_days, 1):
                times = self._calculate(latitude, longitude, day, timezone, method)
                calendar.append({
                    "day": i,
                    "date": day.isoformat(),
                    "suhoor": times["fajr"].strftime("%H:%M"),
                    "fajr": times["fajr"].strftime("%H:%M"),
                    "dhuhr": times["dhuhr"].strftime("%H:%M"),
                    "asr": times["asr"].strftime("%H:%M"),
                    "iftar": times["maghrib"].strftime("%H:%M"),
                    "maghrib": times["maghrib"].strftime("%H:%M"),
                    "isha": times["isha"].strftime("%H:%M"),
                })

            return {
                "hijri_year": hijri_year,
                "total_days": len(calendar),
                "location": {"lat": latitude, "lng": longitude},
                "calendar": calendar
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Error: {str(e)}")

    def _get_current_hijri_year(self) -> int:
        from hijridate import Gregorian
        today = date.today()
        hijri = Gregorian(today.year, today.month, today.day).to_hijri()
        return hijri.year

    def _get_ramadan_days(self, hijri_year: int) -> list:
        from hijridate import Hijri
        days = []
        for day in range(1, 31):
            try:
                hijri = Hijri(hijri_year, 9, day)
                greg = hijri.to_gregorian()
                days.append(date(greg.year, greg.month, greg.day))
            except Exception:
                break
        return days

    def _calculate(self, lat, lng, prayer_date, timezone_str, method_str):
        try:
            tz = pytz.timezone(timezone_str)
            pt = PrayerTimes(CalculationMethod[method_str], AsrMethod.STANDARD)
            return pt.calc_times(prayer_date, tz, lng, lat)
        except KeyError:
            raise HTTPException(400, f"Invalid method: {method_str}")
        except Exception as e:
            raise HTTPException(500, f"Calculation error: {str(e)}")
