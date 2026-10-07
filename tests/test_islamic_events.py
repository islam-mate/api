import pytest
from datetime import date
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

BASE = "/api/v1/hijri/events"
YEAR = 2025  # stable reference year for assertions


class TestIslamicEventsSuccess:

    def test_get_events_default(self):
        """Default call returns 200 with expected top-level keys."""
        response = client.get(BASE)
        assert response.status_code == 200
        data = response.json()
        assert "year" in data
        assert "hijri_year" in data
        assert "total_events" in data
        assert "events" in data

    def test_get_events_response_structure(self):
        response = client.get(BASE, params={"year": YEAR})
        data = response.json()
        events = data["events"]
        for section in ("holidays", "months", "special_nights", "weekly", "monthly"):
            assert section in events, f"Missing section: {section}"

    def test_year_param_reflected(self):
        response = client.get(BASE, params={"year": YEAR})
        data = response.json()
        assert data["year"] == YEAR

    def test_hijri_year_present(self):
        response = client.get(BASE, params={"year": YEAR})
        data = response.json()
        # 2025 corresponds roughly to Hijri 1446/1447
        assert 1446 <= data["hijri_year"] <= 1447

    def test_calculation_method_present(self):
        response = client.get(BASE)
        data = response.json()
        assert "calculation_method" in data
        assert len(data["calculation_method"]) > 0

    def test_total_events_count(self):
        """total_events should match sum of all sections."""
        response = client.get(BASE, params={"year": YEAR})
        data = response.json()
        events = data["events"]
        computed_total = sum(len(v) for v in events.values())
        assert data["total_events"] == computed_total


class TestIslamicHolidays:

    def test_holidays_count(self):
        """Should have 10 holiday events (the fixed list in module)."""
        response = client.get(BASE, params={"year": YEAR})
        holidays = response.json()["events"]["holidays"]
        assert len(holidays) == 10

    def test_holiday_structure(self):
        response = client.get(BASE, params={"year": YEAR})
        holidays = response.json()["events"]["holidays"]
        for h in holidays:
            assert "name" in h
            assert "name_en" in h
            assert "name_ar" in h
            assert "type" in h
            assert "gregorian_date" in h
            assert "hijri_date" in h
            assert "duration_days" in h

    def test_holidays_sorted_by_date(self):
        response = client.get(BASE, params={"year": YEAR})
        holidays = response.json()["events"]["holidays"]
        dates = [h["gregorian_date"] for h in holidays if h["gregorian_date"]]
        assert dates == sorted(dates)

    def test_eid_al_fitr_present(self):
        response = client.get(BASE, params={"year": YEAR})
        holidays = response.json()["events"]["holidays"]
        names_en = [h["name_en"] for h in holidays]
        assert "Eid al-Fitr" in names_en

    def test_eid_al_adha_present(self):
        response = client.get(BASE, params={"year": YEAR})
        holidays = response.json()["events"]["holidays"]
        names_en = [h["name_en"] for h in holidays]
        assert "Eid al-Adha" in names_en

    def test_ramadan_present(self):
        response = client.get(BASE, params={"year": YEAR})
        holidays = response.json()["events"]["holidays"]
        names_en = [h["name_en"] for h in holidays]
        assert "Ramadan" in names_en

    def test_ramadan_duration_30_days(self):
        response = client.get(BASE, params={"year": YEAR})
        holidays = response.json()["events"]["holidays"]
        ramadan = next(h for h in holidays if h["name_en"] == "Ramadan")
        assert ramadan["duration_days"] == 30

    def test_eid_al_adha_duration_4_days(self):
        response = client.get(BASE, params={"year": YEAR})
        holidays = response.json()["events"]["holidays"]
        eid_adha = next(h for h in holidays if h["name_en"] == "Eid al-Adha")
        assert eid_adha["duration_days"] == 4

    def test_ramadan_has_moon_sighting_note(self):
        response = client.get(BASE, params={"year": YEAR})
        holidays = response.json()["events"]["holidays"]
        ramadan = next(h for h in holidays if h["name_en"] == "Ramadan")
        assert "moon_sighting_note" in ramadan
        assert len(ramadan["moon_sighting_note"]) > 0

    def test_holiday_gregorian_dates_in_correct_year(self):
        """All holidays with gregorian_date should have a plausible date."""
        response = client.get(BASE, params={"year": YEAR})
        holidays = response.json()["events"]["holidays"]
        for h in holidays:
            if h["gregorian_date"]:
                d = date.fromisoformat(h["gregorian_date"])
                # Allow ±1 year due to Hijri calendar wraparound
                assert YEAR - 1 <= d.year <= YEAR + 1

    def test_laylat_al_qadr_type_special_night(self):
        response = client.get(BASE, params={"year": YEAR})
        holidays = response.json()["events"]["holidays"]
        qadr = next((h for h in holidays if "Qadr" in h["name_en"]), None)
        assert qadr is not None
        assert qadr["type"] == "special_night"


