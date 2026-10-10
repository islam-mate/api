from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional
import json
import os
import random

from base.base_module import BaseModule

HF_BASE   = "https://huggingface.co/datasets/elprofessorai/islam-mate-data/resolve/main"
DATA_FILE = "data/alsharaawi/index.json"


class Module(BaseModule):
    name         = "alsharaawi"
    version      = "1.0.0"
    dependencies = []

    def __init__(self, service_container):
        super().__init__(service_container)
        self._data = None   # cached on first request

    # ── Route registration ────────────────────────────────────────────────────

    def register_routes(self, router: APIRouter):
        router.add_api_route("/alsharaawi",          self.get_all,     methods=["GET"])
        router.add_api_route("/alsharaawi/search",   self.search,      methods=["GET"])
        router.add_api_route("/alsharaawi/random",   self.get_random,  methods=["GET"])
        router.add_api_route("/alsharaawi/{id}",     self.get_lecture, methods=["GET"])

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if self._data is not None:
            return self._data
        if not os.path.exists(DATA_FILE):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Al-Sharaawi data not found locally.",
                    "hint": f"Place index.json at: {DATA_FILE}",
                }
            )
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        return self._data

    # ── Formatter ─────────────────────────────────────────────────────────────

    def _format_lecture(self, lec: dict, lang: str) -> dict:
        tr = lec.get("translations", {})
        title = tr.get(lang, tr.get("en", {})).get("title", lec.get("title_clean", lec.get("title_raw", "")))
        return {
            "id"           : lec["id"],
            "title"        : title,
            "title_clean"  : lec.get("title_clean", ""),
            "filename"     : lec.get("filename", ""),
            "type"         : lec.get("type", "audio"),
            "size_mb"      : lec.get("size_mb", 0),
            "audio_url"    : lec.get("audio_url") or None,
            "video_url"    : lec.get("video_url") or None,
            "thumbnail_url": lec.get("thumbnail_url") or None,
        }

    # ── Endpoints ─────────────────────────────────────────────────────────────

    async def get_all(
        self,
        request: Request,
        lang   : str          = Query("en",  description="Language: en or ar"),
        type   : Optional[str]= Query(None,  description="Filter: audio | audio_video | all"),
        page   : int          = Query(1,     ge=1, description="Page number"),
        limit  : int          = Query(20,    ge=1, le=100, description="Items per page"),
    ):
        """List all Al-Sharaawi lectures (paginated, filterable by type)."""
        lang = self.get_lang(request, lang)
        data = self._load()

        lectures = data["lectures"]

        if type and type != "all":
            lectures = [l for l in lectures if l.get("type") == type]

        total = len(lectures)
        start = (page - 1) * limit
        end   = start + limit

        return {
            "scholar" : data.get("scholar", {}),
            "total"   : total,
            "page"    : page,
            "limit"   : limit,
            "pages"   : (total + limit - 1) // limit,
            "lectures": [self._format_lecture(l, lang) for l in lectures[start:end]],
        }

    async def get_lecture(
        self,
        id     : int,
        request: Request,
        lang   : str = Query("en", description="Language: en or ar"),
    ):
        """Get a single lecture by ID."""
        lang = self.get_lang(request, lang)
        data = self._load()

        lec = next((l for l in data["lectures"] if l["id"] == id), None)
        if not lec:
            raise HTTPException(status_code=404, detail=f"Lecture {id} not found.")

        result = self._format_lecture(lec, lang)
        result["scholar"] = data.get("scholar", {})
        return result

    async def search(
        self,
        request: Request,
        q      : str = Query(..., min_length=1, description="Search by title or surah name"),
        lang   : str = Query("en", description="Language: en or ar"),
        page   : int = Query(1, ge=1),
        limit  : int = Query(20, ge=1, le=100),
    ):
        """Search lectures by title."""
        lang = self.get_lang(request, lang)
        data = self._load()

        q_low = q.lower()
        matches = [
            l for l in data["lectures"]
            if q_low in l.get("title_clean", "").lower()
            or q_low in l.get("title_raw", "").lower()
            or q_low in l.get("filename", "").lower()
        ]

        total = len(matches)
        start = (page - 1) * limit
        end   = start + limit

        return {
            "query"   : q,
            "total"   : total,
            "page"    : page,
            "limit"   : limit,
            "pages"   : (total + limit - 1) // limit,
            "lectures": [self._format_lecture(l, lang) for l in matches[start:end]],
        }

    async def get_random(
        self,
        request: Request,
        lang   : str          = Query("en", description="Language: en or ar"),
        type   : Optional[str]= Query(None, description="Filter: audio | audio_video"),
    ):
        """Return a random lecture."""
        lang = self.get_lang(request, lang)
        data = self._load()

        lectures = data["lectures"]
        if type and type != "all":
            lectures = [l for l in lectures if l.get("type") == type]

        if not lectures:
            raise HTTPException(status_code=503, detail="No lectures available.")

        lec    = random.choice(lectures)
        result = self._format_lecture(lec, lang)
        result["scholar"] = data.get("scholar", {})
        return result
