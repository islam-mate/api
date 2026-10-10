import os
import importlib
from kernel.service_container import ServiceContainer


class ModuleLoader:
    def __init__(self, service_container: ServiceContainer):
        self.service_container = service_container
        self.modules = []

    def discover(self):
        print("Discovering modules...")
        modules_path = "modules"

        if not os.path.exists(modules_path):
            print("No modules folder found.")
            return

        enabled = self.service_container.config.get_modules()

        for folder in os.listdir(modules_path):
            module_path = os.path.join(modules_path, folder)
            if not os.path.isdir(module_path):
                continue
            if not enabled.get(folder, False):
                print(f"Module '{folder}' is disabled - skipping")
                continue
            try:
                mod = importlib.import_module(f"modules.{folder}.module")
                cls = getattr(mod, "Module")
                instance = cls(self.service_container)
                self.modules.append(instance)
                print(f"Module loaded: {folder}")
            except Exception as e:
                print(f"Failed to load module '{folder}': {e}")

        print(f"Total modules loaded: {len(self.modules)}")
