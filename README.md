<div align="center">

# Islam Mate API 🕌

**Open-source Islamic REST API for Muslim developers**

[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-teal.svg?style=flat-square)](https://fastapi.tiangolo.com)
[![Docs](https://img.shields.io/badge/Docs-readthedocs-blue.svg?style=flat-square)](https://islam-mate-api.readthedocs.io)

[Documentation](https://islam-mate-api.readthedocs.io) · [Report Bug](https://github.com/islam-mate/api/issues) · [Request Feature](https://github.com/islam-mate/api/issues)

---

[English](#english) · [العربية](#arabic)

</div>

---

<a name="english"></a>

## What is Islam Mate API?

A single unified REST API that gives Muslim developers access to all essential Islamic data in one place.

No more juggling multiple APIs. One codebase, everything Islamic.

---

## Features

| Module | Description |
|---|---|
| 🕐 **Prayer Times** | Daily prayer times for any location, next prayer countdown, monthly calendar, 7 calculation methods (MWL, ISNA, Egypt, Makkah, Karachi, Tehran, Jafari) |
| 🧭 **Qibla** | Qibla direction and distance to Mecca for any coordinates |
| 🌙 **Ramadan** | Suhoor/Iftar times and full Ramadan calendar |
| 📅 **Hijri Calendar** | Hijri ↔ Gregorian conversion, Islamic months, upcoming events |
| 📿 **Azkar** | 130+ categories from Hisnul Muslim — morning, evening, prayer, sleep, and more |
| 🤲 **Dua** | Duas by category with Arabic text and transliteration |
| ✨ **99 Names of Allah** | All 99 names with meanings in Arabic and English |
| 📖 **Hadith** | 8 major collections, 36,000+ hadiths — search, random, by collection |
| 📍 **Location** | City and country lookup with coordinates, timezone, and region data |
| 🗓️ **Islamic Events** | Full Islamic calendar events with Hijri and Gregorian dates |
| 💰 **Zakat** | Zakat calculator for gold, silver, cash, and trade goods — with nisab thresholds |
| 🎙️ **Al-Sharaawi** | Catalog of Sheikh Muhammad Metwally Al-Sharaawi lectures |
| 🔊 **Adhan** | Adhan audio catalog by muezzin and style |
| 📚 **Islamic Stories** | 184 curated Islamic videos across 6 categories — Prophet Stories, Seerah, Companions, Miracles, Quran Creatures, Afterlife |

---

## Quick Start

```bash
git clone https://github.com/islam-mate/api
cd api
pip install -r requirements.txt
uvicorn main:app --reload
```

Open: http://localhost:8000/docs

---

## Docker

```bash
docker compose up
```

---

## API Usage

### Language Support

All endpoints support Arabic and English via the URL prefix:

```bash
# English
curl "http://localhost:8000/api/v1/en/prayer-times?latitude=30.04&longitude=31.23&timezone=Africa/Cairo"

# Arabic
curl "http://localhost:8000/api/v1/ar/prayer-times?latitude=30.04&longitude=31.23&timezone=Africa/Cairo"
```

### Quick Examples

```bash
# Prayer times for Cairo
curl "http://localhost:8000/api/v1/en/prayer-times?latitude=30.04&longitude=31.23&timezone=Africa/Cairo"

# Random Hadith
curl "http://localhost:8000/api/v1/en/hadith/random"

# Qibla direction
curl "http://localhost:8000/api/v1/en/qibla?latitude=30.04&longitude=31.23"

# 99 Names of Allah (random)
curl "http://localhost:8000/api/v1/en/allah-names/random"

# Zakat calculator
curl -X POST "http://localhost:8000/api/v1/en/zakat/calculate" \
  -H "Content-Type: application/json" \
  -d '{"gold_grams": 100, "silver_grams": 0, "cash": 5000}'

# Islamic Stories by category
curl "http://localhost:8000/api/v1/en/islamic-stories?category=prophet_stories"
```

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python + FastAPI | REST API framework |
| SQLite / PostgreSQL | Storage (SQLite default, PostgreSQL for production) |
| SlowAPI | Rate limiting (60 req/min) |
| Loguru | Structured logging |
| HuggingFace | Audio and dataset hosting |
| Docker | Containerization |
| yt-dlp | Islamic video catalog pipeline |

---

## Data Sources

| Data | Source | License |
|---|---|---|
| Azkar + Dua | [Hisnul Muslim](https://hisnmuslim.com) | Official API |
| Hadith | [fawazahmed0/hadith-api](https://github.com/fawazahmed0/hadith-api) | Unlicense (Public Domain) |
| Quran Metadata | [QUL by Tarteel](https://qul.tarteel.ai) | MIT |
| Al-Sharaawi Lectures | [HuggingFace](https://huggingface.co/datasets/elprofessorai/islam-mate-data) | — |
| Islamic Stories | YouTube (curated channels) | — |

---

## Documentation

Full documentation at **[islam-mate-api.readthedocs.io](https://islam-mate-api.readthedocs.io)**

- Getting Started
- Authentication
- Rate Limiting
- All Endpoints Reference
- Code Examples (cURL, Python, JavaScript, PHP, Flutter, Android)
- Prayer Time Calculation Methods

---

## Contributing

Contributions are welcome! See [Contributing Guide](https://islam-mate-api.readthedocs.io/en/contributing/index).

---

## License

MIT License — free to use, modify, and distribute.

---

<a name="arabic"></a>

<div dir="rtl">

## ما هي Islam Mate API؟

واجهة برمجية REST موحدة تمنح المطورين المسلمين الوصول إلى جميع البيانات الإسلامية الأساسية في مكان واحد.

لا مزيد من استخدام واجهات برمجية متعددة. قاعدة كود واحدة، كل شيء إسلامي.

---

## المميزات

| الوحدة | الوصف |
|---|---|
| 🕐 **أوقات الصلاة** | أوقات الصلاة اليومية لأي موقع، العد التنازلي للصلاة القادمة، التقويم الشهري، 7 طرق حساب |
| 🧭 **القبلة** | اتجاه القبلة والمسافة إلى مكة المكرمة لأي إحداثيات |
| 🌙 **رمضان** | أوقات السحور والإفطار والتقويم الكامل لشهر رمضان |
| 📅 **التقويم الهجري** | تحويل التاريخ هجري ↔ ميلادي، الأشهر الإسلامية، المناسبات القادمة |
| 📿 **الأذكار** | أكثر من 130 فئة من حصن المسلم — أذكار الصباح والمساء والصلاة والنوم وغيرها |
| 🤲 **الأدعية** | أدعية مصنفة مع النص العربي والنطق |
| ✨ **أسماء الله الحسنى** | جميع الأسماء الـ 99 مع معانيها بالعربية والإنجليزية |
| 📖 **الحديث** | 8 مجموعات كبرى، أكثر من 36,000 حديث — بحث، عشوائي، حسب المجموعة |
| 📍 **الموقع** | البحث عن المدن والدول مع الإحداثيات والمنطقة الزمنية |
| 🗓️ **المناسبات الإسلامية** | تقويم المناسبات الإسلامية بالتاريخين الهجري والميلادي |
| 💰 **الزكاة** | حاسبة زكاة الذهب والفضة والنقود وعروض التجارة مع نصاب محدّث |
| 🎙️ **الشعراوي** | فهرس محاضرات الشيخ محمد متولي الشعراوي |
| 🔊 **الأذان** | فهرس تسجيلات الأذان بأصوات وأساليب مختلفة |
| 📚 **القصص الإسلامية** | 184 فيديو إسلامي منتقى في 6 تصنيفات — قصص الأنبياء، السيرة، الصحابة، المعجزات، مخلوقات القرآن، الآخرة |

---

## البداية السريعة

```bash
git clone https://github.com/islam-mate/api
cd api
pip install -r requirements.txt
uvicorn main:app --reload
```

افتح: http://localhost:8000/docs

---

## أمثلة سريعة

```bash
# أوقات الصلاة للقاهرة
curl "http://localhost:8000/api/v1/ar/prayer-times?latitude=30.04&longitude=31.23&timezone=Africa/Cairo"

# حديث عشوائي
curl "http://localhost:8000/api/v1/ar/hadith/random"

# اتجاه القبلة
curl "http://localhost:8000/api/v1/ar/qibla?latitude=30.04&longitude=31.23"

# حاسبة الزكاة
curl -X POST "http://localhost:8000/api/v1/ar/zakat/calculate" \
  -H "Content-Type: application/json" \
  -d '{"gold_grams": 100, "silver_grams": 0, "cash": 5000}'
```

---

## التوثيق

التوثيق الكامل على **[islam-mate-api.readthedocs.io](https://islam-mate-api.readthedocs.io)**

---

## المساهمة

نرحب بمساهماتك! راجع [دليل المساهمة](https://islam-mate-api.readthedocs.io/ar/contributing/index).

---

## الرخصة

رخصة MIT — مجاني للاستخدام والتعديل والتوزيع.

</div>

---

<div align="center">
Made with ❤️ for the Muslim developer community
</div>