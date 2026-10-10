class TranslatorService:
    SUPPORTED_LANGUAGES = ["en", "ar"]
    DEFAULT_LANGUAGE = "en"

    def translate(self, data: dict, lang: str = "en") -> dict:
        if lang not in self.SUPPORTED_LANGUAGES:
            lang = self.DEFAULT_LANGUAGE
        if isinstance(data, dict):
            return data.get(lang, data.get(self.DEFAULT_LANGUAGE, data))
        return data

    def get_language(self, lang: str = None) -> str:
        if lang and lang in self.SUPPORTED_LANGUAGES:
            return lang
        return self.DEFAULT_LANGUAGE
