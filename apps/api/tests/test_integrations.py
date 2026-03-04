import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_opencontractrx.sqlite")

from fastapi.testclient import TestClient

from opencontractrx_api.core.config import settings
from opencontractrx_api.core.security import mint_dev_token
from opencontractrx_api.db.base import Base
from opencontractrx_api.db.session import engine
from opencontractrx_api.main import app
import opencontractrx_api.routers.integrations as integrations


def _auth_headers() -> dict[str, str]:
    token = mint_dev_token(sub="pytest", role="admin")
    return {"Authorization": f"Bearer {token}"}


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_list_integrations_defaults() -> None:
    with TestClient(app) as client:
        response = client.get("/integrations", headers=_auth_headers())
    assert response.status_code == 200
    payload = response.json()
    assert {row["provider"] for row in payload} == {"chatgpt", "codex", "claude", "claude_code"}
    assert all(row["connected"] is False for row in payload)


def test_connect_api_key_and_test_connection(monkeypatch) -> None:
    async def fake_validate_secret(*args, **kwargs):
        return True, "validated"

    monkeypatch.setattr(integrations, "_validate_secret", fake_validate_secret)

    with TestClient(app) as client:
        create_response = client.post(
            "/integrations/chatgpt/api-key",
            json={"api_key": "sk-test-1234567890"},
            headers=_auth_headers(),
        )
        assert create_response.status_code == 200
        assert create_response.json()["connected"] is True
        assert create_response.json()["auth_method"] == "api_key"

        test_response = client.post("/integrations/chatgpt/test", headers=_auth_headers())
        assert test_response.status_code == 200
        assert test_response.json()["detail"] == "Validated"


def test_oauth_start_and_callback(monkeypatch) -> None:
    settings.chatgpt_oauth_client_id = "client-id"
    settings.chatgpt_oauth_client_secret = "client-secret"
    settings.chatgpt_oauth_auth_url = "https://example.com/oauth/authorize"
    settings.chatgpt_oauth_token_url = "https://example.com/oauth/token"
    settings.chatgpt_oauth_redirect_uri = "http://localhost:8000/integrations/chatgpt/oauth/callback"
    settings.chatgpt_oauth_scopes = "openid profile"

    async def fake_validate_secret(*args, **kwargs):
        return True, "validated"

    async def fake_exchange_code(*args, **kwargs):
        return {"access_token": "oauth-token-123", "refresh_token": "refresh-123", "expires_in": 3600}

    monkeypatch.setattr(integrations, "_validate_secret", fake_validate_secret)
    monkeypatch.setattr(integrations, "_exchange_oauth_code", fake_exchange_code)

    with TestClient(app) as client:
        start_response = client.get("/integrations/chatgpt/oauth/start", headers=_auth_headers())
        assert start_response.status_code == 200
        auth_url = start_response.json()["auth_url"]
        assert "response_type=code" in auth_url
        state = auth_url.split("state=")[1].split("&")[0]

        callback_response = client.get(
            f"/integrations/chatgpt/oauth/callback?code=test-code&state={state}"
        )
        assert callback_response.status_code == 200
        payload = callback_response.json()
        assert payload["connected"] is True
        assert payload["auth_method"] == "oauth"
