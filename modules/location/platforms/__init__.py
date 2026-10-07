"""
Location platform guides package.

main.py imports:  from modules.location.platforms import router
No changes needed in main.py.
"""

from fastapi import APIRouter

from .android import router as android_router
from .ios     import router as ios_router
from .windows import router as windows_router
from .linux   import router as linux_router
from .web     import router as web_router

router = APIRouter(prefix="/api/v1/location", tags=["Location — Platforms"])

router.include_router(android_router)
router.include_router(ios_router)
router.include_router(windows_router)
router.include_router(linux_router)
router.include_router(web_router)
