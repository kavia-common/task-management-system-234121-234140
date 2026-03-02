from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Note: Do not hardcode secrets. Configure via container .env.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database (provided by the task_manager_database container)
    postgres_url: str = Field(..., alias="POSTGRES_URL", description="PostgreSQL connection URL.")

    # Auth
    jwt_secret_key: str = Field(
        ...,
        alias="JWT_SECRET_KEY",
        description="Secret key used to sign JWT access tokens.",
        min_length=16,
    )
    jwt_algorithm: str = Field(
        default="HS256",
        alias="JWT_ALGORITHM",
        description="JWT signing algorithm (default HS256).",
    )
    access_token_expires_minutes: int = Field(
        default=60 * 24 * 7,
        alias="ACCESS_TOKEN_EXPIRES_MINUTES",
        description="JWT access token lifetime in minutes.",
        ge=5,
    )

    # CORS
    cors_allow_origins: str = Field(
        default="*",
        alias="CORS_ALLOW_ORIGINS",
        description="Comma-separated list of allowed origins, or '*' for all.",
    )


settings = Settings()
