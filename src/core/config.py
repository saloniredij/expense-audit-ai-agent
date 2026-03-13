from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    
    API_V1_STR: str = "/v1"
    # API_KEY = "KEY"
    PROJECT_NAME: str = "AI Expense Auditor"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "expense_user"
    POSTGRES_PASSWORD: str = "expense_password"
    POSTGRES_DB: str = "expense_audit"
    POSTGRES_PORT: int = 5432
    
    # OPENAI_API_KEY: str = API_KEY
    OPENAI_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    @computed_field # type: ignore
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
