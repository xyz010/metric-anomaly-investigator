from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str
    DB_URL: str = "data/analytics.db"
    DEFAULT_MODEL_CONFIDENCE: float | None = 0.5
    MODEL_NAME: str = "claude-sonnet-4-5"
    MAX_INVESTIGATION_STEPS: int = 10


settings = Settings()
