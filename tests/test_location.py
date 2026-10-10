from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestLocationModule:

    def test_search_english(self):
        response = client.get("/api/v1/location/search?q=Cairo")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        assert data["results"][0]["latitude"] is not None
        assert data["results"][0]["longitude"] is not None

    def test_search_arabic(self):
        response = client.get("/api/v1/ar/location/search?q=القاهرة")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0

    def test_search_arabic_lang_param(self):
        response = client.get("/api/v1/location/search?q=Cairo&lang=ar")
        assert response.status_code == 200

    def test_search_limit(self):
        response = client.get("/api/v1/location/search?q=Cairo&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] <= 2

    def test_search_empty_query(self):
        response = client.get("/api/v1/location/search?q=a")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    def test_search_no_results(self):
        response = client.get("/api/v1/location/search?q=xyzxyzxyz123")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_detect_localhost(self):
        response = client.get("/api/v1/location/detect")
        assert response.status_code == 200
        data = response.json()
        assert "note" in data or "error" in data

    def test_prayer_times_auto_localhost(self):
        response = client.get("/api/v1/prayer-times/auto")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data or "prayers" in data

    def test_search_riyadh(self):
        response = client.get("/api/v1/location/search?q=Riyadh")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0

    def test_search_returns_coordinates(self):
        response = client.get("/api/v1/location/search?q=London")
        assert response.status_code == 200
        data = response.json()
        result = data["results"][0]
        assert "latitude" in result
        assert "longitude" in result
        assert "country" in result
        assert "name" in result
