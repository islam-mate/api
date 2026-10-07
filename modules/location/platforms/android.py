from fastapi import APIRouter, Request
from ._helpers import _try_ip_detect, _method_list

router = APIRouter()


@router.get("/android")
async def location_android(request: Request):
    """
    Android — location detection guide + IP fallback.

    Returns the recommended method priority for Android apps,
    with a developer guide for each method.
    """
    ip_result = await _try_ip_detect(request)
    priority = ["gps", "wifi", "ip_detection", "city_search", "map_picker"]

    return {
        "platform": "android",
        "ip_detection": ip_result,
        "methods": _method_list(priority),
        "guide": {
            "gps": {
                "title": "GPS (Recommended)",
                "description": "Most accurate. Requires ACCESS_FINE_LOCATION permission.",
                "permission": "android.permission.ACCESS_FINE_LOCATION",
                "code_hint": "Use FusedLocationProviderClient from Google Play Services for best battery + accuracy balance.",
                "flutter_hint": "Use the 'geolocator' package: await Geolocator.getCurrentPosition()",
            },
            "wifi": {
                "title": "WiFi / Network Location",
                "description": "Good accuracy indoors. Uses ACCESS_COARSE_LOCATION.",
                "permission": "android.permission.ACCESS_COARSE_LOCATION",
                "code_hint": "FusedLocationProviderClient with PRIORITY_BALANCED_POWER_ACCURACY.",
                "flutter_hint": "Same geolocator package, lower accuracy setting.",
            },
            "ip_detection": {
                "title": "IP Detection (Automatic Fallback)",
                "description": "No permission needed. Accuracy: city level (~10–50 km).",
                "endpoint": "/api/v1/location/detect",
                "note": "Use when user denies GPS permission.",
            },
            "city_search": {
                "title": "City Search",
                "description": "User types their city name.",
                "endpoint": "/api/v1/location/search?q={city_name}",
                "note": "Use as manual override or when other methods fail.",
            },
            "map_picker": {
                "title": "Map Picker",
                "description": "User taps their location on a map.",
                "endpoint": "/map/picker",
                "embed": "Load in WebView or Flutter WebView. Listen for postMessage with lat/lng.",
            },
        },
        "cache_recommendation": {
            "enabled": True,
            "ttl_hours": 24,
            "note": "Cache the detected location locally to avoid repeated API calls.",
        },
    }
