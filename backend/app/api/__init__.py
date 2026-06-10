from fastapi import APIRouter

from .funds import router as funds_router

router = APIRouter()
router.include_router(funds_router)
