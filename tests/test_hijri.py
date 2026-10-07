import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHijri:

    def test_get_hijri_today(self):
        response = client.get("/api/v1/hijri/today")
        assert response.status_code == 200
        data = response.json()
        assert "gregorian" in data
        assert "hijri" in data

    def test_hijri_response_structure(self):
        response = client.get("/api/v1/hijri/today")
        data = response.json()
        assert "date" in data["gregorian"]
        assert "day" in data["gregorian"]
        assert "month" in data["gregorian"]
        assert "year" in data["gregorian"]
        assert "date" in data["hijri"]
        assert "day" in data["hijri"]
        assert "month" in data["hijri"]
        assert "month_name" in data["hijri"]
        assert "year" in data["hijri"]

    def test_hijri_english(self):
        response = client.get("/api/v1/hijri/today", params={"lang": "en"})
        data = response.json()
        english_months = [
            "Muharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani",
            "Jumada al-Awwal", "Jumada al-Thani", "Rajab", "Shaban",
            "Ramadan", "Shawwal", "Dhul Qadah", "Dhul Hijjah"
        ]
        assert data["hijri"]["month_name"] in english_months

    def test_hijri_arabic(self):
        response = client.get("/api/v1/hijri/today", params={"lang": "ar"})
        data = response.json()
        arabic_months = [
            "محرم", "صفر", "ربيع الأول", "ربيع الثاني",
            "جمادى الأولى", "جمادى الثانية", "رجب", "شعبان",
            "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
        ]
        assert data["hijri"]["month_name"] in arabic_months

    def test_convert_date(self):
        response = client.get(
            "/api/v1/hijri/convert",
            params={"date": "2026-10-02"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["gregorian"]["date"] == "2026-10-02"
        assert data["gregorian"]["year"] == 2026
        assert data["hijri"]["year"] > 1440

    def test_convert_invalid_date(self):
        response = client.get(
            "/api/v1/hijri/convert",
            params={"date": "invalid-date"}
        )
        assert response.status_code == 400

    def test_get_months_english(self):
        response = client.get("/api/v1/hijri/months", params={"lang": "en"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["months"]) == 12
        assert data["months"][0]["name"] == "Muharram"
        assert data["months"][8]["name"] == "Ramadan"

    def test_get_months_arabic(self):
        response = client.get("/api/v1/hijri/months", params={"lang": "ar"})
        data = response.json()
        assert len(data["months"]) == 12
        assert data["months"][0]["name"] == "محرم"
        assert data["months"][8]["name"] == "رمضان"

    def test_get_months_numbering(self):
        response = client.get("/api/v1/hijri/months")
        data = response.json()
        for i, month in enumerate(data["months"], 1):
            assert month["number"] == i

    def test_islamic_events(self):
        # /hijri/events is now served by the islamic_events module (richer format)
        response = client.get("/api/v1/hijri/events")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total_events" in data
        assert data["total_events"] > 0

    def test_islamic_events_specific_year(self):
        response = client.get(
            "/api/v1/hijri/events",
            params={"year": 2026}
        )
        data = response.json()
        assert data["year"] == 2026
        # events is a dict with sections; check at least one section is non-empty
        assert any(len(v) > 0 for v in data["events"].values())

    def test_islamic_events_have_eid(self):
        response = client.get(
            "/api/v1/hijri/events",
            params={"year": 2026}
        )
        data = response.json()
        holiday_names = [h["name_en"] for h in data["events"]["holidays"]]
        assert any("Eid" in name for name in holiday_names)

    def test_islamic_events_sorted_by_date(self):
        response = client.get("/api/v1/hijri/events")
        data = response.json()
        dates = [h["gregorian_date"] for h in data["events"]["holidays"] if h["gregorian_date"]]
        assert dates == sorted(dates)