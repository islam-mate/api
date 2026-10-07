from fastapi import APIRouter, Request
from ._helpers import _try_ip_detect, _method_list

router = APIRouter()


@router.get("/web")
async def location_web(request: Request):
    """
    Web / Browser — location detection guide + IP fallback.
    """
    ip_result = await _try_ip_detect(request)
    priority = ["wifi", "gps", "ip_detection", "city_search", "map_picker"]

    return {
        "platform": "web",
        "ip_detection": ip_result,
        "methods": _method_list(priority),
        "guide": {
            "wifi": {
                "title": "Geolocation API (WiFi + GPS)",
                "description": "Built into every modern browser. Uses WiFi or GPS depending on device.",
                "code_hint": """navigator.geolocation.getCurrentPosition(
  (pos) => {
    const lat = pos.coords.latitude;
    const lng = pos.coords.longitude;
    // send to your API
  },
  (err) => {
    // fallback to IP detection
  }
);""",
                "note": "Requires HTTPS. User must grant permission.",
            },
            "gps": {
                "title": "High-Accuracy GPS (Mobile Browser)",
                "description": "Available on mobile browsers with GPS hardware.",
                "code_hint": "navigator.geolocation.getCurrentPosition(cb, err, { enableHighAccuracy: true })",
            },
            "ip_detection": {
                "title": "IP Detection (No-Permission Fallback)",
                "description": "Works immediately, no permission popup.",
                "endpoint": "/api/v1/location/detect",
                "note": "Use when user denies browser location or as initial fast load.",
            },
            "city_search": {
                "title": "City Search",
                "endpoint": "/api/v1/location/search?q={city_name}",
                "note": "Add a search box to your UI calling this endpoint.",
            },
            "map_picker": {
                "title": "Map Picker",
                "endpoint": "/map/picker",
                "embed": "Embed as <iframe>. Listen for window.addEventListener('message', ...) to receive {lat, lng}.",
                "example": """<iframe src="/map/picker?response=full" id="map-picker"></iframe>
<script>
  window.addEventListener('message', (e) => {
    if (e.data.lat && e.data.lng) {
      console.log(e.data); // { lat, lng, city, timezone }
    }
  });
</script>""",
            },
        },
        "cache_recommendation": {
            "enabled": False,
            "note": "Do not cache in browser — sessionStorage only if needed.",
        },
    }
