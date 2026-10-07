import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestZakatCalculate:

    def test_calculate_no_assets(self):
        """Zero assets → no zakat due."""
        response = client.get("/api/v1/zakat/calculate")
        assert response.status_code == 200
        data = response.json()
        assert data["zakat_due"] is False
        assert data["summary"]["monetary_zakat"] == 0.0
        assert data["summary"]["livestock_zakat_due"] is False

    def test_calculate_response_structure(self):
        """Top-level keys always present."""
        response = client.get("/api/v1/zakat/calculate")
        assert response.status_code == 200
        data = response.json()
        assert "zakat_due" in data
        assert "summary" in data
        assert "nisab" in data
        assert "monetary" in data
        assert "livestock" in data
        assert "meta" in data

    def test_calculate_monetary_structure(self):
        response = client.get("/api/v1/zakat/calculate", params={"cash": 1000})
        data = response.json()
        monetary = data["monetary"]
        assert "meets_nisab" in monetary
        assert "total_assets" in monetary
        assert "zakat_due" in monetary
        assert "rate" in monetary
        assert "breakdown" in monetary
        breakdown = monetary["breakdown"]
        for key in ("gold", "silver", "cash", "stocks", "goods", "receivables"):
            assert key in breakdown

    def test_calculate_livestock_structure(self):
        response = client.get("/api/v1/zakat/calculate")
        data = response.json()
        livestock = data["livestock"]
        assert "camels" in livestock
        assert "cows" in livestock
        assert "sheep" in livestock

    # ── Monetary: below nisab ──────────────────────────────────────────────────

    def test_cash_below_nisab_silver(self):
        """Cash of 1 unit is below silver nisab (595 * 0.9 = 535.5) → no zakat."""
        response = client.get(
            "/api/v1/zakat/calculate",
            params={"cash": 1.0, "silver_price_per_gram": 0.9, "nisab_standard": "silver"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["monetary"]["meets_nisab"] is False
        assert data["monetary"]["zakat_due"] == 0.0

    def test_cash_at_nisab_silver(self):
        """Cash exactly equal to silver nisab → zakat due."""
        # silver nisab = 595 * 0.9 = 535.5
        response = client.get(
            "/api/v1/zakat/calculate",
            params={"cash": 535.5, "silver_price_per_gram": 0.9, "nisab_standard": "silver"}
        )
        data = response.json()
        assert data["monetary"]["meets_nisab"] is True
        assert data["monetary"]["zakat_due"] == pytest.approx(535.5 * 0.025, abs=0.01)

    def test_cash_above_nisab_gold(self):
        """Cash well above gold nisab → 2.5% zakat."""
        # gold nisab = 85 * 90 = 7650
        cash = 10000.0
        response = client.get(
            "/api/v1/zakat/calculate",
            params={"cash": cash, "gold_price_per_gram": 90.0, "nisab_standard": "gold"}
        )
        data = response.json()
        assert data["monetary"]["meets_nisab"] is True
        assert data["monetary"]["zakat_due"] == pytest.approx(cash * 0.025, abs=0.01)

    def test_gold_grams_value_calculated(self):
        """Gold grams × price must appear in breakdown value."""
        response = client.get(
            "/api/v1/zakat/calculate",
            params={"gold_grams": 100.0, "gold_price_per_gram": 90.0}
        )
        data = response.json()
        assert data["monetary"]["breakdown"]["gold"]["value"] == pytest.approx(100 * 90, abs=0.01)

    def test_combined_assets_above_nisab(self):
        """Combination of assets that together exceed nisab."""
        response = client.get(
            "/api/v1/zakat/calculate",
            params={
                "gold_grams": 10.0,
                "gold_price_per_gram": 90.0,
                "cash": 400.0,
                "stocks": 200.0,
                "silver_price_per_gram": 0.9,
                "nisab_standard": "silver"
            }
        )
        data = response.json()
        # total = 10*90 + 400 + 200 = 900 + 600 = 1500 > 535.5
        assert data["monetary"]["meets_nisab"] is True
        assert data["monetary"]["total_assets"] == pytest.approx(1500.0, abs=0.01)

    # ── Nisab standard ─────────────────────────────────────────────────────────

    def test_nisab_standard_gold(self):
        response = client.get(
            "/api/v1/zakat/calculate",
            params={"cash": 5000, "nisab_standard": "gold", "gold_price_per_gram": 90.0}
        )
        data = response.json()
        assert data["nisab"]["standard"] == "gold"
        assert data["nisab"]["applied_nisab_value"] == pytest.approx(85 * 90, abs=0.01)

    def test_nisab_standard_silver(self):
        response = client.get(
            "/api/v1/zakat/calculate",
            params={"cash": 1000, "nisab_standard": "silver", "silver_price_per_gram": 0.9}
        )
        data = response.json()
        assert data["nisab"]["standard"] == "silver"
        assert data["nisab"]["applied_nisab_value"] == pytest.approx(595 * 0.9, abs=0.01)

    def test_nisab_standard_invalid_falls_back_to_silver(self):
        response = client.get(
            "/api/v1/zakat/calculate",
            params={"cash": 1000, "nisab_standard": "bitcoin"}
        )
        data = response.json()
        # invalid standard defaults to silver
        assert data["nisab"]["standard"] == "silver"

    # ── Livestock: camels ──────────────────────────────────────────────────────

    def test_camels_below_minimum(self):
        """4 camels → no zakat."""
        response = client.get("/api/v1/zakat/calculate", params={"camels": 4})
        data = response.json()
        assert data["livestock"]["camels"]["due"] is False

    def test_camels_first_bracket(self):
        """5–9 camels → 1 sheep/goat."""
        response = client.get("/api/v1/zakat/calculate", params={"camels": 7})
        data = response.json()
        camel_result = data["livestock"]["camels"]
        assert camel_result["due"] is True
        assert camel_result["animals_owed"][0]["qty"] == 1

    def test_camels_bracket_25(self):
        """25 camels → 1 bint makhad."""
        response = client.get("/api/v1/zakat/calculate", params={"camels": 25})
        data = response.json()
        camel_result = data["livestock"]["camels"]
        assert camel_result["due"] is True
        assert camel_result["animals_owed"][0]["qty"] == 1

    def test_camels_above_120(self):
        """121+ camels → variable result with scholar note."""
        response = client.get("/api/v1/zakat/calculate", params={"camels": 121})
        data = response.json()
        camel_result = data["livestock"]["camels"]
        assert camel_result["due"] is True
        assert camel_result["animals_owed"][0]["qty"] == "variable"

    # ── Livestock: cows ────────────────────────────────────────────────────────

    def test_cows_below_minimum(self):
        """29 cows → no zakat."""
        response = client.get("/api/v1/zakat/calculate", params={"cows": 29})
        data = response.json()
        assert data["livestock"]["cows"]["due"] is False

    def test_cows_30(self):
        """30 cows → 1 tabi'."""
        response = client.get("/api/v1/zakat/calculate", params={"cows": 30})
        data = response.json()
        assert data["livestock"]["cows"]["due"] is True
        assert data["livestock"]["cows"]["count"] == 30

    def test_cows_40(self):
        """40 cows → 1 musinna."""
        response = client.get("/api/v1/zakat/calculate", params={"cows": 40})
        data = response.json()
        assert data["livestock"]["cows"]["due"] is True

    def test_cows_60(self):
        """60 cows = 2×30 → 2 tabi'."""
        response = client.get("/api/v1/zakat/calculate", params={"cows": 60})
        data = response.json()
        cows_result = data["livestock"]["cows"]
        assert cows_result["due"] is True

    # ── Livestock: sheep ───────────────────────────────────────────────────────

    def test_sheep_below_minimum(self):
        """39 sheep → no zakat."""
        response = client.get("/api/v1/zakat/calculate", params={"sheep": 39})
        data = response.json()
        assert data["livestock"]["sheep"]["due"] is False

    def test_sheep_first_bracket(self):
        """40–120 sheep → 1 sheep."""
        for count in (40, 80, 120):
            response = client.get("/api/v1/zakat/calculate", params={"sheep": count})
            data = response.json()
            assert data["livestock"]["sheep"]["due"] is True
            assert data["livestock"]["sheep"]["animals_owed"][0]["qty"] == 1, f"Failed at count={count}"

    def test_sheep_second_bracket(self):
        """121–200 sheep → 2 sheep."""
        response = client.get("/api/v1/zakat/calculate", params={"sheep": 150})
        data = response.json()
        assert data["livestock"]["sheep"]["animals_owed"][0]["qty"] == 2

    def test_sheep_third_bracket(self):
        """201–399 sheep → 3 sheep."""
        response = client.get("/api/v1/zakat/calculate", params={"sheep": 300})
        data = response.json()
        assert data["livestock"]["sheep"]["animals_owed"][0]["qty"] == 3

    # ── Language ───────────────────────────────────────────────────────────────

    def test_calculate_lang_english(self):
        response = client.get("/api/v1/zakat/calculate", params={"cash": 1000, "lang": "en"})
        data = response.json()
        assert "Zakat" in data["summary"]["label"]

    def test_calculate_lang_arabic(self):
        response = client.get("/api/v1/zakat/calculate", params={"cash": 1000, "lang": "ar"})
        data = response.json()
        assert "الزكاة" in data["summary"]["label"]

    def test_calculate_nisab_label_arabic(self):
        response = client.get(
            "/api/v1/zakat/calculate",
            params={"lang": "ar", "nisab_standard": "silver"}
        )
        data = response.json()
        assert "النصاب" in data["nisab"]["label"]

    # ── Validation ─────────────────────────────────────────────────────────────

    def test_negative_gold_rejected(self):
        response = client.get("/api/v1/zakat/calculate", params={"gold_grams": -10})
        assert response.status_code == 422

    def test_negative_cash_rejected(self):
        response = client.get("/api/v1/zakat/calculate", params={"cash": -500})
        assert response.status_code == 422

    def test_zero_gold_price_rejected(self):
        response = client.get("/api/v1/zakat/calculate", params={"gold_price_per_gram": 0})
        assert response.status_code == 422

    def test_negative_camels_rejected(self):
        response = client.get("/api/v1/zakat/calculate", params={"camels": -1})
        assert response.status_code == 422

    # ── Meta ───────────────────────────────────────────────────────────────────

    def test_meta_prices_reflected(self):
        response = client.get(
            "/api/v1/zakat/calculate",
            params={"gold_price_per_gram": 95.0, "silver_price_per_gram": 1.1}
        )
        data = response.json()
        assert data["meta"]["prices_used"]["gold_per_gram"] == 95.0
        assert data["meta"]["prices_used"]["silver_per_gram"] == 1.1


class TestZakatNisab:

    def test_nisab_info_success(self):
        response = client.get("/api/v1/zakat/nisab")
        assert response.status_code == 200
        data = response.json()
        assert "gold" in data
        assert "silver" in data

    def test_nisab_response_structure(self):
        response = client.get("/api/v1/zakat/nisab")
        data = response.json()
        for key in ("label", "grams", "description", "value"):
            assert key in data["gold"], f"gold missing key: {key}"
            assert key in data["silver"], f"silver missing key: {key}"

    def test_nisab_gold_grams_constant(self):
        response = client.get("/api/v1/zakat/nisab")
        data = response.json()
        assert data["gold"]["grams"] == 85.0

    def test_nisab_silver_grams_constant(self):
        response = client.get("/api/v1/zakat/nisab")
        data = response.json()
        assert data["silver"]["grams"] == 595.0

    def test_nisab_values_reflect_prices(self):
        response = client.get(
            "/api/v1/zakat/nisab",
            params={"gold_price_per_gram": 100.0, "silver_price_per_gram": 1.0}
        )
        data = response.json()
        assert data["gold"]["value"] == pytest.approx(85 * 100, abs=0.01)
        assert data["silver"]["value"] == pytest.approx(595 * 1.0, abs=0.01)

    def test_nisab_lang_arabic(self):
        response = client.get("/api/v1/zakat/nisab", params={"lang": "ar"})
        data = response.json()
        assert "نصاب" in data["gold"]["label"]
        assert "نصاب" in data["silver"]["label"]

    def test_nisab_lang_english(self):
        response = client.get("/api/v1/zakat/nisab", params={"lang": "en"})
        data = response.json()
        assert "Nisab" in data["gold"]["label"]

    def test_nisab_recommendation_present(self):
        response = client.get("/api/v1/zakat/nisab")
        data = response.json()
        assert "recommendation" in data
        assert len(data["recommendation"]) > 0

    def test_nisab_zero_price_rejected(self):
        response = client.get("/api/v1/zakat/nisab", params={"gold_price_per_gram": 0})
        assert response.status_code == 422

    def test_nisab_prices_used_returned(self):
        response = client.get(
            "/api/v1/zakat/nisab",
            params={"gold_price_per_gram": 88.5, "silver_price_per_gram": 0.95}
        )
        data = response.json()
        assert "prices_used" in data
        assert data["prices_used"]["gold_per_gram"] == 88.5
        assert data["prices_used"]["silver_per_gram"] == 0.95
