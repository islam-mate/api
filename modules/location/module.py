from fastapi import APIRouter, Query, Request
from base.base_module import BaseModule
import httpx
import yaml
from pathlib import Path

from .db import db_search, db_reverse_geocode
from .geocoding import nominatim_search, nominatim_reverse


LOCATION_CONFIG_PATH = Path("config/location.yaml")


class Module(BaseModule):
    name = "location"
    version = "2.0.0"
    dependencies = []

    def register_routes(self, router: APIRouter):
        router.add_api_route(
            "/location/detect",
            self.detect,
            methods=["GET"],
            summary="Detect location from IP",
            tags=["Location"]
        )
        router.add_api_route(
            "/location/search",
            self.search,
            methods=["GET"],
            summary="Search city by name",
            tags=["Location"]
        )
        router.add_api_route(
            "/location/auto",
            self.auto,
            methods=["GET"],
            summary="Smart location detection — GPS coords if provided, IP fallback",
            tags=["Location"]
        )
        router.add_api_route(
            "/location/config",
            self.config_view,
            methods=["GET"],
            summary="Location config — enabled methods and platform priorities",
            tags=["Location"]
        )
        router.add_api_route(
            "/prayer-times/auto",
            self.prayer_times_auto,
            methods=["GET"],
            summary="Auto prayer times from IP",
            tags=["Location"]
        )

    # ============================================
    # ENDPOINTS
    # ============================================

    async def detect(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)

        ip = request.headers.get("X-Forwarded-For")
        if ip:
            ip = ip.split(",")[0].strip()
        else:
            ip = request.client.host

        if ip in ("127.0.0.1", "::1", "localhost"):
            return {
                "ip": ip,
                "city": self.translate({"ar": "غير متاح محلياً", "en": "Not available locally"}, lang),
                "country": self.translate({"ar": "اختبار محلي", "en": "Local testing"}, lang),
                "latitude": None,
                "longitude": None,
                "timezone": None,
                "note": self.translate({
                    "ar": "لا يمكن كشف الموقع من localhost. أرسل latitude و longitude يدوياً.",
                    "en": "Cannot detect location from localhost. Pass latitude and longitude manually."
                }, lang)
            }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "status,message,country,city,lat,lon,timezone,query"},
                timeout=5.0
            )
            data = response.json()

        if data.get("status") != "success":
            return {
                "error": self.translate({
                    "ar": "فشل في كشف الموقع",
                    "en": "Failed to detect location"
                }, lang),
                "message": data.get("message", "Unknown error")
            }

        return {
            "ip": data.get("query"),
            "city": data.get("city"),
            "country": data.get("country"),
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
            "timezone": data.get("timezone"),
            "source": "ip-api",
            "accuracy": self.translate({
                "ar": "دقة المدينة (+/- 10-50 كم)",
                "en": "City-level accuracy (+/- 10-50 km)"
            }, lang),
            "note": self.translate({
                "ar": "الدقة كافية لاوقات الصلاة (فرق +/- 1-2 دقيقة مقبول)",
                "en": "Accuracy sufficient for prayer times (+/- 1-2 min difference accepted)"
            }, lang)
        }

    async def search(
        self,
        request: Request,
        q: str = Query(..., description="City name in Arabic or English"),
        lang: str = Query("en", description="Language: en or ar"),
        limit: int = Query(5, ge=1, le=10, description="Max results")
    ):
        lang = self.get_lang(request, lang)

        if not q or len(q.strip()) < 2:
            return {
                "error": self.translate({
                    "ar": "اكتب اسم المدينة (حرفان على الأقل)",
                    "en": "Enter city name (at least 2 characters)"
                }, lang)
            }

        # Step 1: local DB (fast, offline)
        results = db_search(q.strip(), limit)

        if results:
            cities = [
                {
                    "name": r["name"],
                    "name_local": r["name_local"],
                    "country": r["country"],
                    "governorate": r["governorate"],
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
                    "timezone": r["timezone"],
                    "source": "local_db",
                }
                for r in results
            ]
            return {"query": q, "total": len(cities), "source": "local_db", "results": cities}

        # Step 2: Nominatim fallback (online)
        self.logger.info(f"City '{q}' not in local DB, falling back to Nominatim")
        nom_results = await nominatim_search(q, lang, limit)

        if not nom_results:
            return {
                "query": q,
                "total": 0,
                "results": [],
                "message": self.translate({
                    "ar": "لم يتم العثور على نتائج",
                    "en": "No results found"
                }, lang)
            }

        return {
            "query": q,
            "total": len(nom_results),
            "source": "nominatim",
            "note": self.translate({
                "ar": "النتيجة من OpenStreetMap وتم تخزينها محلياً للاستخدام دون انترنت لاحقاً",
                "en": "Result from OpenStreetMap, cached locally for offline use"
            }, lang),
            "results": nom_results
        }

    async def auto(
        self,
        request: Request,
        lat: float = Query(None, description="Latitude from device GPS (optional)"),
        lng: float = Query(None, description="Longitude from device GPS (optional)"),
        platform: str = Query(None, description="Platform hint: android, ios, windows, linux, web"),
        lang: str = Query("en", description="Language: en or ar")
    ):
        """
        Smart location detection.

        Priority:
          1. lat + lng provided → GPS, reverse-geocode from local DB,
             fall back to Nominatim if DB has no nearby city.
          2. Otherwise → detect from client IP via ip-api.com.
        """
        lang = self.get_lang(request, lang)

        # ── Branch 1: GPS coordinates ─────────────────────────────────────────
        if lat is not None and lng is not None:
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return {
                    "error": self.translate({
                        "ar": "إحداثيات غير صالحة. lat بين -90 و 90، lng بين -180 و 180.",
                        "en": "Invalid coordinates. lat must be -90..90, lng must be -180..180."
                    }, lang)
                }

            # Local DB
            db_city = db_reverse_geocode(lat, lng)
            if db_city:
                return {
                    "method": "gps",
                    "source": "local_db",
                    "latitude": lat,
                    "longitude": lng,
                    "city": db_city.get("name"),
                    "city_local": db_city.get("name_local"),
                    "governorate": db_city.get("governorate"),
                    "country": db_city.get("country"),
                    "country_code": db_city.get("iso2"),
                    "timezone": db_city.get("timezone"),
                    "accuracy": self.translate({
                        "ar": "دقة عالية — إحداثيات GPS من الجهاز",
                        "en": "High accuracy — GPS coordinates from device"
                    }, lang),
                    "platform": platform
                }

            # Nominatim reverse
            self.logger.info(f"No DB city near ({lat}, {lng}), trying Nominatim reverse geocode")
            nom_city = await nominatim_reverse(lat, lng, lang)
            if nom_city:
                return {
                    "method": "gps",
                    "source": "nominatim",
                    "latitude": lat,
                    "longitude": lng,
                    "city": nom_city.get("name"),
                    "city_local": nom_city.get("name_local"),
                    "governorate": nom_city.get("governorate"),
                    "country": nom_city.get("country"),
                    "country_code": nom_city.get("country_code"),
                    "timezone": nom_city.get("timezone"),
                    "display_name": nom_city.get("display_name"),
                    "accuracy": self.translate({
                        "ar": "دقة عالية — إحداثيات GPS من الجهاز (اسم المدينة من OpenStreetMap)",
                        "en": "High accuracy — GPS coordinates from device (city name from OpenStreetMap)"
                    }, lang),
                    "note": self.translate({
                        "ar": "تم تخزين المدينة محلياً للاستخدام دون انترنت لاحقاً",
                        "en": "City cached locally for future offline use"
                    }, lang),
                    "platform": platform
                }

            # GPS known, city lookup failed
            return {
                "method": "gps",
                "source": "coordinates_only",
                "latitude": lat,
                "longitude": lng,
                "city": None,
                "country": None,
                "timezone": None,
                "accuracy": self.translate({
                    "ar": "إحداثيات GPS متاحة — اسم المدينة غير متاح حالياً",
                    "en": "GPS coordinates available — city name unavailable right now"
                }, lang),
                "note": self.translate({
                    "ar": "يمكن حساب أوقات الصلاة مباشرة من الإحداثيات",
                    "en": "Prayer times can be calculated directly from coordinates"
                }, lang),
                "platform": platform
            }

        # ── Branch 2: IP detection ────────────────────────────────────────────
        ip = request.headers.get("X-Forwarded-For")
        if ip:
            ip = ip.split(",")[0].strip()
        else:
            ip = request.client.host

        if ip in ("127.0.0.1", "::1", "localhost"):
            return {
                "method": "none",
                "source": "localhost",
                "latitude": None,
                "longitude": None,
                "city": None,
                "country": None,
                "timezone": None,
                "error": self.translate({
                    "ar": "الكشف التلقائي غير متاح من localhost. أرسل lat و lng من الجهاز.",
                    "en": "Auto-detection unavailable from localhost. Pass lat and lng from device."
                }, lang),
                "platform": platform,
                "suggested_endpoint": "/api/v1/location/auto?lat=30.0444&lng=31.2357"
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://ip-api.com/json/{ip}",
                    params={"fields": "status,message,country,countryCode,regionName,city,lat,lon,timezone,query"},
                    timeout=5.0
                )
                data = response.json()
        except Exception:
            return {
                "method": "none",
                "source": "ip_failed",
                "error": self.translate({
                    "ar": "فشل في الكشف عن الموقع. أرسل lat و lng يدوياً.",
                    "en": "Location detection failed. Pass lat and lng manually."
                }, lang),
                "platform": platform
            }

        if data.get("status") != "success":
            return {
                "method": "none",
                "source": "ip_failed",
                "error": self.translate({
                    "ar": "فشل في الكشف عن الموقع عبر IP",
                    "en": "Failed to detect location from IP"
                }, lang),
                "message": data.get("message", "Unknown error"),
                "platform": platform
            }

        return {
            "method": "ip",
            "source": "ip-api",
            "ip": data.get("query"),
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
            "city": data.get("city"),
            "governorate": data.get("regionName"),
            "country": data.get("country"),
            "country_code": data.get("countryCode"),
            "timezone": data.get("timezone"),
            "accuracy": self.translate({
                "ar": "دقة مستوى المدينة (+/- 10-50 كم)",
                "en": "City-level accuracy (+/- 10-50 km)"
            }, lang),
            "note": self.translate({
                "ar": "دقة كافية لأوقات الصلاة (فرق +/- 1-2 دقيقة مقبول شرعاً). للدقة الكاملة أرسل GPS.",
                "en": "Sufficient for prayer times (+/- 1-2 min accepted). Send GPS coords for full accuracy."
            }, lang),
            "platform": platform
        }

    async def config_view(
        self,
        request: Request,
        platform: str = Query(None, description="Filter to a specific platform: android, ios, windows, linux, web, desktop"),
        lang: str = Query("en", description="Language: en or ar")
    ):
        """
        Return the active location config from config/location.yaml.

        Protection level is controlled by config_endpoint.protection:
          - public     → anyone can call it
          - api_key    → requires valid X-API-Key (enforced by main middleware)
          - disabled   → 404
        """
        lang = self.get_lang(request, lang)

        if not LOCATION_CONFIG_PATH.exists():
            return {
                "error": self.translate({
                    "ar": "ملف الإعدادات غير موجود",
                    "en": "Config file not found"
                }, lang),
                "path": str(LOCATION_CONFIG_PATH)
            }

        try:
            with open(LOCATION_CONFIG_PATH, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except Exception as e:
            return {
                "error": self.translate({
                    "ar": "فشل في قراءة ملف الإعدادات",
                    "en": "Failed to read config file"
                }, lang),
                "detail": str(e)
            }

        loc = raw.get("location", {})

        endpoint_cfg = loc.get("config_endpoint", {})
        if not endpoint_cfg.get("enabled", True):
            return {
                "error": self.translate({
                    "ar": "نقطة الإعدادات معطلة",
                    "en": "Config endpoint is disabled"
                }, lang)
            }

        methods_raw = loc.get("methods", {})
        methods = {}
        for key, val in methods_raw.items():
            methods[key] = {
                "enabled": val.get("enabled", False),
                "label": self.translate({
                    "en": val.get("label_en", key),
                    "ar": val.get("label_ar", key)
                }, lang),
            }
            for extra_key in ("provider", "timeout_seconds", "source", "cache_results",
                              "default_zoom", "default_center_lat", "default_center_lng",
                              "online_tiles", "offline_tiles", "allow_coordinates", "allow_city_name"):
                if extra_key in val:
                    methods[key][extra_key] = val[extra_key]

        platforms_raw = loc.get("platforms", {})

        if platform:
            if platform not in platforms_raw:
                return {
                    "error": self.translate({
                        "ar": f"المنصة '{platform}' غير معرّفة في الإعدادات",
                        "en": f"Platform '{platform}' is not defined in config"
                    }, lang),
                    "available_platforms": list(platforms_raw.keys())
                }

            plat_cfg = platforms_raw[platform]
            priority_labeled = [
                {
                    "method": m,
                    "order": i + 1,
                    "label": methods.get(m, {}).get("label", m),
                    "enabled": methods.get(m, {}).get("enabled", False)
                }
                for i, m in enumerate(plat_cfg.get("priority", []))
            ]

            return {
                "platform": platform,
                "priority": priority_labeled,
                "cache_location": plat_cfg.get("cache_location", False),
                "cache_ttl_hours": plat_cfg.get("cache_ttl_hours"),
                "methods": methods,
                "global": {
                    "enabled": loc.get("enabled", True),
                    "on_method_disabled": loc.get("on_method_disabled", "skip"),
                    "accuracy": loc.get("accuracy", {}),
                    "offline": loc.get("offline", {}),
                }
            }

        platforms_out = {}
        for plat_name, plat_cfg in platforms_raw.items():
            priority_labeled = [
                {
                    "method": m,
                    "order": i + 1,
                    "label": methods.get(m, {}).get("label", m),
                    "enabled": methods.get(m, {}).get("enabled", False)
                }
                for i, m in enumerate(plat_cfg.get("priority", []))
            ]
            platforms_out[plat_name] = {
                "priority": priority_labeled,
                "cache_location": plat_cfg.get("cache_location", False),
                "cache_ttl_hours": plat_cfg.get("cache_ttl_hours"),
            }

        return {
            "enabled": loc.get("enabled", True),
            "on_method_disabled": loc.get("on_method_disabled", "skip"),
            "methods": methods,
            "platforms": platforms_out,
            "accuracy": loc.get("accuracy", {}),
            "offline": loc.get("offline", {}),
            "map": loc.get("map", {}),
        }

    async def prayer_times_auto(
        self,
        request: Request,
        method: str = Query("EGYPT", description="Calculation method"),
        lang: str = Query("en", description="Language: en or ar"),
        timezone: str = Query(None, description="Override timezone")
    ):
        # Try to import the prayer_times module — it may not exist yet
        try:
            import pytz as _pytz
            from datetime import date as _date
            from modules.prayer_times.core.methods import PrayerTimes, CalculationMethod, AsrMethod
        except ImportError:
            return {
                "error": "Prayer times module is not available yet",
                "note": "The prayer_times module has not been implemented. Use /api/v1/prayer-times instead."
            }

        lang = self.get_lang(request, lang)

        ip = request.headers.get("X-Forwarded-For")
        if ip:
            ip = ip.split(",")[0].strip()
        else:
            ip = request.client.host

        if not ip or ip in ("127.0.0.1", "::1", "localhost", "testclient"):
            latitude, longitude = 30.0444, 31.2357
            detected_timezone = timezone or "Africa/Cairo"
            city, country = "Cairo (localhost fallback)", "Egypt"
            ip_used = ip
        else:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://ip-api.com/json/{ip}",
                    params={"fields": "status,country,city,lat,lon,timezone,query"},
                    timeout=5.0
                )
                location = response.json()

            if location.get("status") != "success":
                from fastapi import HTTPException
                raise HTTPException(503, self.translate({
                    "ar": "فشل في كشف الموقع تلقائياً",
                    "en": "Failed to auto-detect location"
                }, lang))

            latitude = location["lat"]
            longitude = location["lon"]
            detected_timezone = timezone or location.get("timezone", "UTC")
            city = location.get("city")
            country = location.get("country")
            ip_used = location.get("query", ip)

        today = _date.today()
        tz = _pytz.timezone(detected_timezone)
        try:
            pt = PrayerTimes(CalculationMethod[method], AsrMethod.STANDARD)
            times = pt.calc_times(today, tz, longitude, latitude)
        except KeyError:
            from fastapi import HTTPException
            raise HTTPException(400, f"Invalid method: {method}")
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(500, str(e))

        return {
            "detected_location": {
                "ip": ip_used,
                "city": city,
                "country": country,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": detected_timezone,
            },
            "date": today.isoformat(),
            "method": method,
            "accuracy_note": self.translate({
                "ar": "دقة IP: مستوى المدينة. الفرق +/- 1-2 دقيقة مقبول شرعاً كاحتياط.",
                "en": "IP accuracy: city-level. +/- 1-2 min difference is acceptable as a fallback."
            }, lang),
            "sunrise": times["sunrise"].strftime("%H:%M"),
            "prayers": [
                {"name": self.translate({"en": "Fajr",    "ar": "الفجر"},    lang), "time": times["fajr"].strftime("%H:%M")},
                {"name": self.translate({"en": "Dhuhr",   "ar": "الظهر"},   lang), "time": times["dhuhr"].strftime("%H:%M")},
                {"name": self.translate({"en": "Asr",     "ar": "العصر"},     lang), "time": times["asr"].strftime("%H:%M")},
                {"name": self.translate({"en": "Maghrib", "ar": "المغرب"}, lang), "time": times["maghrib"].strftime("%H:%M")},
                {"name": self.translate({"en": "Isha",    "ar": "العشاء"},    lang), "time": times["isha"].strftime("%H:%M")},
            ]
        }