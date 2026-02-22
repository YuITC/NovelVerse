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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
