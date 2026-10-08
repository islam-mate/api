from fastapi import APIRouter, Query, HTTPException, Request
import json
import os
import random

from base.base_module import BaseModule

HF_BASE      = "https://huggingface.co/datasets/elprofessorai/islam-mate-data/resolve/main"
HF_INDEX_URL = f"{HF_BASE}/alsharaawi/index.json"
DATA_FILE    = "data/alsharaawi/index.json"


class Module(BaseModule):
    name         = "sharaawi"
    version      = "1.1.0"
    dependencies = []

    def __init__(self, service_container):
        super().__init__(service_container)
        self._index = None   # cached on first request

    # ── Route registration ────────────────────────────────────────────────────

    def register_routes(self, router: APIRouter):
        router.add_api_route("/alsharaawi/lectures",        self.get_lectures,    methods=["GET"])
        router.add_api_route("/alsharaawi/lectures/{id}",   self.get_lecture,     methods=["GET"])
        router.add_api_route("/alsharaawi/search",          self.search_lectures, methods=["GET"])
        router.add_api_route("/alsharaawi/random",          self.get_random,      methods=["GET"])
        router.add_api_route("/alsharaawi/scholar",         self.get_scholar,     methods=["GET"])

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_index(self) -> dict:
        """Load and cache index.json from local data dir."""
        if self._index is not None:
            return self._index
        if not os.path.exists(DATA_FILE):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Al-Sharaawi data not found locally.",
                    "hint": f"Download index.json from: {HF_INDEX_URL}",
                }
            )
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            self._index = json.load(f)
        return self._index

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _has_audio(self, lecture: dict) -> bool:
        return bool(lecture.get("audio_url") or lecture.get("audio_file"))

    def _has_video(self, lecture: dict) -> bool:
        return bool(lecture.get("video_url") or lecture.get("video_file"))

    def _apply_type_filter(self, lectures: list, type_lower: str) -> list:
        if type_lower in ("audio", "mp3"):
            return [l for l in lectures if self._has_audio(l)]
        if type_lower in ("video", "mp4"):
            return [l for l in lectures if self._has_video(l)]
        if type_lower == "all":
            return lectures
        raise HTTPException(status_code=400, detail=f"Invalid type '{type_lower}'. Use: audio, video, all")

    # ── Formatters ────────────────────────────────────────────────────────────

    def _format_lecture(self, lecture: dict, lang: str) -> dict:
        translations = lecture.get("translations", {})
        lang_data    = translations.get(lang, translations.get("en", {}))
        return {
            "id"           : lecture["id"],
            "title"        : lang_data.get("title", lecture.get("title_raw", "")),
            "scholar"      : lang_data.get("scholar", ""),
            "size_mb"      : lecture.get("size_mb"),
            "audio_url"    : lecture.get("audio_url") or None,
            "video_url"    : lecture.get("video_url") or None,
            "thumbnail_url": lecture.get("thumbnail_url") or None,
        }

    def _format_scholar(self, scholar: dict, lang: str) -> dict:
        return {
            "name": scholar.get(lang, scholar.get("en", "")),
            "bio" : scholar.get(f"bio_{lang}", scholar.get("bio_en", "")),
        }

    # ── Endpoints ─────────────────────────────────────────────────────────────

    async def get_lectures(
        self,
        request : Request,
        type    : str = Query("all", description="Filter by media type: audio | video | all"),
        lang    : str = Query("en",  description="Language: en or ar"),
        page    : int = Query(1,     ge=1, description="Page number"),
        limit   : int = Query(20,    ge=1, le=100, description="Items per page"),
    ):
        """List Al-Sharaawi lectures. Filter by type: audio, video, or all."""
        lang    = self.get_lang(request, lang)
        index   = self._load_index()
        all_lec = self._apply_type_filter(index.get("lectures", []), type.lower())

        total = len(all_lec)
        start = (page - 1) * limit
        end   = start + limit

        return {
            "total"   : total,
            "page"    : page,
            "limit"   : limit,
            "pages"   : (total + limit - 1) // limit,
            "type"    : type.lower(),
            "lectures": [self._format_lecture(lec, lang) for lec in all_lec[start:end]],
        }

    async def get_lecture(
        self,
        id      : int,
        request : Request,
        lang    : str = Query("en", description="Language: en or ar"),
    ):
        """Get a single lecture by ID."""
        lang  = self.get_lang(request, lang)
        index = self._load_index()
        lecture = next((l for l in index["lectures"] if l["id"] == id), None)
        if not lecture:
            raise HTTPException(status_code=404, detail=f"Lecture {id} not found.")
        return self._format_lecture(lecture, lang)

    async def search_lectures(
        self,
        request : Request,
        q       : str = Query(..., min_length=1, description="Search query (Arabic or English)"),
        type    : str = Query("all", description="Filter by media type: audio | video | all"),
        lang    : str = Query("en",  description="Language: en or ar"),
        page    : int = Query(1,     ge=1),
        limit   : int = Query(20,    ge=1, le=100),
    ):
        """Search lectures by title in Arabic or English."""
        lang  = self.get_lang(request, lang)
        index = self._load_index()
        q_low = q.lower()

        matches = [
            lec for lec in index["lectures"]
            if (
                q_low in lec.get("translations", {}).get("en", {}).get("title", "").lower()
                or q    in lec.get("translations", {}).get("ar", {}).get("title", "")
                or q_low in lec.get("title_raw", "").lower()
            )
        ]
        matches = self._apply_type_filter(matches, type.lower())

        total = len(matches)
        start = (page - 1) * limit
        end   = start + limit

        return {
            "query"   : q,
            "total"   : total,
            "page"    : page,
            "limit"   : limit,
            "pages"   : (total + limit - 1) // limit,
            "type"    : type.lower(),
            "lectures": [self._format_lecture(lec, lang) for lec in matches[start:end]],
        }

    async def get_random(
        self,
        request : Request,
        type    : str = Query("all", description="Filter by media type: audio | video | all"),
        lang    : str = Query("en",  description="Language: en or ar"),
    ):
        """Return a random lecture."""
        lang     = self.get_lang(request, lang)
        index    = self._load_index()
        lectures = self._apply_type_filter(index.get("lectures", []), type.lower())

        if not lectures:
            raise HTTPException(status_code=503, detail="No lectures available for this filter.")

        return self._format_lecture(random.choice(lectures), lang)

    async def get_scholar(
        self,
        request : Request,
        lang    : str = Query("en", description="Language: en or ar"),
    ):
        """Return Al-Sharaawi scholar information and stats."""
        lang    = self.get_lang(request, lang)
        index   = self._load_index()
        scholar = index.get("scholar", {})
        return {
            "scholar"       : self._format_scholar(scholar, lang),
            "total_lectures": index.get("total_files", 0),
            "audio_count"   : index.get("audio_count", 0),
            "video_count"   : index.get("video_count", 0),
        }
