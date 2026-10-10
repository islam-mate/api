from fastapi import FastAPI
from kernel.service_container import ServiceContainer
from kernel.module_loader import ModuleLoader
from kernel.router import Router
from kernel.mode_manager import ModeManager
from kernel.hot_reloader import HotReloader
from kernel.dependency_checker import DependencyChecker


class Kernel:
    def __init__(self):
        self.mode_manager = ModeManager()
        self.service_container = ServiceContainer()
        self.module_loader = ModuleLoader(self.service_container)
        self.dependency_checker = DependencyChecker()
        self.hot_reloader = HotReloader()
        self.router = Router()

    def discover(self):
        print("Starting Islamic API...")
        self.mode_manager.load()
        self.service_container.config.load()
        self.service_container.logger.setup()
        self.module_loader.discover()
        self.dependency_checker.check(self.module_loader.modules)
        self.hot_reloader.start()
        print(f"Mode: {self.mode_manager.mode}")
        print(f"Modules loaded: {len(self.module_loader.modules)}")

    async def init_services(self):
        await self.service_container.db.connect()
        await self.service_container.cache.connect()
        self.service_container.logger.info("All services initialized")
        print("Islamic API is ready.")

    async def shutdown(self):
        await self.service_container.dispose()
        self.hot_reloader.stop()
        print("Islamic API stopped.")

    def register_routes(self, app: FastAPI):
        self.router.register(app, self.module_loader.modules)
