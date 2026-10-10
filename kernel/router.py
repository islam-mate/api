from fastapi import FastAPI
from fastapi.routing import APIRouter


class Router:
    def register(self, app: FastAPI, modules: list):
        print("Registering module routes...")
        for module in modules:
            for lang in ["en", "ar"]:
                router = APIRouter(prefix=f"/api/v1/{lang}")
                module.register_routes(router)
                app.include_router(router)

            router_default = APIRouter(prefix="/api/v1")
            module.register_routes(router_default)
            app.include_router(router_default)

            print(f"Routes registered: {module.name}")
        print("All routes registered.")
