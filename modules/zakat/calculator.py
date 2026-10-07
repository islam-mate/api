"""
modules/zakat/calculator.py
============================
Zakat constants and livestock calculation helpers.

Uses a mixin pattern so self.translate() works automatically
when ZakatCalculatorMixin is combined with BaseModule in Module.

Imported by module.py:
  from .calculator import ZakatCalculatorMixin, NISAB_GOLD_GRAMS, NISAB_SILVER_GRAMS, ZAKAT_RATE
"""

# ── Constants ──────────────────────────────────────────────────────────────────
NISAB_GOLD_GRAMS   = 85.0    # grams of gold   — 20 mithqal
NISAB_SILVER_GRAMS = 595.0   # grams of silver  — 200 dirhams
ZAKAT_RATE         = 0.025   # 2.5% on monetary wealth


# ── Mixin ──────────────────────────────────────────────────────────────────────

class ZakatCalculatorMixin:
    """
    Livestock zakat helpers.

    self.translate() is resolved at runtime through Module's MRO
    (Module inherits both this mixin and BaseModule).
    """

    def _camels_zakat(self, count: int, lang: str) -> dict:
        """
        Camel Zakat table (consensus across major schools).
        Below 5 camels: no Zakat.
        """
        label = self.translate({"en": "Camels", "ar": "الإبل"}, lang)
        no_due = {"count": count, "due": False, "animals_owed": [], "label": label}

        if count < 5:
            return no_due

        brackets = [
            (5,   9,  [{"qty": 1, "type": {"en": "sheep/goat",                    "ar": "شاة"}}]),
            (10,  14, [{"qty": 2, "type": {"en": "sheep/goats",                   "ar": "شاتان"}}]),
            (15,  19, [{"qty": 3, "type": {"en": "sheep/goats",                   "ar": "ثلاث شياه"}}]),
            (20,  24, [{"qty": 4, "type": {"en": "sheep/goats",                   "ar": "أربع شياه"}}]),
            (25,  35, [{"qty": 1, "type": {"en": "bint makhad (1-yr she-camel)",  "ar": "بنت مخاض"}}]),
            (36,  45, [{"qty": 1, "type": {"en": "bint labun (2-yr she-camel)",   "ar": "بنت لبون"}}]),
            (46,  60, [{"qty": 1, "type": {"en": "hiqqah (3-yr she-camel)",       "ar": "حِقَّة"}}]),
            (61,  75, [{"qty": 1, "type": {"en": "jadha'ah (4-yr she-camel)",     "ar": "جذعة"}}]),
            (76,  90, [{"qty": 2, "type": {"en": "bint labun (2-yr she-camels)",  "ar": "بنتا لبون"}}]),
            (91, 120, [{"qty": 2, "type": {"en": "hiqqah (3-yr she-camels)",      "ar": "حِقَّتان"}}]),
        ]

        for low, high, animals in brackets:
            if low <= count <= high:
                return {
                    "count": count,
                    "due":   True,
                    "animals_owed": [
                        {"qty": a["qty"], "description": self.translate(a["type"], lang)}
                        for a in animals
                    ],
                    "label": label,
                }

        # 121+: per-40 bint labun + per-50 hiqqah
        if count >= 121:
            return {
                "count": count,
                "due":   True,
                "animals_owed": [{
                    "qty": "variable",
                    "description": self.translate({
                        "en": "1 bint labun per 40 camels + 1 hiqqah per 50 camels",
                        "ar": "بنت لبون عن كل ٤٠ ناقة + حِقَّة عن كل ٥٠ ناقة"
                    }, lang),
                }],
                "label": label,
                "scholar_note": self.translate({
                    "en": "For 121+ camels the exact combination varies by school of thought. Please consult a scholar.",
                    "ar": "لأكثر من 121 ناقة، تختلف التفصيلات بين المذاهب. يُرجى استشارة عالم متخصص."
                }, lang),
            }

        return no_due

    def _cows_zakat(self, count: int, lang: str) -> dict:
        """
        Cow / buffalo Zakat.
        30 cows → 1 tabi'   (1-yr calf)
        40 cows → 1 musinna (2-yr heifer)
        Finds the split a×30 + b×40 = count that minimises a+b.
        """
        label = self.translate({"en": "Cows / Buffaloes", "ar": "البقر والجاموس"}, lang)
        no_due = {"count": count, "due": False, "animals_owed": [], "label": label}

        if count < 30:
            return no_due

        best_a, best_b = None, None
        for b in range(count // 40 + 1):
            remainder = count - 40 * b
            if remainder >= 0 and remainder % 30 == 0:
                a = remainder // 30
                if best_a is None or (a + b) < (best_a + best_b):
                    best_a, best_b = a, b

        if best_a is None:
            return {**no_due, "due": True, "scholar_note": self.translate({
                "en": "Count does not fit the standard 30/40 bracket. Consult a scholar.",
                "ar": "العدد لا يندرج في الشرائح الاعتيادية. استشر عالماً."
            }, lang)}

        animals_owed = []
        if best_a:
            animals_owed.append({
                "qty": best_a,
                "description": self.translate(
                    {"en": f"{best_a} tabi' (1-yr calf)", "ar": f"{best_a} تبيع (عجل عمره سنة)"},
                    lang
                ),
            })
        if best_b:
            animals_owed.append({
                "qty": best_b,
                "description": self.translate(
                    {"en": f"{best_b} musinna (2-yr heifer)", "ar": f"{best_b} مُسِنَّة (بقرة عمرها سنتان)"},
                    lang
                ),
            })

        return {"count": count, "due": True, "animals_owed": animals_owed, "label": label}

    def _sheep_zakat(self, count: int, lang: str) -> dict:
        """
        Sheep / goat Zakat.
        40–120  → 1 sheep
        121–200 → 2 sheep
        201–399 → 3 sheep
        400–499 → 4 sheep
        500+    → +1 per 100
        """
        label = self.translate({"en": "Sheep / Goats", "ar": "الغنم والماعز"}, lang)
        no_due = {"count": count, "due": False, "animals_owed": [], "label": label}

        if count < 40:
            return no_due

        if   count <= 120: qty = 1
        elif count <= 200: qty = 2
        elif count <= 399: qty = 3
        else:              qty = 4 + (count - 400) // 100

        return {
            "count": count,
            "due":   True,
            "animals_owed": [{
                "qty": qty,
                "description": self.translate(
                    {"en": f"{qty} sheep/goat(s)", "ar": f"{qty} رأس من الغنم"},
                    lang
                ),
            }],
            "label": label,
        }
