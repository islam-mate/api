"""
Shared helpers for all platform location endpoints.
"""

from fastapi import Request
import httpx


async def _try_ip_detect(request: Request) -> dict:
    """Attempt IP-based location detection. Returns result or error dict."""
    client_ip = request.client.host if request.client else None

    if not client_ip or client_ip in ("127.0.0.1", "::1", "localhost"):
        return {
            "detected": False,
            "note": "localhost detected — IP detection requires a real public IP",
        }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"http://ip-api.com/json/{client_ip}?fields=status,city,lat,lon,timezone,country,regionName"
            )
            data = resp.json()

        if data.get("status") == "success":
            return {
                "detected": True,
                "ip": client_ip,
                "city": data.get("city"),
                "region": data.get("regionName"),
                "country": data.get("country"),
                "latitude": data.get("lat"),
                "longitude": data.get("lon"),
                "timezone": data.get("timezone"),
            }
        return {
            "detected": False,
            "note": "IP detection failed — use city search or manual entry",
        }
    except Exception:
        return {
            "detected": False,
            "note": "IP detection service unreachable — use city search or manual entry",
        }


def _method_list(priority: list[str]) -> list[dict]:
    """Convert priority list to labeled method objects."""
    labels = {
        "gps":          {"label_en": "Use my GPS",         "label_ar": "استخدم GPS",       "requires_permission": True},
        "wifi":         {"label_en": "Detect via WiFi",    "label_ar": "كشف عبر WiFi",     "requires_permission": False},
        "ip_detection": {"label_en": "Auto detect (IP)",   "label_ar": "كشف تلقائي",        "requires_permission": False},
        "city_search":  {"label_en": "Search city",        "label_ar": "ابحث عن مدينة",    "requires_permission": False},
        "map_picker":   {"label_en": "Pick on map",        "label_ar": "اختر على الخريطة", "requires_permission": False},
        "manual_entry": {"label_en": "Enter manually",     "label_ar": "إدخال يدوي",       "requires_permission": False},
    }
    return [
        {"method": m, "order": i + 1, **labels.get(m, {})}
        for i, m in enumerate(priority)
    ]