class TestIslamicMonths:

    def test_months_count(self):
        """12 Hijri months always returned."""
        response = client.get(BASE, params={"year": YEAR})
        months = response.json()["events"]["months"]
        assert len(months) == 12

    def test_month_structure(self):
        response = client.get(BASE, params={"year": YEAR})
        months = response.json()["events"]["months"]
        for m in months:
            assert "number" in m
            assert "name" in m
            assert "name_en" in m
            assert "name_ar" in m
            assert "hijri_year" in m
            assert "hijri_month" in m

    def test_month_numbers_sequential(self):
        response = client.get(BASE, params={"year": YEAR})
        months = response.json()["events"]["months"]
        numbers = [m["number"] for m in months]
        assert numbers == list(range(1, 13))

    def test_ramadan_month_moon_sighting_note(self):
        """Month 9 (Ramadan) must have moon_sighting_note."""
        response = client.get(BASE, params={"year": YEAR})
        months = response.json()["events"]["months"]
        ramadan_month = next(m for m in months if m["number"] == 9)
        assert ramadan_month["moon_sighting_note"] is not None

    def test_regular_months_no_moon_sighting_note(self):
        """Months other than 9, 10, 12 should have null moon_sighting_note."""
        response = client.get(BASE, params={"year": YEAR})
        months = response.json()["events"]["months"]
        for m in months:
            if m["number"] not in (9, 10, 12):
                assert m["moon_sighting_note"] is None


class TestSpecialNights:

    def test_special_nights_count(self):
        """Last 10 nights of Ramadan (21–30) = 9 or 10 entries (Ramadan is 29 or 30 days)."""
        response = client.get(BASE, params={"year": YEAR})
        special_nights = response.json()["events"]["special_nights"]
        assert 9 <= len(special_nights) <= 10

    def test_special_night_structure(self):
        response = client.get(BASE, params={"year": YEAR})
        special_nights = response.json()["events"]["special_nights"]
        for n in special_nights:
            assert "name" in n
            assert "gregorian_date" in n
            assert "hijri_date" in n
            assert "type" in n
            assert "is_odd" in n

    def test_special_night_type_value(self):
        response = client.get(BASE, params={"year": YEAR})
        special_nights = response.json()["events"]["special_nights"]
        for n in special_nights:
            assert n["type"] == "special_night"

    def test_odd_nights_flagged(self):
        """Nights 21,23,25,27,29 are odd; 22,24,26,28,(30) are even.
        Day 30 may be absent when Ramadan is 29 days."""
        response = client.get(BASE, params={"year": YEAR})
        special_nights = response.json()["events"]["special_nights"]
        odd_nights = [n for n in special_nights if n["is_odd"]]
        even_nights = [n for n in special_nights if not n["is_odd"]]
        assert len(odd_nights) == 5
        assert 4 <= len(even_nights) <= 5

    def test_special_nights_sorted(self):
        response = client.get(BASE, params={"year": YEAR})
        special_nights = response.json()["events"]["special_nights"]
        dates = [n["gregorian_date"] for n in special_nights if n["gregorian_date"]]
        assert dates == sorted(dates)


class TestWeeklyJumuah:

    def test_weekly_included_by_default(self):
        """include_weekly defaults to True → weekly section non-empty."""
        response = client.get(BASE, params={"year": YEAR})
        weekly = response.json()["events"]["weekly"]
        assert len(weekly) > 0

    def test_weekly_all_fridays(self):
        """A year has 52 or 53 Fridays."""
        response = client.get(BASE, params={"year": YEAR})
        weekly = response.json()["events"]["weekly"]
        assert 52 <= len(weekly) <= 53

    def test_weekly_structure(self):
        response = client.get(BASE, params={"year": YEAR})
        weekly = response.json()["events"]["weekly"]
        for w in weekly:
            assert "name" in w
            assert "gregorian_date" in w
            assert "type" in w
            assert w["type"] == "weekly"
            assert w["day_of_week"] == "Friday"

    def test_weekly_excluded_when_disabled(self):
        response = client.get(
            BASE,
            params={"year": YEAR, "include_weekly": False}
        )
        weekly = response.json()["events"]["weekly"]
        assert len(weekly) == 0

    def test_weekly_dates_all_fridays(self):
        """Every gregorian_date in weekly must be a Friday."""
        response = client.get(BASE, params={"year": YEAR})
        weekly = response.json()["events"]["weekly"]
        for w in weekly:
            d = date.fromisoformat(w["gregorian_date"])
            assert d.weekday() == 4, f"{w['gregorian_date']} is not a Friday"


