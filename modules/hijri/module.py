from fastapi import APIRouter, Query, HTTPException, Request
from datetime import datetime, date
from typing import Optional

from base.base_module import BaseModule


class Module(BaseModule):
    name = "hijri"
    version = "1.0.0"
    dependencies = []

    ISLAMIC_MONTHS = {
        "ar": [
            "محرم", "صفر", "ربيع الأول", "ربيع الثاني",
            "جمادى الأولى", "جمادى الثانية", "رجب", "شعبان",
            "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
        ],
        "en": [
            "Muharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani",
            "Jumada al-Awwal", "Jumada al-Thani", "Rajab", "Shaban",
            "Ramadan", "Shawwal", "Dhul Qadah", "Dhul Hijjah"
        ]
    }

    DAY_NAMES = {
        "ar": ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"],
        "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    }

    ISLAMIC_EVENTS = [
        {"hijri_month": 1,  "hijri_day": 1,  "event_type": "holiday",     "name": {"en": "Islamic New Year",       "ar": "رأس السنة الهجرية"}},
        {"hijri_month": 1,  "hijri_day": 10, "event_type": "observance",  "name": {"en": "Day of Ashura",           "ar": "يوم عاشوراء"}},
        {"hijri_month": 3,  "hijri_day": 12, "event_type": "holiday",     "name": {"en": "Prophet's Birthday",      "ar": "المولد النبوي الشريف"}},
        {"hijri_month": 7,  "hijri_day": 27, "event_type": "observance",  "name": {"en": "Isra and Miraj",          "ar": "الإسراء والمعراج"}},
        {"hijri_month": 8,  "hijri_day": 15, "event_type": "observance",  "name": {"en": "Shaban Middle Night",     "ar": "نصف شعبان"}},
        {"hijri_month": 9,  "hijri_day": 1,  "event_type": "observance",  "name": {"en": "Ramadan Start",           "ar": "بداية رمضان"}},
        {"hijri_month": 9,  "hijri_day": 27, "event_type": "observance",  "name": {"en": "Laylat al-Qadr",          "ar": "ليلة القدر"}},
        {"hijri_month": 10, "hijri_day": 1,  "event_type": "holiday",     "name": {"en": "Eid al-Fitr",             "ar": "عيد الفطر"}},
        {"hijri_month": 12, "hijri_day": 9,  "event_type": "observance",  "name": {"en": "Day of Arafah",           "ar": "يوم عرفة"}},
        {"hijri_month": 12, "hijri_day": 10, "event_type": "holiday",     "name": {"en": "Eid al-Adha",             "ar": "عيد الأضحى"}},
        {"event_type": "weekly",                                            "name": {"en": "Jumu'ah (Friday Prayer)", "ar": "صلاة الجمعة"}},
    ]

    def register_routes(self, router: APIRouter):
        router.add_api_route("/hijri/today",   self.get_hijri_date, methods=["GET"])
        router.add_api_route("/hijri/convert", self.convert_date,   methods=["GET"])
        router.add_api_route("/hijri/months",  self.get_months,     methods=["GET"])
        # /hijri/events is owned by the islamic_events module (richer implementation)

    async def get_hijri_date(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        today = date.today()
        hijri = self._to_hijri(today)
        return self._build_response(today, hijri, lang)

    async def convert_date(
        self,
        request: Request,
        date: str = Query(..., description="Gregorian date YYYY-MM-DD"),
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        try:
            greg = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")
        hijri = self._to_hijri(greg)
        return self._build_response(greg, hijri, lang)

    async def get_months(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        months = self.ISLAMIC_MONTHS.get(lang, self.ISLAMIC_MONTHS["en"])
        return {
            "months": [
                {"number": i + 1, "name": name}
                for i, name in enumerate(months)
            ]
        }

    async def get_islamic_events(
        self,
        request: Request,
        year: Optional[int] = Query(None, description="Gregorian year (default: current)"),
        lang: str = Query("en", description="Language: en or ar"),
        event_type: Optional[str] = Query(None, description="Filter by type: holiday, observance, weekly"),
        include_weekly: bool = Query(True, description="Include weekly events (e.g. Jumu'ah)")
    ):
        lang = self.get_lang(request, lang)
        from hijridate import Hijri, Gregorian
        target_year = year or date.today().year

        jan1  = Gregorian(target_year, 1,  1).to_hijri()
        dec31 = Gregorian(target_year, 12, 31).to_hijri()
        hijri_years = set(range(jan1.year, dec31.year + 1))

        results = []
        for event in self.ISLAMIC_EVENTS:
            etype = event.get("event_type", "observance")

            # Handle weekly events separately
            if etype == "weekly":
                if not include_weekly:
                    continue
                if event_type and event_type != "weekly":
                    continue
                results.append({
                    "name":           self.translate(event["name"], lang),
                    "event_type":     "weekly",
                    "hijri_date":     None,
                    "gregorian_date": None,
                    "recurring":      "every Friday"
                })
                continue

            # Filter by event_type
            if event_type and etype != event_type:
                continue

            # Calculate gregorian date for this hijri event
            for hy in hijri_years:
                try:
                    g = Hijri(hy, event["hijri_month"], event["hijri_day"]).to_gregorian()
                    greg_date = date(g.year, g.month, g.day)
                    if greg_date.year == target_year:
                        results.append({
                            "name":           self.translate(event["name"], lang),
                            "event_type":     etype,
                            "hijri_date":     f"{hy}/{event['hijri_month']:02d}/{event['hijri_day']:02d}",
                            "gregorian_date": greg_date.isoformat(),
                        })
                        break
                except Exception:
                    continue

        # Sort: dated events first (by date), then weekly at end
        results.sort(key=lambda x: x.get("gregorian_date") or "9999-99-99")

        return {
            "year":   target_year,
            "total":  len(results),
            "events": results
        }

    def _to_hijri(self, greg: date):
        from hijridate import Gregorian
        return Gregorian(greg.year, greg.month, greg.day).to_hijri()

    def _build_response(self, greg: date, hijri, lang: str) -> dict:
        months   = self.ISLAMIC_MONTHS.get(lang, self.ISLAMIC_MONTHS["en"])
        day_names = self.DAY_NAMES.get(lang, self.DAY_NAMES["en"])
        month_name = months[hijri.month - 1]
        day_name   = day_names[greg.weekday()]   # Mon=0 .. Sun=6
        return {
            "gregorian": {
                "date":  greg.isoformat(),
                "day":   greg.day,
                "month": greg.month,
                "year":  greg.year,
            },
            "hijri": {
                "date":       f"{hijri.year}/{hijri.month:02d}/{hijri.day:02d}",
                "day":        hijri.day,
                "month":      hijri.month,
                "month_name": month_name,
                "year":       hijri.year,
            },
            "day_name": day_name
        }