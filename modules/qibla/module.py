from fastapi import APIRouter, Query
from base.base_module import BaseModule
import math


class Module(BaseModule):
    name = "qibla"
    version = "1.0.0"
    dependencies = []

    # Kaaba coordinates
    KAABA_LAT = 21.4225
    KAABA_LNG = 39.8262

    def register_routes(self, router: APIRouter):
        router.add_api_route("/qibla", self.get_qibla, methods=["GET"])

    async def get_qibla(
        self,
        latitude: float = Query(..., ge=-90, le=90, description="Your latitude"),
        longitude: float = Query(..., ge=-180, le=180, description="Your longitude"),
        lang: str = Query("en", description="Language: en or ar")
    ):
        bearing = self._calculate_bearing(latitude, longitude)
        distance = self._calculate_distance(latitude, longitude)
        direction = self._bearing_to_direction(bearing)

        return {
            "location": {"lat": latitude, "lng": longitude},
            "qibla": {
                "bearing": round(bearing, 2),
                "direction": direction,
                "distance_km": round(distance, 2),
                "description": self.translate({
                    "en": f"Qibla is {round(bearing, 1)} degrees from North",
                    "ar": f"اتجاه القبلة {round(bearing, 1)} درجة من الشمال"
                }, lang),
                "kaaba": {
                    "lat": self.KAABA_LAT,
                    "lng": self.KAABA_LNG
                }
            }
        }

    def _calculate_bearing(self, lat: float, lng: float) -> float:
        lat1 = math.radians(lat)
        lat2 = math.radians(self.KAABA_LAT)
        delta_lng = math.radians(self.KAABA_LNG - lng)

        x = math.sin(delta_lng) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lng)

        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360

    def _calculate_distance(self, lat: float, lng: float) -> float:
        R = 6371  # Earth radius in km
        lat1 = math.radians(lat)
        lat2 = math.radians(self.KAABA_LAT)
        delta_lat = math.radians(self.KAABA_LAT - lat)
        delta_lng = math.radians(self.KAABA_LNG - lng)

        a = math.sin(delta_lat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _bearing_to_direction(self, bearing: float) -> str:
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(bearing / 45) % 8
        return directions[index]
