import os
from dotenv import load_dotenv

load_dotenv()


class ModeManager:
    DEVELOPMENT = "development"
    PRODUCTION = "production"

    def __init__(self):
        self.mode = self.DEVELOPMENT

    def load(self):
        self.mode = os.getenv("APP_MODE", self.DEVELOPMENT).lower()
        print(f"Running in {self.mode.upper()} mode")

    @property
    def is_development(self) -> bool:
        return self.mode == self.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.mode == self.PRODUCTION
