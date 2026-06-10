from fastapi import APIRouter

from .funds import router as funds_router
from .categories import router as categories_router

router = APIRouter()
router.include_router(funds_router)
router.include_router(categories_router)
