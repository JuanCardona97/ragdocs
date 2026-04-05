"""
Configuration — App settings loaded from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with sensible defaults."""

    # Google Gemini
    GOOGLE_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    TEMPERATURE: float = 0.1

    # RAG parameters
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 4

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # CORS (comma-separated string, parsed into list)
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://ragdocs.onrender.com,https://ragdocs-frontend.onrender.com"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
