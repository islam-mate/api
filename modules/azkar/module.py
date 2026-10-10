from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional
import json
import os
import random

from base.base_module import BaseModule

HF_BASE = "https://huggingface.co/datasets/elprofessorai/islam-mate-data/resolve/main"
DATA_DIR = "data/azkar"


class Module(BaseModule):
    name = "azkar"
    version = "1.0.0"
    dependencies = []

    def __init__(self, service_container):
        super().__init__(service_container)
        self._index = None
        self._cache = {}

    def register_routes(self, router: APIRouter):
        router.add_api_route("/azkar", self.get_categories, methods=["GET"])
        router.add_api_route("/azkar/{category_id}", self.get_azkar, methods=["GET"])
        router.add_api_route("/azkar/slug/{slug}", self.get_azkar_by_slug, methods=["GET"])
        router.add_api_route("/azkar/random/item", self.get_random, methods=["GET"])

    def _load_index(self):
        if self._index is not None:
            return self._index
        index_path = f"{DATA_DIR}/index.json"
        if not os.path.exists(index_path):
            raise HTTPException(503, "Azkar data not found.")
        with open(index_path, "r", encoding="utf-8-sig") as f:
            self._index = json.load(f)
        return self._index

    def _load_category(self, filename: str):
        if filename in self._cache:
            return self._cache[filename]
        filepath = f"{DATA_DIR}/{filename}"
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        self._cache[filename] = data
        return data

    def _format_category(self, cat: dict, lang: str) -> dict:
        audio_file = cat.get("audio_file", "")
        return {
            "id": cat["id"],
            "slug": cat["slug"],
            "title": self.translate(cat.get("title", {}), lang),
            "count": cat["count"],
            "audio_url": f"{HF_BASE}/azkar/audio/{audio_file}" if audio_file else ""
        }

    def _format_azkar_item(self, item: dict, lang: str) -> dict:
        audio_file = item.get("audio_file", "")
        return {
            "id": item["id"],
            "repeat": item.get("repeat", 1),
            "source": item.get("source", ""),
            "transliteration": item.get("transliteration", ""),
            "text": self.translate({
                "ar": item.get("translations", {}).get("ar", {}).get("text", ""),
                "en": item.get("translations", {}).get("en", {}).get("text", "")
            }, lang),
            "description": self.translate({
                "ar": item.get("translations", {}).get("ar", {}).get("description", ""),
                "en": item.get("translations", {}).get("en", {}).get("description", "")
            }, lang),
            "audio_url": f"{HF_BASE}/azkar/audio/{audio_file}" if audio_file else ""
        }

    async def get_categories(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        index = self._load_index()
        return {
            "total": index["total"],
            "categories": [self._format_category(cat, lang) for cat in index["categories"]]
        }

    async def get_azkar(
        self,
        category_id: int,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        index = self._load_index()
        cat_meta = next((c for c in index["categories"] if c["id"] == category_id), None)
        if not cat_meta:
            raise HTTPException(404, f"Category {category_id} not found")
        data = self._load_category(cat_meta["file"])
        if not data:
            raise HTTPException(404, "Category data file not found")
        return {
            "id": data["id"],
            "slug": data["slug"],
            "title": self.translate(data.get("title", {}), lang),
            "audio_url": f"{HF_BASE}/azkar/audio/{data.get('audio_file', '')}" if data.get("audio_file") else "",
            "total": len(data["azkar"]),
            "azkar": [self._format_azkar_item(item, lang) for item in data["azkar"]]
        }

    async def get_azkar_by_slug(
        self,
        slug: str,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        index = self._load_index()
        cat_meta = next((c for c in index["categories"] if c["slug"] == slug), None)
        if not cat_meta:
            raise HTTPException(404, f"Category '{slug}' not found")
        return await self.get_azkar(cat_meta["id"], request, lang)

    async def get_random(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        index = self._load_index()
        categories = index["categories"]

        for _ in range(20):
            cat_meta = random.choice(categories)
            data = self._load_category(cat_meta["file"])
            if data and data.get("azkar"):
                item = random.choice(data["azkar"])
                return {
                    "category": self.translate(data.get("title", {}), lang),
                    "azkar": self._format_azkar_item(item, lang)
                }

        raise HTTPException(503, "No azkar data available")


