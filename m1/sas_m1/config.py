from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SAS_M1_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./sas_m1.db"
    genesis_audit_hash: str = "0" * 64


settings = Settings()
