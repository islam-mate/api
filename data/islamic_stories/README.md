# Islamic Stories — Video Catalog

Metadata-only catalog of curated Islamic video content from YouTube.
Videos are **referenced, not hosted** — only `provider` + `video_id` are stored.
URLs are derived at read time by the consuming application.

---

## Directory Structure

```
data/islamic_stories/
├── README.md
├── index.json              ← GENERATED — complete catalog, single source of truth
├── channels/               ← GENERATED — one file per channel (filtered view)
│   ├── yousef_elkott.json
│   ├── abdulrahman_babgi.json
│   └── omar_abdulrahman.json
├── categories/             ← GENERATED — one file per category (filtered view)
│   ├── prophet_stories.json
│   ├── seerah.json
│   ├── companions.json
│   ├── miracles.json
│   ├── quran_creatures.json
│   └── islamic_history.json
├── source/                 ← MANUALLY MAINTAINED — edit these, not the outputs
│   ├── channels.json
│   ├── categories.json
│   └── videos/
│       ├── prophet_stories.json
│       ├── seerah.json
│       ├── companions.json
│       ├── miracles.json
│       ├── quran_creatures.json
│       └── islamic_history.json
├── schemas/
│   ├── catalog.schema.json
│   ├── channel.schema.json
│   └── video.schema.json
└── scripts/
    ├── scraper.py          ← pulls playlist metadata via yt-dlp
    ├── build_catalog.py    ← generates all output files from source/
    └── validate_catalog.py ← checks index.json for consistency
```

> **Rule:** Never edit `index.json`, `channels/`, or `categories/` directly.
> Edit `source/` and regenerate with `build_catalog.py`.

---

## Channels

| ID | Name | Language | Notes |
|----|------|----------|-------|
| `yousef_elkott` | يوسف القط | Arabic | Full playlists — all Islamic |
| `abdulrahman_babgi` | عبدالرحمن بابجي | Arabic | Full playlist — all Islamic |
| `omar_abdulrahman` | عمر عبدالرحمن | Arabic | Curated — channel has mixed content |

## Categories

| ID | Arabic | English |
|----|--------|---------|
| `prophet_stories` | قصص الأنبياء | Prophet Stories |
| `seerah` | السيرة النبوية | Prophetic Seerah |
| `companions` | قصص الصحابة | Companions Stories |
| `miracles` | معجزات الأنبياء | Prophets' Miracles |
| `quran_creatures` | مخلوقات القرآن | Quran Creatures |
| `islamic_history` | التاريخ الإسلامي | Islamic History |
| `afterlife` | الآخرة | Afterlife |

---

## URL Derivation

Never stored in JSON — derived by the app at read time:

```python
# YouTube embed (for in-app player)
embed_url = f"https://www.youtube.com/embed/{video_id}"

# YouTube watch (for external link)
watch_url = f"https://youtube.com/watch?v={video_id}"
```

---

## Workflow

### 1. Scrape a playlist

```bash
pip install yt-dlp

# Yousef Elkott — prophet stories
python scripts/scraper.py \
    --playlist "https://www.youtube.com/playlist?list=PL6mMw2piuhMzvk--derzlpgPu8Cv5hJm3" \
    --category prophet_stories \
    --channel yousef_elkott \
    --depth detailed

# Abdulrahman Babgi — miracles
python scripts/scraper.py \
    --playlist "https://www.youtube.com/playlist?list=PLaiWvL5dLn1Dgvmx7taT8SuwMmMx8VBvS" \
    --category miracles \
    --channel abdulrahman_babgi \
    --depth detailed

# Omar Abdulrahman — dry run first (to review before saving)
python scripts/scraper.py \
    --playlist "https://www.youtube.com/playlist?list=<playlist_id>" \
    --category prophet_stories \
    --channel omar_abdulrahman \
    --depth detailed \
    --dry-run
```

### 2. Edit the output file (manual step)

After scraping, open `source/videos/{category}.json` and:
- Add `title.en` (English translation)
- Add `prophet_id` for prophet-specific videos (e.g. `"ibrahim"`, `"musa"`)
- Remove any non-Islamic videos (Omar Abdulrahman mixed playlists)
- Adjust `depth` per video if needed

### 3. Build the catalog

```bash
python scripts/build_catalog.py

# Build + validate in one step
python scripts/build_catalog.py --validate

# Check what would be built without writing
python scripts/build_catalog.py --dry-run
```

### 4. Validate only

```bash
python scripts/validate_catalog.py
```

---

## Video Schema

```json
{
  "id": "youtube:abc123xxxxx",
  "provider": "youtube",
  "video_id": "abc123xxxxx",
  "channel_id": "yousef_elkott",
  "category_id": "prophet_stories",
  "title": {
    "ar": "قصة سيدنا إبراهيم عليه السلام",
    "en": "The Story of Prophet Ibrahim"
  },
  "language": "ar",
  "depth": "detailed",
  "duration_seconds": 1454,
  "sort_order": 1,
  "prophet_id": "ibrahim"
}
```

| Field | Required | Auto-filled | Notes |
|-------|----------|-------------|-------|
| `id` | ✅ | ✅ scraper | `"{provider}:{video_id}"` |
| `provider` | ✅ | ✅ scraper | Always `"youtube"` for now |
| `video_id` | ✅ | ✅ scraper | 11-char YouTube ID |
| `channel_id` | ✅ | ✅ scraper | Must match `source/channels.json` |
| `category_id` | ✅ | ✅ scraper | Must match `source/categories.json` |
| `title.ar` | ✅ | ✅ scraper | From yt-dlp |
| `title.en` | — | ❌ manual | Optional but useful |
| `language` | ✅ | ✅ scraper | `"ar"` default |
| `depth` | ✅ | ✅ `--depth` flag | `summary` / `detailed` / `series` |
| `duration_seconds` | ✅ | ✅ scraper | From yt-dlp |
| `sort_order` | ✅ | ✅ scraper | Playlist index |
| `prophet_id` | — | ❌ manual | Optional, for prophet filtering |