from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:3000",
    ]
    jwt_secret: str
    jwt_expire_minutes: int = 60

    # AWS Price List Query API (solo lectura, sin costos).
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    # "simulation" usa las tarifas almacenadas; "live" consulta la API real.
    catalog_mode: str = "simulation"

    # Revisión de pedidos con IA: "heuristic" (solo reglas), "llm" (proveedor de
    # IA) o "hybrid" (reglas + resumen redactado por el LLM). El proveedor y el
    # modelo también se pueden fijar/consultar en app_settings (BD) y desde la UI.
    review_mode: str = "heuristic"
    review_provider: str = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-flash-lite-latest"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_api_key: str | None = None
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()

# Validación manual para no incluir el valor del secreto en el mensaje de error.
if not settings.jwt_secret.strip() or len(settings.jwt_secret) < 32:
    raise RuntimeError(
        "JWT_SECRET debe tener al menos 32 caracteres. Genera uno con: "
        'python -c "import secrets; print(secrets.token_urlsafe(48))"'
    )
