from fastapi import APIRouter, Query, HTTPException, Request
from datetime import date as _date, datetime
from typing import Optional
from base.base_module import BaseModule

from .core.methods import PrayerTimes, CalculationMethod, AsrMethod, AVAILABLE_METHODS


class Module(BaseModule):
    name = "prayer_times"
    version = "1.0.0"
    dependencies = []

    def register_routes(self, router: APIRouter):
        router.add_api_route(
            "/prayer-times",
            self.get_times,
            methods=["GET"],
            summary="Prayer times by coordinates",
            tags=["Prayer Times"],
        )
        router.add_api_route(
            "/prayer/next",
            self.get_next_prayer,
            methods=["GET"],
            summary="Next upcoming prayer",
            tags=["Prayer Times"],
        )
        router.add_api_route(
            "/prayer/month",
            self.get_month,
            methods=["GET"],
            summary="Prayer times for a full month",
            tags=["Prayer Times"],
        )
        router.add_api_route(
            "/prayer/methods",
            self.get_methods,
            methods=["GET"],
            summary="List available calculation methods",
            tags=["Prayer Times"],
        )
        # Backward-compat alias
        router.add_api_route(
            "/prayer-times/methods",
            self.get_methods,
            methods=["GET"],
            include_in_schema=False,
            tags=["Prayer Times"],
        )

    # ── Shared helpers ────────────────────────────────────────────────────────

    def _resolve_tz(self, timezone: str):
        try:
            import pytz
            return pytz.timezone(timezone)
        except Exception:
            import pytz
            return pytz.UTC

    def _resolve_coords(self, lat, latitude, lng, longitude):
        """Accept both short (lat/lng) and long (latitude/longitude) param names."""
        resolved_lat = lat if lat is not None else latitude
        resolved_lng = lng if lng is not None else longitude
        if resolved_lat is None:
            raise HTTPException(422, detail="lat or latitude is required")
        if resolved_lng is None:
            raise HTTPException(422, detail="lng or longitude is required")
        return resolved_lat, resolved_lng

    def _resolve_date(self, date_str: Optional[str]) -> _date:
        if date_str is None:
            return _date.today()
        try:
            return _date.fromisoformat(date_str)
        except (ValueError, AttributeError):
            raise HTTPException(400, detail=f"Invalid date: '{date_str}'. Use YYYY-MM-DD.")

    def _validate_method(self, method: str) -> str:
        method = method.upper()
        if method not in AVAILABLE_METHODS:
            raise HTTPException(
                400,
                detail={"error": f"Unknown method: {method}", "available": AVAILABLE_METHODS},
            )
        return method

    def _validate_asr(self, asr: str) -> AsrMethod:
        asr = asr.upper()
        try:
            return AsrMethod[asr]
        except KeyError:
            raise HTTPException(400, detail=f"Unknown asr method: {asr}. Use STANDARD or HANAFI.")

    def _labels(self, lang: str) -> dict:
        return {
            "en": {
                "fajr": "Fajr", "sunrise": "Sunrise", "dhuhr": "Dhuhr",
                "asr": "Asr", "maghrib": "Maghrib", "isha": "Isha",
            },
            "ar": {
                "fajr": "الفجر", "sunrise": "الشروق", "dhuhr": "الظهر",
                "asr": "العصر", "maghrib": "المغرب", "isha": "العشاء",
            },
        }.get(lang, {"fajr": "Fajr", "sunrise": "Sunrise", "dhuhr": "Dhuhr",
                     "asr": "Asr", "maghrib": "Maghrib", "isha": "Isha"})

    # ── Endpoints ─────────────────────────────────────────────────────────────

    async def get_times(
        self,
        request: Request,
        # Short names (picker.html) — kept for backward compat
        lat: Optional[float] = Query(None, ge=-90,  le=90,  description="Latitude (short)"),
        lng: Optional[float] = Query(None, ge=-180, le=180, description="Longitude (short)"),
        # Long names (test suite)
        latitude:  Optional[float] = Query(None, ge=-90,  le=90,  description="Latitude (long)"),
        longitude: Optional[float] = Query(None, ge=-180, le=180, description="Longitude (long)"),
        timezone: str          = Query("UTC",      description="IANA timezone, e.g. Africa/Cairo"),
        method:   str          = Query("EGYPT",    description=f"Calculation method: {', '.join(AVAILABLE_METHODS)}"),
        asr:      str          = Query("STANDARD", description="Asr method: STANDARD or HANAFI"),
        lang:     str          = Query("en",       description="Language: en or ar"),
        date:     Optional[str] = Query(None,      description="Date in YYYY-MM-DD format (default: today)"),
    ):
        lang = self.get_lang(request, lang)
        resolved_lat, resolved_lng = self._resolve_coords(lat, latitude, lng, longitude)
        method    = self._validate_method(method)
        asr_method = self._validate_asr(asr)
        target_date = self._resolve_date(date)
        tz_obj    = self._resolve_tz(timezone)
        lbl       = self._labels(lang)

        try:
            pt    = PrayerTimes(CalculationMethod[method], asr_method)
            times = pt.calc_times(target_date, tz_obj, longitude=resolved_lng, latitude=resolved_lat)
        except Exception as exc:
            raise HTTPException(500, detail=str(exc))

        prayers_order = ["fajr", "dhuhr", "asr", "maghrib", "isha"]

        return {
            "date":     target_date.isoformat(),
            "method":   method,
            "asr":      asr.upper(),
            "timezone": timezone,
            "location": {"lat": round(resolved_lat, 6), "lng": round(resolved_lng, 6)},
            "sunrise":  times["sunrise"].strftime("%H:%M"),
            "prayers": [
                {"key": key, "name": lbl[key], "time": times[key].strftime("%H:%M")}
                for key in prayers_order
            ],
        }

    async def get_next_prayer(
        self,
        request: Request,
        lat:       Optional[float] = Query(None, ge=-90,  le=90),
        lng:       Optional[float] = Query(None, ge=-180, le=180),
        latitude:  Optional[float] = Query(None, ge=-90,  le=90),
        longitude: Optional[float] = Query(None, ge=-180, le=180),
        timezone:  str = Query("UTC"),
        method:    str = Query("EGYPT"),
        asr:       str = Query("STANDARD"),
        lang:      str = Query("en"),
    ):
        lang = self.get_lang(request, lang)
        resolved_lat, resolved_lng = self._resolve_coords(lat, latitude, lng, longitude)
        method     = self._validate_method(method)
        asr_method = self._validate_asr(asr)
        tz_obj     = self._resolve_tz(timezone)
        lbl        = self._labels(lang)
        today      = _date.today()

        try:
            pt    = PrayerTimes(CalculationMethod[method], asr_method)
            times = pt.calc_times(today, tz_obj, longitude=resolved_lng, latitude=resolved_lat)
        except Exception as exc:
            raise HTTPException(500, detail=str(exc))

        import pytz
        now = datetime.now(tz_obj if hasattr(tz_obj, "localize") else pytz.UTC)

        prayers_order = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
        next_prayer   = None

        for key in prayers_order:
            if times[key] > now:
                next_prayer = {
                    "key":      key,
                    "name":     lbl[key],
                    "time":     times[key].strftime("%H:%M"),
                    "tomorrow": False,
                }
                break

        if next_prayer is None:
            # Past Isha — next is Fajr tomorrow
            from datetime import timedelta
            tomorrow = today + timedelta(days=1)
            times_tomorrow = pt.calc_times(tomorrow, tz_obj, longitude=resolved_lng, latitude=resolved_lat)
            next_prayer = {
                "key":      "fajr",
                "name":     lbl["fajr"],
                "time":     times_tomorrow["fajr"].strftime("%H:%M"),
                "tomorrow": True,
            }

        return {
            "date":         today.isoformat(),
            "next_prayer":  next_prayer,
            "time":         next_prayer["time"],
        }

    async def get_month(
        self,
        request: Request,
        lat:       Optional[float] = Query(None, ge=-90,  le=90),
        lng:       Optional[float] = Query(None, ge=-180, le=180),
        latitude:  Optional[float] = Query(None, ge=-90,  le=90),
        longitude: Optional[float] = Query(None, ge=-180, le=180),
        timezone:  str = Query("UTC"),
        method:    str = Query("EGYPT"),
        asr:       str = Query("STANDARD"),
        lang:      str = Query("en"),
        month:     int = Query(..., ge=1, le=12,   description="Month (1–12)"),
        year:      int = Query(..., ge=1900, le=2100, description="Year"),
    ):
        import calendar

        lang = self.get_lang(request, lang)
        resolved_lat, resolved_lng = self._resolve_coords(lat, latitude, lng, longitude)
        method     = self._validate_method(method)
        asr_method = self._validate_asr(asr)
        tz_obj     = self._resolve_tz(timezone)
        lbl        = self._labels(lang)
        prayers_order = ["fajr", "dhuhr", "asr", "maghrib", "isha"]

        try:
            pt           = PrayerTimes(CalculationMethod[method], asr_method)
            days_in_month = calendar.monthrange(year, month)[1]
            days = []
            for day in range(1, days_in_month + 1):
                d     = _date(year, month, day)
                times = pt.calc_times(d, tz_obj, longitude=resolved_lng, latitude=resolved_lat)
                days.append({
                    "date":    d.isoformat(),
                    "sunrise": times["sunrise"].strftime("%H:%M"),
                    "prayers": [
                        {"key": key, "name": lbl[key], "time": times[key].strftime("%H:%M")}
                        for key in prayers_order
                    ],
                })
        except Exception as exc:
            raise HTTPException(500, detail=str(exc))

        return {
            "month":    month,
            "year":     year,
            "method":   method,
            "timezone": timezone,
            "location": {"lat": round(resolved_lat, 6), "lng": round(resolved_lng, 6)},
            "days":     days,
        }

    async def get_methods(self, request: Request):
        return {
            "methods": AVAILABLE_METHODS,
            "descriptions": {
                "MWL":     "Muslim World League",
                "ISNA":    "Islamic Society of North America",
                "EGYPT":   "Egyptian General Authority of Survey",
                "MAKKAH":  "Umm al-Qura, Makkah (90 min after Maghrib for Isha)",
                "KARACHI": "University of Islamic Sciences, Karachi",
                "TEHRAN":  "Institute of Geophysics, Tehran",
                "JAFARI":  "Shia Ithna-Ashari, Leva Research Institute, Qum",
            },
        }