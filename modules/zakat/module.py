"""
Islam Mate API — Zakat Calculator Module
=========================================
GET /api/v1/zakat/calculate  — Full Zakat calculation (monetary + livestock)
GET /api/v1/zakat/nisab      — Current Nisab thresholds

Covers:
  - Zakat al-Mal  : gold, silver, cash, stocks, business goods, receivables (2.5%)
  - Zakat al-An'am: camels, cows/buffaloes, sheep/goats (animal-based brackets)

Nisab standards:
  - Gold   : 85 grams  (20 mithqal)
  - Silver : 595 grams (200 dirhams)

Reference: Fiqh al-Zakat — Sheikh Yusuf al-Qaradawi
"""

from fastapi import APIRouter, Query, Request

from base.base_module import BaseModule
from .calculator import ZakatCalculatorMixin, NISAB_GOLD_GRAMS, NISAB_SILVER_GRAMS, ZAKAT_RATE


class Module(ZakatCalculatorMixin, BaseModule):
    name = "zakat"
    version = "1.0.0"
    dependencies = []

    def register_routes(self, router: APIRouter):
        router.add_api_route(
            "/zakat/calculate",
            self.calculate,
            methods=["GET"],
            summary="Calculate Zakat",
            description=(
                "Calculate Zakat al-Mal (monetary wealth) and Zakat al-An'am (livestock). "
                "Provide current gold/silver prices for accurate monetary nisab. "
                "All asset fields default to 0 — pass only what you own."
            ),
        )
        router.add_api_route(
            "/zakat/nisab",
            self.nisab_info,
            methods=["GET"],
            summary="Nisab Thresholds",
            description="Get gold and silver nisab thresholds in value using today's prices.",
        )

    # ── Main endpoint ──────────────────────────────────────────────────────────

    async def calculate(
        self,
        request: Request,
        # ── Monetary assets ────────────────────────────────────────────────
        gold_grams: float = Query(0.0, ge=0, description="Gold owned in grams"),
        silver_grams: float = Query(0.0, ge=0, description="Silver owned in grams"),
        cash: float = Query(0.0, ge=0, description="Cash and bank savings"),
        stocks: float = Query(0.0, ge=0, description="Stock and investment portfolio value"),
        goods: float = Query(0.0, ge=0, description="Business inventory / trade goods value"),
        receivables: float = Query(0.0, ge=0, description="Confirmed debts owed to you"),
        # ── Prices ─────────────────────────────────────────────────────────
        gold_price_per_gram: float = Query(
            90.0, gt=0,
            description="Current gold spot price per gram (in your local currency)"
        ),
        silver_price_per_gram: float = Query(
            0.9, gt=0,
            description="Current silver spot price per gram (in your local currency)"
        ),
        # ── Nisab standard ─────────────────────────────────────────────────
        nisab_standard: str = Query(
            "silver",
            description="Nisab standard to apply: 'gold' or 'silver'. "
                        "Most scholars recommend silver as it benefits more people."
        ),
        # ── Livestock ──────────────────────────────────────────────────────
        camels: int = Query(0, ge=0, description="Number of camels you own"),
        cows: int = Query(0, ge=0, description="Number of cows / buffaloes you own"),
        sheep: int = Query(0, ge=0, description="Number of sheep / goats you own"),
        # ── Language ───────────────────────────────────────────────────────
        lang: str = Query("en", description="Response language: 'en' or 'ar'"),
    ):
        lang = self.get_lang(request, lang)

        # ── Nisab values ───────────────────────────────────────────────────
        nisab_gold_value   = round(NISAB_GOLD_GRAMS   * gold_price_per_gram,   2)
        nisab_silver_value = round(NISAB_SILVER_GRAMS * silver_price_per_gram, 2)

        if nisab_standard not in ("gold", "silver"):
            nisab_standard = "silver"

        nisab_value = nisab_gold_value if nisab_standard == "gold" else nisab_silver_value

        # ── Monetary assets ────────────────────────────────────────────────
        gold_value   = round(gold_grams   * gold_price_per_gram,   2)
        silver_value = round(silver_grams * silver_price_per_gram, 2)
        total_monetary = round(gold_value + silver_value + cash + stocks + goods + receivables, 2)

        monetary_meets_nisab = total_monetary >= nisab_value
        monetary_zakat = round(total_monetary * ZAKAT_RATE, 2) if monetary_meets_nisab else 0.0

        # ── Livestock ──────────────────────────────────────────────────────
        camels_result = self._camels_zakat(camels, lang)
        cows_result   = self._cows_zakat(cows,   lang)
        sheep_result  = self._sheep_zakat(sheep,  lang)

        has_livestock_zakat = (
            camels_result["due"] or
            cows_result["due"]   or
            sheep_result["due"]
        )

        zakat_due = monetary_meets_nisab or has_livestock_zakat

        return {
            "zakat_due": zakat_due,
            "summary": {
                "label": self.translate({"en": "Zakat Summary", "ar": "ملخص الزكاة"}, lang),
                "monetary_zakat": monetary_zakat,
                "livestock_zakat_due": has_livestock_zakat,
                "status": self.translate(
                    {"en": "Zakat is due", "ar": "الزكاة واجبة"} if zakat_due
                    else {"en": "No Zakat due — assets below nisab", "ar": "لا زكاة — الأصول دون النصاب"},
                    lang
                ),
            },
            "nisab": {
                "standard": nisab_standard,
                "gold_threshold_grams":   NISAB_GOLD_GRAMS,
                "silver_threshold_grams": NISAB_SILVER_GRAMS,
                "gold_nisab_value":       nisab_gold_value,
                "silver_nisab_value":     nisab_silver_value,
                "applied_nisab_value":    nisab_value,
                "label": self.translate({
                    "en": f"Nisab ({nisab_standard} standard)",
                    "ar": f"النصاب (معيار {'الفضة' if nisab_standard == 'silver' else 'الذهب'})"
                }, lang),
            },
            "monetary": {
                "label":           self.translate({"en": "Monetary Zakat (Zakat al-Mal)", "ar": "زكاة المال"}, lang),
                "meets_nisab":     monetary_meets_nisab,
                "total_assets":    total_monetary,
                "zakat_due":       monetary_zakat,
                "rate":            "2.5%",
                "breakdown": {
                    "gold": {
                        "label":  self.translate({"en": "Gold", "ar": "الذهب"}, lang),
                        "grams":  gold_grams,
                        "value":  gold_value,
                    },
                    "silver": {
                        "label":  self.translate({"en": "Silver", "ar": "الفضة"}, lang),
                        "grams":  silver_grams,
                        "value":  silver_value,
                    },
                    "cash": {
                        "label": self.translate({"en": "Cash & Savings", "ar": "النقود والمدخرات"}, lang),
                        "value": round(cash, 2),
                    },
                    "stocks": {
                        "label": self.translate({"en": "Stocks & Investments", "ar": "الأسهم والاستثمارات"}, lang),
                        "value": round(stocks, 2),
                    },
                    "goods": {
                        "label": self.translate({"en": "Business Goods", "ar": "عروض التجارة"}, lang),
                        "value": round(goods, 2),
                    },
                    "receivables": {
                        "label": self.translate({"en": "Receivables (confirmed debts)", "ar": "الديون المستحقة لك"}, lang),
                        "value": round(receivables, 2),
                    },
                },
                "hawl_note": self.translate({
                    "en": "Condition: all assets must have been owned for one complete lunar year (hawl).",
                    "ar": "شرط: يجب أن تكون هذه الأصول مملوكة طوال حول هجري كامل."
                }, lang),
            },
            "livestock": {
                "label":  self.translate({"en": "Livestock Zakat (Zakat al-An'am)", "ar": "زكاة الأنعام"}, lang),
                "camels": camels_result,
                "cows":   cows_result,
                "sheep":  sheep_result,
            },
            "meta": {
                "prices_used": {
                    "gold_per_gram":   gold_price_per_gram,
                    "silver_per_gram": silver_price_per_gram,
                },
                "price_note": self.translate({
                    "en": "Update gold/silver prices to today's market rates for accurate calculation.",
                    "ar": "يُرجى تحديث أسعار الذهب والفضة بالأسعار اليومية للحساب الدقيق."
                }, lang),
                "reference": "Fiqh al-Zakat — Sheikh Yusuf al-Qaradawi",
                "disclaimer": self.translate({
                    "en": "This tool provides a general estimate. Consult a qualified scholar for your specific situation.",
                    "ar": "هذه الأداة تقدّم تقديراً عاماً. استشر عالماً مؤهلاً لوضعك الخاص."
                }, lang),
            },
        }

    # ── Nisab endpoint ─────────────────────────────────────────────────────────

    async def nisab_info(
        self,
        gold_price_per_gram: float = Query(90.0, gt=0, description="Gold price per gram"),
        silver_price_per_gram: float = Query(0.9, gt=0, description="Silver price per gram"),
        lang: str = Query("en", description="Language: en or ar"),
    ):
        gold_value   = round(NISAB_GOLD_GRAMS   * gold_price_per_gram,   2)
        silver_value = round(NISAB_SILVER_GRAMS * silver_price_per_gram, 2)

        return {
            "gold": {
                "label":       self.translate({"en": "Gold Nisab",   "ar": "نصاب الذهب"},   lang),
                "grams":       NISAB_GOLD_GRAMS,
                "description": self.translate({"en": "20 mithqal",  "ar": "20 مثقالاً"},   lang),
                "value":       gold_value,
            },
            "silver": {
                "label":       self.translate({"en": "Silver Nisab", "ar": "نصاب الفضة"},   lang),
                "grams":       NISAB_SILVER_GRAMS,
                "description": self.translate({"en": "200 dirhams", "ar": "200 درهم"},      lang),
                "value":       silver_value,
            },
            "recommendation": self.translate({
                "en": (
                    "Most contemporary scholars recommend using the silver nisab "
                    "because it includes more people who owe Zakat."
                ),
                "ar": (
                    "يوصي أكثر العلماء المعاصرين بنصاب الفضة "
                    "لأنه يوجب الزكاة على عدد أكبر من الناس."
                )
            }, lang),
            "prices_used": {
                "gold_per_gram":   gold_price_per_gram,
                "silver_per_gram": silver_price_per_gram,
            },
        }
