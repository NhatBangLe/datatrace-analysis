from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )


settings = Settings()
