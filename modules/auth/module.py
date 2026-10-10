from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from kernel.services.auth import generate_key, list_keys, revoke_key, init_db
from base.base_module import BaseModule


class RegisterRequest(BaseModel):
    name: str
    email: str = ""


class Module(BaseModule):
    name = "auth"
    version = "1.0.0"
    dependencies = []

    def register_routes(self, router: APIRouter):
        init_db()
        router.add_api_route("/auth/register", self.register, methods=["POST"])
        router.add_api_route("/auth/keys", self.get_keys, methods=["GET"])
        router.add_api_route("/auth/keys/{key_id}/revoke", self.revoke, methods=["POST"])

    async def register(self, body: RegisterRequest):
        if not body.name:
            raise HTTPException(400, "Name is required")
        key = generate_key(body.name, body.email)
        return {
            "message": "API key generated successfully",
            "api_key": key,
            "warning": "Save this key — it will not be shown again"
        }

    async def get_keys(self):
        return {"keys": list_keys()}

    async def revoke(self, key_id: int):
        revoke_key(key_id)
        return {"message": f"Key {key_id} revoked"}
