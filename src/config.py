from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging.config


class Settings(BaseSettings):
    # FastAPI Application Settings
    APP_NAME: str = "DataTrace Analysis API"
    APP_VERSION: str = "0.1.0"

    # SeaweedFS S3 Gateway Settings
    SEAWEEDFS_ENDPOINT_URL: str = "http://localhost:8333"
    S3_ACCESS_KEY_ID: str = Field(default="any", description="Access key ID")
    S3_SECRET_ACCESS_KEY: str = Field(default="any", description="Secret access key")
    S3_BUCKET_NAME: str = Field(default="datatrace-raw", description="Bucket name")

    # DuckDB Analytics Settings
    DUCKDB_DATABASE: str = Field(
        default=":memory",
        description="Path to DuckDB database or ':memory:' for in-memory",
    )

    # Security Settings
    # Change this in production!
    HMAC_SECRET_KEY: str = Field(
        default="your-super-secret-hmac-key", description="HMAC secret key"
    )

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )


settings = Settings()


def setup_logging():
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colorful_with_time": {
                "()": "uvicorn.logging.ColourizedFormatter",
                # This string gives you the timestamp + FastAPI colors
                "format": "{asctime} | {levelprefix:<8} | {name} | {message}",
                "datefmt": "%Y-%m-%d %H:%M:%S",  # Clean timestamp format
                "style": "{",
                "use_colors": True,
            },
        },
        "handlers": {
            "default": {
                "formatter": "colorful_with_time",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "handlers": ["default"],
            "level": "INFO",
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)
