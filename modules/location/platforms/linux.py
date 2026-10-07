from fastapi import APIRouter, Request
from ._helpers import _try_ip_detect, _method_list

router = APIRouter()


@router.get("/linux")
async def location_linux(request: Request):
    """
    Linux — location detection guide + IP fallback.
    """
    ip_result = await _try_ip_detect(request)
    priority = ["wifi", "ip_detection", "city_search", "map_picker", "manual_entry"]

    return {
        "platform": "linux",
        "ip_detection": ip_result,
        "methods": _method_list(priority),
        "guide": {
            "wifi": {
                "title": "GeoClue2 (Linux Location Service)",
                "description": "D-Bus service for location on Linux. Available on most modern distros.",
                "command": "apt install geoclue-2.0  # Debian/Ubuntu",
                "python_hint": "Use 'pyclue' or call D-Bus directly via dbus-python.",
                "note": "Not available on all server Linux installs — use IP detection as primary.",
            },
            "ip_detection": {
                "title": "IP Detection (Primary on Linux)",
                "description": "Most reliable option for Linux desktop and server.",
                "endpoint": "/api/v1/location/detect",
                "python_hint": "import geocoder; g = geocoder.ip('me'); print(g.latlng)",
            },
            "city_search": {
                "title": "City Search",
                "endpoint": "/api/v1/location/search?q={city_name}",
            },
            "map_picker": {
                "title": "Map Picker",
                "endpoint": "/map/picker",
                "embed": "Embed in Electron, GTK WebView, or Qt WebEngine.",
            },
            "manual_entry": {
                "title": "Manual Entry",
                "description": "User types city name or lat/long.",
            },
        },
        "cache_recommendation": {
            "enabled": True,
            "ttl_hours": 168,
        },
    }
