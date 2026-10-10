from fastapi import Request
from fastapi.responses import JSONResponse
from kernel.services.auth import validate_key
from kernel.services.config_reader import ConfigReader

EXEMPT_PATHS = [
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/api/v1/auth/register",
]


async def auth_middleware(request: Request, call_next):
    config_reader = ConfigReader()
    config_reader.load()

    mode = config_reader.get("app.mode", "development")
    auth_enabled = config_reader.get("security.auth_enabled", False)

    print(f"DEBUG middleware: mode={mode}, auth_enabled={auth_enabled}, path={request.url.path}")

    if mode == "development" or not auth_enabled:
        return await call_next(request)

    path = request.url.path
    if any(path.startswith(p) for p in EXEMPT_PATHS):
        return await call_next(request)

    api_key = (
        request.headers.get("X-API-Key") or
        request.headers.get("Authorization", "").replace("Bearer ", "") or
        request.query_params.get("api_key")
    )

    print(f"DEBUG middleware: api_key={api_key}")

    if not api_key:
        return JSONResponse(
            status_code=401,
            content={
                "error": "API key required",
                "message": "Pass your key via X-API-Key header or ?api_key= param"
            }
        )

    if not validate_key(api_key):
        return JSONResponse(
            status_code=403,
            content={
                "error": "Invalid API key",
                "message": "Key not found or inactive"
            }
        )

    return await call_next(request)
