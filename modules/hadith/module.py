from fastapi import APIRouter, Query, HTTPException, Request
import json
import os
import random

from base.base_module import BaseModule

DATA_DIR = "data/hadith"


class Module(BaseModule):
    name = "hadith"
    version = "1.0.0"
    dependencies = []

    def __init__(self, service_container):
        super().__init__(service_container)
        self._index = None
        self._cache = {}

    def register_routes(self, router: APIRouter):
        router.add_api_route("/hadith", self.get_collections, methods=["GET"])
        router.add_api_route("/hadith/random", self.get_random, methods=["GET"])
        router.add_api_route("/hadith/{collection}", self.get_collection, methods=["GET"])
        router.add_api_route("/hadith/{collection}/{number}", self.get_by_number, methods=["GET"])

    def _load_index(self):
        if self._index is not None:
            return self._index
        path = f"{DATA_DIR}/index.json"
        if not os.path.exists(path):
            raise HTTPException(503, "Hadith data not found. Run fetch_hadith.py first.")
        with open(path, "r", encoding="utf-8") as f:
            self._index = json.load(f)
        return self._index

    def _load_collection(self, collection_id: str):
        if collection_id in self._cache:
            return self._cache[collection_id]
        path = f"{DATA_DIR}/{collection_id}.json"
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._cache[collection_id] = data
        return data

    def _format_hadith(self, hadith: dict, lang: str) -> dict:
        return {
            "number": hadith.get("number"),
            "grade": hadith.get("grade", ""),
            "text": self.translate(hadith.get("text", {}), lang),
            "reference": hadith.get("reference", {})
        }

    async def get_collections(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        index = self._load_index()
        return {
            "total_collections": index["total_collections"],
            "collections": [
                {
                    "id": col["id"],
                    "name": self.translate(col["name"], lang),
                    "total": col["total"]
                }
                for col in index["collections"]
            ]
        }

    async def get_collection(
        self,
        collection: str,
        request: Request,
        lang: str = Query("en", description="Language: en or ar"),
        page: int = Query(1, description="Page number", ge=1),
        limit: int = Query(50, description="Results per page", ge=1, le=200)
    ):
        lang = self.get_lang(request, lang)
        data = self._load_collection(collection)
        if not data:
            raise HTTPException(404, f"Collection '{collection}' not found")

        hadiths = data.get("hadiths", [])
        total = len(hadiths)
        start = (page - 1) * limit
        end = start + limit
        page_data = hadiths[start:end]

        return {
            "collection": collection,
            "name": self.translate(data.get("name", {}), lang),
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "hadiths": [self._format_hadith(h, lang) for h in page_data]
        }

    async def get_by_number(
        self,
        collection: str,
        number: int,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        data = self._load_collection(collection)
        if not data:
            raise HTTPException(404, f"Collection '{collection}' not found")

        hadith = next(
            (h for h in data.get("hadiths", []) if h.get("number") == number),
            None
        )
        if not hadith:
            raise HTTPException(404, f"Hadith {number} not found in {collection}")

        return {
            "collection": collection,
            "hadith": self._format_hadith(hadith, lang)
        }

    async def get_random(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar"),
        collection: str = Query(None, description="Specific collection (optional)")
    ):
        lang = self.get_lang(request, lang)
        index = self._load_index()

        if collection:
            data = self._load_collection(collection)
            if not data:
                raise HTTPException(404, f"Collection '{collection}' not found")
        else:
            col = random.choice(index["collections"])
            data = self._load_collection(col["id"])
            collection = col["id"]

        hadiths = data.get("hadiths", [])
        if not hadiths:
            raise HTTPException(404, "No hadiths found")

        hadith = random.choice(hadiths)
        return {
            "collection": collection,
            "hadith": self._format_hadith(hadith, lang)
        }
