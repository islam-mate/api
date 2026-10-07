from fastapi import APIRouter, Request
from ._helpers import _try_ip_detect, _method_list

router = APIRouter()


@router.get("/ios")
async def location_ios(request: Request):
    """
    iOS — location detection guide + IP fallback.
    """
    ip_result = await _try_ip_detect(request)
    priority = ["gps", "wifi", "ip_detection", "city_search", "map_picker"]

    return {
        "platform": "ios",
        "ip_detection": ip_result,
        "methods": _method_list(priority),
        "guide": {
            "gps": {
                "title": "Core Location GPS (Recommended)",
                "description": "Most accurate. Requires NSLocationWhenInUseUsageDescription in Info.plist.",
                "plist_key": "NSLocationWhenInUseUsageDescription",
                "code_hint": "Use CLLocationManager. Request whenInUseAuthorization before starting updates.",
                "flutter_hint": "Use 'geolocator' package. Add NSLocationWhenInUseUsageDescription to Info.plist.",
            },
            "wifi": {
                "title": "WiFi / Network Location",
                "description": "Uses kCLAuthorizationStatusAuthorizedWhenInUse with lower accuracy.",
                "code_hint": "CLLocationManager with desiredAccuracy = kCLLocationAccuracyKilometer.",
            },
            "ip_detection": {
                "title": "IP Detection (Automatic Fallback)",
                "description": "No permission needed. Accuracy: city level.",
                "endpoint": "/api/v1/location/detect",
                "note": "Use when user denies Core Location permission.",
            },
            "city_search": {
                "title": "City Search",
                "endpoint": "/api/v1/location/search?q={city_name}",
            },
            "map_picker": {
                "title": "Map Picker",
                "endpoint": "/map/picker",
                "embed": "Load in WKWebView. Use window.postMessage to receive lat/lng back.",
            },
        },
        "cache_recommendation": {
            "enabled": True,
            "ttl_hours": 24,
        },
    }
