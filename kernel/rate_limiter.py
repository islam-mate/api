from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
import threading

limiter = Limiter(key_func=get_remote_address)

_request_counts = defaultdict(list)
_lock = threading.Lock()

RATE_LIMIT = 60
WINDOW = 60


def is_rate_limited(ip: str) -> bool:
    now = time.time()
    with _lock:
        _request_counts[ip] = [t for t in _request_counts[ip] if now - t < WINDOW]
        if len(_request_counts[ip]) >= RATE_LIMIT:
            return True
        _request_counts[ip].append(now)
        return False


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {RATE_LIMIT} per {WINDOW} seconds",
            "retry_after": "60 seconds"
        }
    )
