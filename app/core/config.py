from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Procesally API"
    VERSION: str = "0.1.0"

    LOG_LEVEL: str = "INFO"

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DB_HOST: str
    DB_PORT: str

    OPENAI_API_KEY: str = "sk-placeholder"
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-small"
    PARSING_ONLY_MODE: bool = True
    USE_ZERO_EMBEDDINGS: bool = True
    ZERO_EMBEDDING_DIM: int = 1536
    DISABLE_LLM_ROUTER: bool = True

    CORS_ALLOW_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    CORS_EXPOSE_HEADERS: List[str] = ["*"]
    CORS_MAX_AGE: int = 600

    ALLOWED_DOMAINS: List[str] = ["www.dof.gob.mx", "www.ordenjuridico.gob.mx"]
    ORDEN_JURIDICO_URL: str = "https://www.ordenjuridico.gob.mx/"
    HTTP_VERIFY_SSL: bool = True
    HTTP_ALLOW_INSECURE_SSL_FALLBACK: bool = True
    MAX_EMBEDDING_CHARS: int = 24000

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"

    @property
    def db_url_async(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
