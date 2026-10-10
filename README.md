<div align="center">

# Islam Mate API 🕌

**Open-source Islamic REST API for Muslim developers**

[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-teal.svg?style=flat-square)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/Tests-98%20passing-brightgreen.svg?style=flat-square)](#)
[![Docs](https://img.shields.io/badge/Docs-readthedocs-blue.svg?style=flat-square)](https://islam-mate-api.readthedocs.io)

[Documentation](https://islam-mate-api.readthedocs.io) · [Report Bug](https://github.com/Youssef-Mekkkawy/islam-mate-api/issues) · [Request Feature](https://github.com/Youssef-Mekkkawy/islam-mate-api/issues)

---

[English](#english) · [العربية](#arabic)

</div>

---

<a name="english"></a>

## What is Islam Mate API?

A single unified REST API that gives Muslim developers access to all essential Islamic data in one place.

No more juggling 5 different APIs. One key, everything Islamic.

---

## Features

| Module | Endpoints | Description |
|---|---|---|
| 🕐 Prayer Times | 4 | Daily times, next prayer, monthly calendar, 7 calculation methods |
| 🧭 Qibla | 1 | Direction and distance to Mecca for any location |
| 🌙 Ramadan | 2 | Suhoor/Iftar times and full calendar |
| 📅 Hijri Calendar | 4 | Conversion, months, Islamic events |
| 📿 Azkar | 4 | 130+ categories from Hisnul Muslim with audio |
| 🤲 Dua | 3 | Duas by category with transliteration |
| ✨ 99 Names of Allah | 3 | Names with meanings in Arabic and English |
| 📖 Hadith | 4 | 8 collections, 36,000+ hadiths |

---

## Quick Start

```bash
git clone https://github.com/Youssef-Mekkkawy/islam-mate-api
cd islam-mate-api
pip install -r requirements.txt
python scripts/fetch_azkar.py
python scripts/fetch_hadith.py
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

# 99 Names of Allah
curl "http://localhost:8000/api/v1/en/allah-names/random"
```

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python + FastAPI | REST API |
| SQLite | API key storage |
| SlowAPI | Rate limiting (60 req/min) |
| Loguru | Logging |
| HuggingFace | Audio and data hosting |
| Docker | Containerization |

---

## Data Sources

| Data | Source | License |
|---|---|---|
| Azkar + Dua | [Hisnul Muslim](https://hisnmuslim.com) | Official API |
| Hadith | [fawazahmed0/hadith-api](https://github.com/fawazahmed0/hadith-api) | Unlicense (Public Domain) |
| Quran Metadata | [QUL by Tarteel](https://qul.tarteel.ai) | MIT |
| Al-Sharaawi Lectures | [HuggingFace](https://huggingface.co/datasets/elprofessorai/islam-mate-data) | — |

---

## Documentation

Full documentation at **[islam-mate-api.readthedocs.io](https://islam-mate-api.readthedocs.io)**

- Getting Started
- Authentication
- Rate Limiting
- All Endpoints
- How to Use (cURL, Python, JS, PHP, Flutter, Android)
- Prayer Time Math

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

لا مزيد من استخدام 5 واجهات برمجية مختلفة. مفتاح واحد، كل شيء إسلامي.

---

## المميزات

| الوحدة | نقاط النهاية | الوصف |
|---|---|---|
| 🕐 اوقات الصلاة | 4 | الاوقات اليومية، الصلاة القادمة، التقويم الشهري، 7 طرق حساب |
| 🧭 القبلة | 1 | الاتجاه والمسافة الى مكة المكرمة لاي موقع |
| 🌙 رمضان | 2 | اوقات السحور والافطار والتقويم الكامل |
| 📅 التقويم الهجري | 4 | التحويل، الاشهر، المناسبات الاسلامية |
| 📿 الاذكار | 4 | اكثر من 130 فئة من حصن المسلم مع الصوت |
| 🤲 الادعية | 3 | ادعية مصنفة مع النص العربي |
| ✨ اسماء الله الحسنى | 3 | الاسماء مع معانيها بالعربية والانجليزية |
| 📖 الحديث | 4 | 8 مجموعات، اكثر من 36,000 حديث |

---

## البداية السريعة

```bash
git clone https://github.com/Youssef-Mekkkawy/islam-mate-api
cd islam-mate-api
pip install -r requirements.txt
python scripts/fetch_azkar.py
python scripts/fetch_hadith.py
uvicorn main:app --reload
```

افتح: http://localhost:8000/docs

---

## Docker

```bash
docker compose up
```

---

## امثلة سريعة

```bash
# اوقات الصلاة للقاهرة
curl "http://localhost:8000/api/v1/ar/prayer-times?latitude=30.04&longitude=31.23&timezone=Africa/Cairo"

# حديث عشوائي
curl "http://localhost:8000/api/v1/ar/hadith/random"

# اتجاه القبلة
curl "http://localhost:8000/api/v1/ar/qibla?latitude=30.04&longitude=31.23"
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