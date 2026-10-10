from fastapi import APIRouter, Query, HTTPException, Request
import json
import os
import random

from base.base_module import BaseModule

HF_BASE         = "https://huggingface.co/datasets/elprofessorai/islam-mate-data/resolve/main"
HF_METADATA_URL = f"{HF_BASE}/adhan/metadata.json"
DATA_FILE       = "data/adhan/metadata.json"


class Module(BaseModule):
    name         = "adhan"
    version      = "1.1.0"
    dependencies = []

    def __init__(self, service_container):
        super().__init__(service_container)
        self._recordings   = None
        self._by_muezzin   = None
        self._muezzin_list = None

    def register_routes(self, router: APIRouter):
        router.add_api_route("/adhan/muezzins",       self.get_muezzins, methods=["GET"])
        router.add_api_route("/adhan/muezzins/{id}",  self.get_muezzin,  methods=["GET"])
        router.add_api_route("/adhan/random",         self.get_random,   methods=["GET"])
        router.add_api_route("/adhan",                self.get_all,      methods=["GET"])
        router.add_api_route("/adhan/{id}",           self.get_adhan,    methods=["GET"])

    def _load(self):
        if self._recordings is not None:
            return
        if not os.path.exists(DATA_FILE):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Adhan data not found locally.",
                    "hint": f"Download metadata.json from: {HF_METADATA_URL}",
                    "path": DATA_FILE,
                }
            )
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            self._recordings = json.load(f)
        grouped = {}
        for rec in self._recordings:
            slug = rec.get("muezzin", "unknown")
            grouped.setdefault(slug, []).append(rec)
        def _slug_key(s):
            return (1 if s == "unknown" else 0, s)
        self._by_muezzin = grouped
        self._muezzin_list = []
        for idx, slug in enumerate(sorted(grouped.keys(), key=_slug_key), start=1):
            recs = grouped[slug]
            derived = slug.replace("_", " ").title()
            self._muezzin_list.append({
                "id": idx, "slug": slug,
                "name_ar": derived, "name_en": derived,
                "count": len(recs), "recordings": recs,
            })

    def _fmt_rec(self, rec: dict, lang: str) -> dict:
        return {
            "id"       : rec["id"],
            "title"    : rec.get("title_ar", "") if lang == "ar" else rec.get("title_en", ""),
            "title_ar" : rec.get("title_ar", ""),
            "title_en" : rec.get("title_en", ""),
            "muezzin"  : rec.get("muezzin", ""),
            "filename" : rec.get("filename", ""),
            "audio_url": rec.get("audio_url") or None,
        }

    def _fmt_muezzin(self, m: dict, lang: str, include_recordings: bool = False) -> dict:
        result = {
            "id": m["id"], "slug": m["slug"],
            "name": m["name_ar"] if lang == "ar" else m["name_en"],
            "name_ar": m["name_ar"], "name_en": m["name_en"],
            "count": m["count"],
        }
        if include_recordings:
            result["recordings"] = [self._fmt_rec(r, lang) for r in m["recordings"]]
        return result

    async def get_all(self, request: Request,
                      lang: str = Query("en"), page: int = Query(1, ge=1),
                      limit: int = Query(20, ge=1, le=100)):
        lang = self.get_lang(request, lang)
        self._load()
        total = len(self._recordings)
        start = (page - 1) * limit
        return {
            "total": total, "page": page, "limit": limit,
            "pages": (total + limit - 1) // limit,
            "recordings": [self._fmt_rec(r, lang) for r in self._recordings[start:start + limit]],
        }

    async def get_muezzins(self, request: Request, lang: str = Query("en")):
        lang = self.get_lang(request, lang)
        self._load()
        return {"total": len(self._muezzin_list),
                "muezzins": [self._fmt_muezzin(m, lang) for m in self._muezzin_list]}

    async def get_muezzin(self, id: int, request: Request, lang: str = Query("en")):
        lang = self.get_lang(request, lang)
        self._load()
        m = next((m for m in self._muezzin_list if m["id"] == id), None)
        if not m:
            raise HTTPException(status_code=404, detail=f"Muezzin {id} not found.")
        return self._fmt_muezzin(m, lang, include_recordings=True)

    async def get_adhan(self, id: int, request: Request, lang: str = Query("en")):
        lang = self.get_lang(request, lang)
        self._load()
        rec = next((r for r in self._recordings if r["id"] == id), None)
        if not rec:
            raise HTTPException(status_code=404, detail=f"Adhan recording {id} not found.")
        return self._fmt_rec(rec, lang)

    async def get_random(self, request: Request, lang: str = Query("en")):
        lang = self.get_lang(request, lang)
        self._load()
        if not self._recordings:
            raise HTTPException(status_code=503, detail="No adhan data available.")
        import random
        return self._fmt_rec(random.choice(self._recordings), lang)
