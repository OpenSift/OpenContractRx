from dataclasses import dataclass
from enum import StrEnum

from opencontractrx_api.core.config import settings


class Provider(StrEnum):
    CHATGPT = "chatgpt"
    CODEX = "codex"
    CLAUDE = "claude"
    CLAUDE_CODE = "claude_code"


@dataclass(frozen=True)
class ProviderConfig:
    provider: Provider
    display_name: str
    validate_url: str
    oauth_client_id: str | None
    oauth_client_secret: str | None
    oauth_auth_url: str | None
    oauth_token_url: str | None
    oauth_redirect_uri: str | None
    oauth_scopes: str


def get_provider_config(provider: Provider) -> ProviderConfig:
    if provider == Provider.CHATGPT:
        return ProviderConfig(
            provider=provider,
            display_name="ChatGPT",
            validate_url=settings.chatgpt_validate_url,
            oauth_client_id=settings.chatgpt_oauth_client_id,
            oauth_client_secret=settings.chatgpt_oauth_client_secret,
            oauth_auth_url=settings.chatgpt_oauth_auth_url,
            oauth_token_url=settings.chatgpt_oauth_token_url,
            oauth_redirect_uri=settings.chatgpt_oauth_redirect_uri,
            oauth_scopes=settings.chatgpt_oauth_scopes,
        )

    if provider == Provider.CODEX:
        return ProviderConfig(
            provider=provider,
            display_name="Codex",
            validate_url=settings.codex_validate_url,
            oauth_client_id=settings.codex_oauth_client_id,
            oauth_client_secret=settings.codex_oauth_client_secret,
            oauth_auth_url=settings.codex_oauth_auth_url,
            oauth_token_url=settings.codex_oauth_token_url,
            oauth_redirect_uri=settings.codex_oauth_redirect_uri,
            oauth_scopes=settings.codex_oauth_scopes,
        )

    if provider == Provider.CLAUDE:
        return ProviderConfig(
            provider=provider,
            display_name="Claude",
            validate_url=settings.claude_validate_url,
            oauth_client_id=settings.claude_oauth_client_id,
            oauth_client_secret=settings.claude_oauth_client_secret,
            oauth_auth_url=settings.claude_oauth_auth_url,
            oauth_token_url=settings.claude_oauth_token_url,
            oauth_redirect_uri=settings.claude_oauth_redirect_uri,
            oauth_scopes=settings.claude_oauth_scopes,
        )

    return ProviderConfig(
        provider=provider,
        display_name="Claude Code",
        validate_url=settings.claude_code_validate_url,
        oauth_client_id=settings.claude_code_oauth_client_id,
        oauth_client_secret=settings.claude_code_oauth_client_secret,
        oauth_auth_url=settings.claude_code_oauth_auth_url,
        oauth_token_url=settings.claude_code_oauth_token_url,
        oauth_redirect_uri=settings.claude_code_oauth_redirect_uri,
        oauth_scopes=settings.claude_code_oauth_scopes,
    )
