from fastapi import APIRouter, Request
from ._helpers import _try_ip_detect, _method_list

router = APIRouter()


@router.get("/windows")
async def location_windows(request: Request):
    """
    Windows — location detection guide + IP fallback.
    """
    ip_result = await _try_ip_detect(request)
    priority = ["wifi", "ip_detection", "city_search", "map_picker", "manual_entry"]

    return {
        "platform": "windows",
        "ip_detection": ip_result,
        "methods": _method_list(priority),
        "guide": {
            "wifi": {
                "title": "Windows Location API",
                "description": "Uses WiFi triangulation via Windows.Devices.Geolocation.",
                "code_hint": "Geolocator geolocator = new Geolocator(); var position = await geolocator.GetGeopositionAsync();",
                "note": "User must have Location Services enabled in Windows Settings → Privacy → Location.",
                "python_hint": "Use the 'geocoder' library: geocoder.ip('me') as fallback.",
            },
            "ip_detection": {
                "title": "IP Detection (Primary Fallback)",
                "description": "No permission needed. Accuracy: city level.",
                "endpoint": "/api/v1/location/detect",
                "note": "Most reliable on Windows where GPS is uncommon.",
            },
            "city_search": {
                "title": "City Search",
                "endpoint": "/api/v1/location/search?q={city_name}",
            },
            "map_picker": {
                "title": "Map Picker",
                "endpoint": "/map/picker",
                "embed": "Embed in WebView2 (WPF/WinForms) or Electron BrowserWindow.",
            },
            "manual_entry": {
                "title": "Manual Entry",
                "description": "User types city name or coordinates.",
                "note": "Always offer as last resort.",
            },
        },
        "cache_recommendation": {
            "enabled": True,
            "ttl_hours": 168,
            "note": "Cache for 1 week on desktop — location rarely changes.",
        },
    }
