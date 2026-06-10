from ..core.config import settings
from .base import MutualFundProvider
from .mfapi import MFAPIProvider


def get_provider() -> MutualFundProvider:
    return MFAPIProvider(base_url=settings.mfapi_base_url)
