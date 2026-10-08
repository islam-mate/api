from fastapi import APIRouter, Query, HTTPException, Request
import json
import os
import random

from base.base_module import BaseModule

HF_BASE = "https://huggingface.co/datasets/elprofessorai/islam-mate-data/resolve/main"
HF_INDEX_URL = f"{HF_BASE}/adhan/index.json"
DATA_FILE = "data/adhan/index.json"


class Module(BaseModule):
    name = "adhan"
    version = "1.0.0"
    dependencies = []

    def __init__(self, service_container):
        super().__init__(service_container)
        self._index = None   # cached on first request

    # ── Route registration ────────────────────────────────────────────────────

    def register_routes(self, router: APIRouter):
        router.add_api_route("/adhan/muezzins",
                             self.get_muezzins, methods=["GET"])
        router.add_api_route(
            "/adhan/muezzins/{id}",  self.get_muezzin,  methods=["GET"])
        router.add_api_route("/adhan/random",
                             self.get_random,   methods=["GET"])
        router.add_api_route(
            "/adhan",                self.get_all,      methods=["GET"])
        router.add_api_route("/adhan/{id}",
                             self.get_adhan,    methods=["GET"])

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_index(self) -> dict:
        if self._index is not None:
            return self._index
        if not os.path.exists(DATA_FILE):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Adhan data not found locally.",
                    "hint": f"Download index.json from: {HF_INDEX_URL}",
                }
            )
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            self._index = json.load(f)
        return self._index

    # ── Formatters ────────────────────────────────────────────────────────────

    def _format_recording(self, rec: dict, lang: str) -> dict:
        return {
            "id": rec["id"],
            "title": rec.get("title_ar", "") if lang == "ar" else rec.get("title_en", ""),
            "title_ar": rec.get("title_ar", ""),
            "title_en": rec.get("title_en", ""),
            "filename": rec.get("filename", ""),
            "audio_url": rec.get("audio_url") or None,
        }

    def _format_muezzin(self, muezzin: dict, lang: str, include_recordings: bool = False) -> dict:
        name_obj = muezzin.get("name", {})
        result = {
            "id": muezzin["id"],
            "slug": muezzin["slug"],
            "name": name_obj.get("ar", "") if lang == "ar" else name_obj.get("en", ""),
            "name_ar": name_obj.get("ar", ""),
            "name_en": name_obj.get("en", ""),
            "count": muezzin.get("count", len(muezzin.get("recordings", []))),
        }
        if include_recordings:
            result["recordings"] = [
                self._format_recording(r, lang) for r in muezzin.get("recordings", [])
            ]
        return result

    # ── Endpoints ─────────────────────────────────────────────────────────────

    async def get_all(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar"),
        page: int = Query(1,   ge=1, description="Page number"),
        limit: int = Query(20,  ge=1, le=100, description="Items per page"),
    ):
        """List all adhan recordings (flat, paginated)."""
        lang = self.get_lang(request, lang)
        index = self._load_index()

        # Flatten all recordings across muezzins
        all_recordings = []
        for m in index["muezzins"]:
            for rec in m.get("recordings", []):
                all_recordings.append((m, rec))

        total = len(all_recordings)
        start = (page - 1) * limit
        end = start + limit

        items = []
        for muezzin, rec in all_recordings[start:end]:
            fmt = self._format_recording(rec, lang)
            name_obj = muezzin.get("name", {})
            fmt["muezzin_id"] = muezzin["id"]
            fmt["muezzin_slug"] = muezzin["slug"]
            fmt["muezzin_name"] = name_obj.get(
                "ar", "") if lang == "ar" else name_obj.get("en", "")
            items.append(fmt)

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "recordings": items,
        }

    async def get_muezzins(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar"),
    ):
        """List all muezzins (without their recordings)."""
        lang = self.get_lang(request, lang)
        index = self._load_index()

        return {
            "total": index["total_muezzins"],
            "muezzins": [self._format_muezzin(m, lang) for m in index["muezzins"]],
        }

    async def get_muezzin(
        self,
        id: int,
        request: Request,
        lang: str = Query("en", description="Language: en or ar"),
    ):
        """Get a single muezzin with all their recordings."""
        lang = self.get_lang(request, lang)
        index = self._load_index()

        muezzin = next((m for m in index["muezzins"] if m["id"] == id), None)
        if not muezzin:
            raise HTTPException(
                status_code=404, detail=f"Muezzin {id} not found.")

        return self._format_muezzin(muezzin, lang, include_recordings=True)

    async def get_adhan(
        self,
        id: int,
        request: Request,
        lang: str = Query("en", description="Language: en or ar"),
    ):
        """Get a single adhan recording by its ID."""
        lang = self.get_lang(request, lang)
        index = self._load_index()

        for muezzin in index["muezzins"]:
            for rec in muezzin.get("recordings", []):
                if rec["id"] == id:
                    fmt = self._format_recording(rec, lang)
                    name_obj = muezzin.get("name", {})
                    fmt["muezzin_id"] = muezzin["id"]
                    fmt["muezzin_slug"] = muezzin["slug"]
                    fmt["muezzin_name"] = name_obj.get(
                        "ar", "") if lang == "ar" else name_obj.get("en", "")
                    return fmt

        raise HTTPException(
            status_code=404, detail=f"Adhan recording {id} not found.")

    async def get_random(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar"),
    ):
        """Return a random adhan recording."""
        lang = self.get_lang(request, lang)
        index = self._load_index()

        candidates = [m for m in index["muezzins"] if m.get("recordings")]
        if not candidates:
            raise HTTPException(
                status_code=503, detail="No adhan data available.")

        muezzin = random.choice(candidates)
        rec = random.choice(muezzin["recordings"])

        fmt = self._format_recording(rec, lang)
        name_obj = muezzin.get("name", {})
        fmt["muezzin_id"] = muezzin["id"]
        fmt["muezzin_slug"] = muezzin["slug"]
        fmt["muezzin_name"] = name_obj.get(
            "ar", "") if lang == "ar" else name_obj.get("en", "")
        return fmt
