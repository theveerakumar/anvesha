from fastapi import APIRouter

from .funds import router as funds_router
from .categories import router as categories_router
from .sip import router as sip_router
from .swp import router as swp_router
from .screener import router as screener_router
from .dashboard import router as dashboard_router
from .managers import router as managers_router
from .recommendations import router as recommendations_router

router = APIRouter()
router.include_router(dashboard_router)
router.include_router(funds_router)
router.include_router(categories_router)
router.include_router(sip_router)
router.include_router(screener_router)
router.include_router(managers_router)
router.include_router(swp_router)
router.include_router(recommendations_router)
