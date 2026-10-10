from fastapi import APIRouter, Query, HTTPException, Request
import json
import os
import random

from base.base_module import BaseModule

DATA_FILE = "data/allah_names/names.json"


class Module(BaseModule):
    name = "allah_names"
    version = "1.0.0"
    dependencies = []

    def __init__(self, service_container):
        super().__init__(service_container)
        self._data = None

    def register_routes(self, router: APIRouter):
        router.add_api_route("/allah-names", self.get_all, methods=["GET"])
        router.add_api_route("/allah-names/random", self.get_random, methods=["GET"])
        router.add_api_route("/allah-names/{number}", self.get_by_number, methods=["GET"])

    def _load(self):
        if self._data is not None:
            return self._data
        if not os.path.exists(DATA_FILE):
            raise HTTPException(503, "Names data not found")
        with open(DATA_FILE, "r", encoding="utf-8-sig") as f:
            self._data = json.load(f)
        return self._data

    def _format(self, name: dict, lang: str) -> dict:
        return {
            "number": name["number"],
            "arabic": name["arabic"],
            "transliteration": name["transliteration"],
            "name": self.translate(name["translations"], lang),
            "meaning": self.translate(name["meaning"], lang)
        }

    async def get_all(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        data = self._load()
        return {
            "total": data["total"],
            "names": [self._format(n, lang) for n in data["names"]]
        }

    async def get_by_number(
        self,
        number: int,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        data = self._load()
        if number < 1 or number > 99:
            raise HTTPException(404, "Number must be between 1 and 99")
        name = next((n for n in data["names"] if n["number"] == number), None)
        if not name:
            raise HTTPException(404, f"Name number {number} not found")
        return self._format(name, lang)

    async def get_random(
        self,
        request: Request,
        lang: str = Query("en", description="Language: en or ar")
    ):
        lang = self.get_lang(request, lang)
        data = self._load()
        name = random.choice(data["names"])
        return self._format(name, lang)
