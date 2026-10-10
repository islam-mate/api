from fastapi import APIRouter, Query, Request
from base.base_module import BaseModule
from datetime import datetime, date, timedelta
from hijridate import Gregorian, Hijri


class Module(BaseModule):
    name = "islamic_events"
    version = "1.0.0"
    dependencies = []

    def register_routes(self, router: APIRouter):
        router.add_api_route(
            "/hijri/events",
            self.get_events,
            methods=["GET"],
            summary="Full Islamic calendar events for a year",
            tags=["Hijri Calendar"]
        )

    # ============================================
    # HELPERS
    # ============================================

    def _hijri_to_gregorian(self, year: int, month: int, day: int) -> date:
        """Convert Hijri date to Gregorian."""
        try:
            g = Hijri(year, month, day).to_gregorian()
            return date(g.year, g.month, g.day)
        except Exception:
            return None

    def _gregorian_to_hijri(self, d: date) -> tuple:
        """Convert Gregorian date to Hijri."""
        try:
            h = Gregorian(d.year, d.month, d.day).to_hijri()
            return h.year, h.month, h.day
        except Exception:
            return None, None, None

    def _get_all_fridays(self, year: int) -> list[date]:
        """Get all Fridays in a Gregorian year."""
        fridays = []
        d = date(year, 1, 1)
        while d.weekday() != 4:  # 4 = Friday
            d += timedelta(days=1)
        while d.year == year:
            fridays.append(d)
            d += timedelta(days=7)
        return fridays

    def _get_white_days(self, hijri_year: int) -> list[dict]:
        """Get White Days (13, 14, 15) for all Hijri months in a year."""
        white_days = []
        for month in range(1, 13):
            for day in [13, 14, 15]:
                g_date = self._hijri_to_gregorian(hijri_year, month, day)
                if g_date:
                    white_days.append({
                        "hijri_day": day,
                        "hijri_month": month,
                        "gregorian_date": str(g_date)
                    })
        return white_days

    def _format_event(
        self,
        name_en: str,
        name_ar: str,
        gregorian_date: date,
        hijri_year: int,
        hijri_month: int,
        hijri_day: int,
        event_type: str,
        description_en: str = None,
        description_ar: str = None,
        duration_days: int = 1,
        moon_sighting_note: bool = False,
        lang: str = "en"
    ) -> dict:
        event = {
            "name": name_ar if lang == "ar" else name_en,
            "name_en": name_en,
            "name_ar": name_ar,
            "type": event_type,
            "gregorian_date": str(gregorian_date) if gregorian_date else None,
            "hijri_date": f"{hijri_year}/{hijri_month:02d}/{hijri_day:02d}",
            "hijri_year": hijri_year,
            "hijri_month": hijri_month,
            "hijri_day": hijri_day,
            "duration_days": duration_days,
        }

        if description_en or description_ar:
            event["description"] = description_ar if lang == "ar" else description_en
            event["description_en"] = description_en
            event["description_ar"] = description_ar

        if moon_sighting_note:
            event["moon_sighting_note"] = self.translate({
                "ar": "قد يختلف التاريخ الفعلي يوماً واحداً بناءً على رؤية الهلال",
                "en": "Actual date may differ by 1 day based on moon sighting"
            }, lang)

        return event

    # ============================================
    # MAIN ENDPOINT
    # ============================================

    async def get_events(
        self,
        request: Request,
        year: int = Query(
            None, description="Gregorian year (default: current year)"),
        lang: str = Query("en", description="Language: en or ar"),
        include_weekly: bool = Query(
            True, description="Include weekly Jumu'ah (Friday prayers)"),
        include_monthly: bool = Query(
            True, description="Include monthly White Days"),
        event_type: str = Query(
            None, description="Filter by type: holidays, months, special_nights, weekly, monthly")
    ):
        lang = self.get_lang(request, lang)

        if year is None:
            year = datetime.now().year

        h_year, _, _ = self._gregorian_to_hijri(date(year, 6, 15))
        hijri_year = h_year if h_year else 1446

        # ============================================
        # HOLIDAYS
        # ============================================
        holidays = []

        new_year_date = self._hijri_to_gregorian(hijri_year, 1, 1)
        holidays.append(self._format_event(
            "Islamic New Year", "رأس السنة الهجرية",
            new_year_date, hijri_year, 1, 1,
            "holiday",
            "Beginning of the Islamic lunar calendar year",
            "بداية السنة الهجرية القمرية",
            lang=lang
        ))

        ashura_date = self._hijri_to_gregorian(hijri_year, 1, 10)
        holidays.append(self._format_event(
            "Ashura", "يوم عاشوراء",
            ashura_date, hijri_year, 1, 10,
            "holiday",
            "The 10th of Muharram — a day of fasting",
            "العاشر من محرم — يوم صيام",
            lang=lang
        ))

        isra_date = self._hijri_to_gregorian(hijri_year, 7, 27)
        holidays.append(self._format_event(
            "Isra and Mi'raj", "الإسراء والمعراج",
            isra_date, hijri_year, 7, 27,
            "holiday",
            "The Prophet's night journey and ascension to heaven",
            "رحلة النبي الليلية والصعود إلى السماء",
            lang=lang
        ))

        mid_shaban_date = self._hijri_to_gregorian(hijri_year, 8, 15)
        holidays.append(self._format_event(
            "Mid Sha'ban (Laylat al-Bara'ah)", "نصف شعبان (ليلة البراءة)",
            mid_shaban_date, hijri_year, 8, 15,
            "holiday",
            "The 15th of Sha'ban — Night of Forgiveness",
            "الخامس عشر من شعبان — ليلة البراءة",
            lang=lang
        ))

        ramadan_date = self._hijri_to_gregorian(hijri_year, 9, 1)
        holidays.append(self._format_event(
            "Ramadan", "رمضان",
            ramadan_date, hijri_year, 9, 1,
            "holiday",
            "The holy month of fasting",
            "الشهر الفضيل",
            duration_days=30,
            moon_sighting_note=True,
            lang=lang
        ))

        qadr_date = self._hijri_to_gregorian(hijri_year, 9, 27)
        holidays.append(self._format_event(
            "Laylat al-Qadr (Night of Power)", "ليلة القدر",
            qadr_date, hijri_year, 9, 27,
            "special_night",
            "The Night of Power — better than 1000 months (27th Ramadan)",
            "ليلة القدر — خير من ألف شهر (السابع والعشرون من رمضان)",
            lang=lang
        ))

        eid_fitr_date = self._hijri_to_gregorian(hijri_year, 10, 1)
        holidays.append(self._format_event(
            "Eid al-Fitr", "عيد الفطر",
            eid_fitr_date, hijri_year, 10, 1,
            "holiday",
            "Festival of Breaking the Fast",
            "عيد الفطر المبارك",
            duration_days=3,
            moon_sighting_note=True,
            lang=lang
        ))

        arafat_date = self._hijri_to_gregorian(hijri_year, 12, 9)
        holidays.append(self._format_event(
            "Day of Arafat", "يوم عرفة",
            arafat_date, hijri_year, 12, 9,
            "holiday",
            "The Day of Arafat — recommended fasting for non-pilgrims",
            "يوم عرفة — يستحب صيامه لغير الحجاج",
            lang=lang
        ))

        eid_adha_date = self._hijri_to_gregorian(hijri_year, 12, 10)
        holidays.append(self._format_event(
            "Eid al-Adha", "عيد الأضحى",
            eid_adha_date, hijri_year, 12, 10,
            "holiday",
            "Festival of Sacrifice",
            "عيد الأضحى المبارك",
            duration_days=4,
            moon_sighting_note=True,
            lang=lang
        ))

        mawlid_date = self._hijri_to_gregorian(hijri_year, 3, 12)
        holidays.append(self._format_event(
            "Mawlid al-Nabi (Prophet's Birthday)", "المولد النبوي الشريف",
            mawlid_date, hijri_year, 3, 12,
            "holiday",
            "Birthday of the Prophet Muhammad ﷺ",
            "ذكرى مولد النبي محمد ﷺ",
            lang=lang
        ))

        holidays = sorted(
            [h for h in holidays if h.get("gregorian_date")],
            key=lambda x: x["gregorian_date"]
        )

        # ============================================
        # HIJRI MONTHS
        # ============================================
        hijri_month_names = [
            ("Muharram", "محرم"),
            ("Safar", "صفر"),
            ("Rabi al-Awwal", "ربيع الأول"),
            ("Rabi al-Thani", "ربيع الثاني"),
            ("Jumada al-Awwal", "جمادى الأولى"),
            ("Jumada al-Thani", "جمادى الثانية"),
            ("Rajab", "رجب"),
            ("Sha'ban", "شعبان"),
            ("Ramadan", "رمضان"),
            ("Shawwal", "شوال"),
            ("Dhul Qa'dah", "ذو القعدة"),
            ("Dhul Hijjah", "ذو الحجة"),
        ]

        months = []
        for i, (name_en, name_ar) in enumerate(hijri_month_names, 1):
            start_date = self._hijri_to_gregorian(hijri_year, i, 1)
            months.append({
                "number": i,
                "name": name_ar if lang == "ar" else name_en,
                "name_en": name_en,
                "name_ar": name_ar,
                "hijri_year": hijri_year,
                "hijri_month": i,
                "gregorian_start": str(start_date) if start_date else None,
                "moon_sighting_note": self.translate({
                    "ar": "بداية الشهر تعتمد على رؤية الهلال",
                    "en": "Month start depends on moon sighting"
                }, lang) if i in [9, 10, 12] else None
            })

        # ============================================
        # SPECIAL NIGHTS
        # ============================================
        special_nights = []

        for day in range(21, 31):
            night_date = self._hijri_to_gregorian(hijri_year, 9, day)
            special_nights.append({
                "name": self.translate({
                    "ar": f"ليلة {day} رمضان",
                    "en": f"Night of {day} Ramadan"
                }, lang),
                "gregorian_date": str(night_date) if night_date else None,
                "hijri_date": f"{hijri_year}/09/{day:02d}",
                "type": "special_night",
                "description": self.translate({
                    "ar": "من الليالي الفضيلة في العشر الأواخر من رمضان",
                    "en": "One of the blessed nights in the last 10 days of Ramadan"
                }, lang),
                "is_odd": day % 2 != 0
            })

        special_nights_sorted = sorted(
            [n for n in special_nights if n.get("gregorian_date")],
            key=lambda x: x["gregorian_date"]
        )

        # ============================================
        # WEEKLY (Fridays / Jumu'ah)
        # ============================================
        weekly = []
        if include_weekly:
            fridays = self._get_all_fridays(year)
            for friday in fridays:
                h_y, h_m, h_d = self._gregorian_to_hijri(friday)
                weekly.append({
                    "name": self.translate({
                        "ar": "صلاة الجمعة",
                        "en": "Jumu'ah (Friday Prayer)"
                    }, lang),
                    "gregorian_date": str(friday),
                    "hijri_date": f"{h_y}/{h_m:02d}/{h_d:02d}" if h_y else None,
                    "type": "weekly",
                    "day_of_week": "Friday"
                })

        # ============================================
        # MONTHLY (White Days)
        # ============================================
        monthly = []
        if include_monthly:
            white_days_raw = self._get_white_days(hijri_year)
            for wd in white_days_raw:
                monthly.append({
                    "name": self.translate({
                        "ar": f"الأيام البيض — {wd['hijri_day']} من الشهر",
                        "en": f"White Days — Day {wd['hijri_day']} of the month"
                    }, lang),
                    "gregorian_date": wd["gregorian_date"],
                    "hijri_date": f"{hijri_year}/{wd['hijri_month']:02d}/{wd['hijri_day']:02d}",
                    "hijri_day": wd["hijri_day"],
                    "hijri_month": wd["hijri_month"],
                    "type": "monthly",
                    "description": self.translate({
                        "ar": "يستحب صيام الأيام البيض 13 و14 و15 من كل شهر هجري",
                        "en": "Recommended fasting on days 13, 14, 15 of each Hijri month"
                    }, lang)
                })

        # ============================================
        # BUILD RESPONSE
        # ============================================
        all_events = {
            "holidays": holidays,
            "months": months,
            "special_nights": special_nights_sorted,
            "weekly": weekly,
            "monthly": monthly
        }

        # Filter by type if requested
        if event_type and event_type in all_events:
            all_events = {event_type: all_events[event_type]}

        # Count total
        total = sum(len(v) for v in all_events.values())

        # Flat sorted list — useful for simple chronological iteration
        flat_events = []
        for section in all_events.values():
            flat_events.extend(section)
        flat_events = sorted(
            [e for e in flat_events if e.get("gregorian_date")],
            key=lambda x: x["gregorian_date"]
        )

        return {
            "year": year,
            "hijri_year": hijri_year,
            "total": total,
            "total_events": total,
            "calculation_method": self.translate({
                "ar": "حساب فلكي — قد يختلف يوماً واحداً بناءً على رؤية الهلال",
                "en": "Astronomical calculation — may differ by 1 day based on moon sighting"
            }, lang),
            "events": all_events,
            "events_flat": flat_events,
        }