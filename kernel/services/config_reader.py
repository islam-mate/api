import yaml
import os


class ConfigReader:
    def __init__(self):
        self.config = {}
        self.config_path = "config.yaml"

    def load(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"config.yaml not found")
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        print("config.yaml loaded")

    def get(self, key: str, default=None):
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_modules(self) -> dict:
        return self.config.get("modules", {})

    def is_module_enabled(self, module_name: str) -> bool:
        return self.get_modules().get(module_name, False)
