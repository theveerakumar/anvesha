from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://anvesha:anvesha@localhost/anvesha"
    redis_url: str = "redis://localhost:6379"
    mfapi_base_url: str = "https://api.mfapi.in"
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
