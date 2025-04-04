from typing import Any, Dict, Optional
from pydantic import PostgresDsn, field_validator
from pydantic_settings  import BaseSettings

from opendss_fastapi_celery.app.config.settings import db_settings


class Settings(BaseSettings):

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    OPENDSS_INSTALL_DIR: str = 'C:\\Program Files\\OpenDSS\\'

    @field_validator("SQLALCHEMY_DATABASE_URI", mode='before')
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=values.data.get("POSTGRES_USER"),
            password=values.data.get("POSTGRES_PASSWORD"),
            host=values.data.get("POSTGRES_SERVER"),
            path=f"{values.data.get('POSTGRES_DB') or ''}",
        )

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Load settings from the settings_dict
settings = Settings(**db_settings)

