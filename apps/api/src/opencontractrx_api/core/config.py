from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str
    jwt_secret: str = "dev-change-me"
    jwt_issuer: str = "opencontractrx"
    credentials_encryption_key: str | None = None

    chatgpt_validate_url: str = "https://api.openai.com/v1/models"
    codex_validate_url: str = "https://api.openai.com/v1/models"
    claude_validate_url: str = "https://api.anthropic.com/v1/models"
    claude_code_validate_url: str = "https://api.anthropic.com/v1/models"

    chatgpt_oauth_client_id: str | None = None
    chatgpt_oauth_client_secret: str | None = None
    chatgpt_oauth_auth_url: str | None = None
    chatgpt_oauth_token_url: str | None = None
    chatgpt_oauth_redirect_uri: str | None = None
    chatgpt_oauth_scopes: str = "openid profile"

    codex_oauth_client_id: str | None = None
    codex_oauth_client_secret: str | None = None
    codex_oauth_auth_url: str | None = None
    codex_oauth_token_url: str | None = None
    codex_oauth_redirect_uri: str | None = None
    codex_oauth_scopes: str = "openid profile"

    claude_oauth_client_id: str | None = None
    claude_oauth_client_secret: str | None = None
    claude_oauth_auth_url: str | None = None
    claude_oauth_token_url: str | None = None
    claude_oauth_redirect_uri: str | None = None
    claude_oauth_scopes: str = "openid profile"

    claude_code_oauth_client_id: str | None = None
    claude_code_oauth_client_secret: str | None = None
    claude_code_oauth_auth_url: str | None = None
    claude_code_oauth_token_url: str | None = None
    claude_code_oauth_redirect_uri: str | None = None
    claude_code_oauth_scopes: str = "openid profile"


settings = Settings()  # type: ignore[call-arg]
