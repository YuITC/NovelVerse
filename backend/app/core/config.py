from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_key: str
    supabase_jwt_secret: str

    # App
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    debug: bool = False

    # AI (optional -- no key means Gemini translation is unavailable)
    gemini_api_key: str = ""

    # Qdrant (optional -- embedding pipeline disabled if not set)
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Upstash Redis (optional -- rate limiting disabled if not set)
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
