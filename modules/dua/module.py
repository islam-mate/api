from fastapi import APIRouter, Query, HTTPException, Request
import json
import os
import random

from base.base_module import BaseModule

DATA_DIR = "data/dua"


class Module(BaseModule):
    name = "dua"
    version = "1.0.0"
    dependencies = []

    def __init__(self, service_container):
        super().__init__(service_container)
        self._cache = {}

    def register_routes(self, router: APIRouter):
        router.add_api_route("/dua", self.get_categories, methods=["GET"])
        router.add_api_route("/dua/random", self.get_random, methods=["GET"])
        router.add_api_route("/dua/{category}", self.get_dua, methods=["GET"])

    def _load_category(self, category: str) -> dict:
        if category in self._cache:
            return self._cache[category]
        filepath = f"{DATA_DIR}/{category}.json"
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        self._cache[category] = data
        return data

    def _get_all_categories(self) -> list:
        if not os.path.exists(DATA_DIR):
            return []
        return [
            f.replace(".json", "")
            for f in os.listdir(DATA_DIR)
            if f.endswith(".json")
        ]

    def _format_dua(self, item: dict, lang: str) -> dict:
        return {
            "id": item.get("id"),
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
            }, lang)
        }

    async def get_categories(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        categories = self._get_all_categories()
        result = []
        for cat in sorted(categories):
            data = self._load_category(cat)
            if data:
                title = data.get("title", {})
                result.append({
                    "category": cat,
                    "title": self.translate(title, lang) if isinstance(title, dict) else cat,
                    "count": len(data.get("duas", []))
                })
        return {
            "total": len(result),
            "categories": result
        }

    async def get_dua(
        self,
        category: str,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        data = self._load_category(category)
        if not data:
            raise HTTPException(404, f"Category '{category}' not found")
        duas = data.get("duas", [])
        return {
            "category": category,
            "total": len(duas),
            "duas": [self._format_dua(d, lang) for d in duas]
        }

    async def get_random(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        categories = self._get_all_categories()
        if not categories:
            raise HTTPException(404, "No dua data found")
        category = random.choice(categories)
        data = self._load_category(category)
        if not data or not data.get("duas"):
            raise HTTPException(404, "No duas found")
        item = random.choice(data["duas"])
        return {
            "category": category,
            "dua": self._format_dua(item, lang)
        }