class TestMonthlyWhiteDays:

    def test_monthly_included_by_default(self):
        response = client.get(BASE, params={"year": YEAR})
        monthly = response.json()["events"]["monthly"]
        assert len(monthly) > 0

    def test_monthly_count_36(self):
        """12 months × 3 days (13, 14, 15) = 36 white day entries."""
        response = client.get(BASE, params={"year": YEAR})
        monthly = response.json()["events"]["monthly"]
        assert len(monthly) == 36

    def test_monthly_structure(self):
        response = client.get(BASE, params={"year": YEAR})
        monthly = response.json()["events"]["monthly"]
        for m in monthly:
            assert "name" in m
            assert "gregorian_date" in m
            assert "hijri_date" in m
            assert "hijri_day" in m
            assert "hijri_month" in m
            assert "type" in m

    def test_monthly_type_value(self):
        response = client.get(BASE, params={"year": YEAR})
        monthly = response.json()["events"]["monthly"]
        for m in monthly:
            assert m["type"] == "monthly"

    def test_white_days_only_13_14_15(self):
        response = client.get(BASE, params={"year": YEAR})
        monthly = response.json()["events"]["monthly"]
        for m in monthly:
            assert m["hijri_day"] in (13, 14, 15)

    def test_monthly_excluded_when_disabled(self):
        response = client.get(
            BASE,
            params={"year": YEAR, "include_monthly": False}
        )
        monthly = response.json()["events"]["monthly"]
        assert len(monthly) == 0


class TestEventTypeFilter:

    def test_filter_holidays(self):
        response = client.get(BASE, params={"year": YEAR, "event_type": "holidays"})
        data = response.json()
        assert "holidays" in data["events"]
        assert len(data["events"]) == 1

    def test_filter_months(self):
        response = client.get(BASE, params={"year": YEAR, "event_type": "months"})
        data = response.json()
        assert "months" in data["events"]
        assert len(data["events"]) == 1

    def test_filter_special_nights(self):
        response = client.get(BASE, params={"year": YEAR, "event_type": "special_nights"})
        data = response.json()
        assert "special_nights" in data["events"]
        assert len(data["events"]) == 1

    def test_filter_weekly(self):
        response = client.get(BASE, params={"year": YEAR, "event_type": "weekly"})
        data = response.json()
        assert "weekly" in data["events"]
        assert len(data["events"]) == 1

    def test_filter_monthly(self):
        response = client.get(BASE, params={"year": YEAR, "event_type": "monthly"})
        data = response.json()
        assert "monthly" in data["events"]
        assert len(data["events"]) == 1

    def test_invalid_filter_returns_all(self):
        """An unknown event_type should return all sections."""
        response = client.get(BASE, params={"year": YEAR, "event_type": "invalid_type"})
        data = response.json()
        assert len(data["events"]) == 5


class TestIslamicEventsLanguage:

    def test_holidays_english(self):
        response = client.get(BASE, params={"year": YEAR, "lang": "en"})
        holidays = response.json()["events"]["holidays"]
        eid = next(h for h in holidays if h["name_en"] == "Eid al-Fitr")
        assert eid["name"] == "Eid al-Fitr"

    def test_holidays_arabic(self):
        response = client.get(BASE, params={"year": YEAR, "lang": "ar"})
        holidays = response.json()["events"]["holidays"]
        eid = next(h for h in holidays if h["name_en"] == "Eid al-Fitr")
        assert eid["name"] == "عيد الفطر"

    def test_months_name_arabic(self):
        response = client.get(BASE, params={"year": YEAR, "lang": "ar"})
        months = response.json()["events"]["months"]
        ramadan_month = next(m for m in months if m["number"] == 9)
        assert ramadan_month["name"] == "رمضان"

    def test_months_name_english(self):
        response = client.get(BASE, params={"year": YEAR, "lang": "en"})
        months = response.json()["events"]["months"]
        ramadan_month = next(m for m in months if m["number"] == 9)
        assert ramadan_month["name"] == "Ramadan"

    def test_both_name_fields_always_present(self):
        """name_en and name_ar always present regardless of lang."""
        for lang in ("en", "ar"):
            response = client.get(BASE, params={"year": YEAR, "lang": lang})
            holidays = response.json()["events"]["holidays"]
            for h in holidays:
                assert h["name_en"], f"name_en missing for lang={lang}"
                assert h["name_ar"], f"name_ar missing for lang={lang}"