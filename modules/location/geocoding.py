"""
modules/location/geocoding.py
==============================
Nominatim (OpenStreetMap) helpers — city search and reverse geocoding.

Results are automatically cached to cities.db via cache_to_db.

Imported by module.py → nominatim_search, nominatim_reverse
"""

import httpx

from .db import cache_to_db


_HEADERS = {"User-Agent": "IslamMateAPI/2.0"}
_TIMEOUT = 10.0


async def nominatim_search(q: str, lang: str = "en", limit: int = 5) -> list[dict]:
    """Search Nominatim for a city by name. Caches results to local DB."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": q,
                    "format": "json",
                    "limit": limit,
                    "addressdetails": 1,
                    "accept-language": lang,
                },
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            results = response.json()

        cities = []
        for r in results:
            address = r.get("address", {})
            city_name = (
                address.get("city") or
                address.get("town") or
                address.get("village") or
                address.get("county") or
                r.get("display_name", "").split(",")[0]
            )

            city = {
                "name": city_name,
                "name_local": None,
                "country": address.get("country", ""),
                "country_code": address.get("country_code", "").upper(),
                "governorate": address.get("state", ""),
                "latitude": float(r.get("lat", 0)),
                "longitude": float(r.get("lon", 0)),
                "timezone": None,
                "display_name": r.get("display_name", ""),
                "source": "nominatim",
            }
            cities.append(city)
            cache_to_db(city)

        return cities
    except Exception:
        return []


async def nominatim_reverse(lat: float, lng: float, lang: str = "en") -> dict | None:
    """Reverse geocode lat/lng → city info via Nominatim. Caches result to local DB."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": lat,
                    "lon": lng,
                    "format": "json",
                    "addressdetails": 1,
                    "accept-language": lang,
                },
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            r = response.json()

        if "error" in r:
            return None

        address = r.get("address", {})
        city_name = (
            address.get("city") or
            address.get("town") or
            address.get("village") or
            address.get("county") or
            r.get("display_name", "").split(",")[0]
        )

        result = {
            "name": city_name,
            "name_local": None,
            "country": address.get("country", ""),
            "country_code": address.get("country_code", "").upper(),
            "governorate": address.get("state", ""),
            "latitude": lat,
            "longitude": lng,
            "timezone": None,
            "display_name": r.get("display_name", ""),
            "source": "nominatim",
        }

        cache_to_db(result)
        return result
    except Exception:
        return None
