from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str
    jwt_secret: str = "dev-change-me"
    jwt_issuer: str = "opencontractrx"


settings = Settings()  # type: ignore[call-arg]