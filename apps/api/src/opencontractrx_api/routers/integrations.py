from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from opencontractrx_api.core.config import settings
from opencontractrx_api.core.integrations import Provider, get_provider_config
from opencontractrx_api.core.security import AuthContext, get_auth_context
from opencontractrx_api.core.secrets import seal, unseal
from opencontractrx_api.db.deps import get_db_session
from opencontractrx_api.db.models import IntegrationCredential

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(payload: str) -> bytes:
    pad = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode((payload + pad).encode("utf-8"))


def _sign_state(payload_b64: str) -> str:
    digest = hmac.new(settings.jwt_secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    return _b64url(digest)


def _make_oauth_state(sub: str, provider: Provider, ttl_seconds: int = 600) -> str:
    payload = {
        "sub": sub,
        "provider": provider.value,
        "exp": int((_utc_now() + timedelta(seconds=ttl_seconds)).timestamp()),
        "nonce": secrets.token_urlsafe(12),
    }
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = _sign_state(payload_b64)
    return f"{payload_b64}.{sig}"


def _parse_oauth_state(state: str) -> tuple[str, Provider]:
    try:
        payload_b64, provided_sig = state.split(".", maxsplit=1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state") from exc

    expected_sig = _sign_state(payload_b64)
    if not hmac.compare_digest(provided_sig, expected_sig):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state signature")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(_utc_now().timestamp()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expired OAuth state")

    return str(payload["sub"]), Provider(payload["provider"])


def _ensure_oauth_enabled(provider: Provider) -> None:
    cfg = get_provider_config(provider)
    missing = [
        name
        for name, value in (
            ("oauth_client_id", cfg.oauth_client_id),
            ("oauth_client_secret", cfg.oauth_client_secret),
            ("oauth_auth_url", cfg.oauth_auth_url),
            ("oauth_token_url", cfg.oauth_token_url),
            ("oauth_redirect_uri", cfg.oauth_redirect_uri),
        )
        if not value
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth not configured for {provider.value}. Missing: {', '.join(missing)}",
        )


async def _validate_secret(provider: Provider, secret_value: str, auth_method: str) -> tuple[bool, str]:
    cfg = get_provider_config(provider)
    headers: dict[str, str] = {}
    if provider in {Provider.CHATGPT, Provider.CODEX} or auth_method == "oauth":
        headers["Authorization"] = f"Bearer {secret_value}"
    elif provider in {Provider.CLAUDE, Provider.CLAUDE_CODE}:
        headers["x-api-key"] = secret_value
        headers["anthropic-version"] = "2023-06-01"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(cfg.validate_url, headers=headers)
        if response.status_code < 400:
            return True, "validated"
        return False, f"Validation failed ({response.status_code})"
    except httpx.HTTPError as exc:
        return False, f"Validation request failed: {exc.__class__.__name__}"


async def _exchange_oauth_code(provider: Provider, code: str) -> dict:
    cfg = get_provider_config(provider)
    _ensure_oauth_enabled(provider)

    form_data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": cfg.oauth_client_id,
        "client_secret": cfg.oauth_client_secret,
        "redirect_uri": cfg.oauth_redirect_uri,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            str(cfg.oauth_token_url),
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth token exchange failed ({response.status_code})",
        )
    return response.json()


def _upsert_credential(
    db: Session,
    sub: str,
    provider: Provider,
    auth_method: str,
    secret_value: str,
    refresh_token: str | None = None,
    token_expires_at: datetime | None = None,
    metadata_json: dict | None = None,
) -> IntegrationCredential:
    row = db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.sub == sub,
            IntegrationCredential.provider == provider.value,
        )
    ).scalar_one_or_none()
    if row is None:
        row = IntegrationCredential(
            sub=sub,
            provider=provider.value,
            auth_method=auth_method,
            encrypted_secret=seal(secret_value),
            encrypted_refresh_token=seal(refresh_token) if refresh_token else None,
            token_expires_at=token_expires_at,
            metadata_json=metadata_json or {},
            last_validated_at=_utc_now(),
        )
        db.add(row)
    else:
        row.auth_method = auth_method
        row.encrypted_secret = seal(secret_value)
        row.encrypted_refresh_token = seal(refresh_token) if refresh_token else None
        row.token_expires_at = token_expires_at
        row.metadata_json = metadata_json or {}
        row.last_validated_at = _utc_now()

    db.commit()
    db.refresh(row)
    return row


class IntegrationStatusOut(BaseModel):
    provider: Provider
    connected: bool
    auth_method: str | None = None
    last_validated_at: datetime | None = None
    token_expires_at: datetime | None = None


class ApiKeyConnectIn(BaseModel):
    api_key: str = Field(min_length=8, max_length=4000)


class IntegrationConnectOut(BaseModel):
    provider: Provider
    auth_method: str
    connected: bool
    detail: str


class OAuthStartOut(BaseModel):
    provider: Provider
    auth_url: str


@router.get("", response_model=list[IntegrationStatusOut])
def list_integrations(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db_session),
) -> list[IntegrationStatusOut]:
    rows = db.execute(
        select(IntegrationCredential).where(IntegrationCredential.sub == auth.sub)
    ).scalars().all()
    existing = {row.provider: row for row in rows}
    out: list[IntegrationStatusOut] = []
    for provider in Provider:
        row = existing.get(provider.value)
        out.append(
            IntegrationStatusOut(
                provider=provider,
                connected=row is not None,
                auth_method=row.auth_method if row else None,
                last_validated_at=row.last_validated_at if row else None,
                token_expires_at=row.token_expires_at if row else None,
            )
        )
    return out


@router.post("/{provider}/api-key", response_model=IntegrationConnectOut)
async def connect_api_key(
    provider: Provider,
    payload: ApiKeyConnectIn,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db_session),
) -> IntegrationConnectOut:
    ok, detail = await _validate_secret(provider, payload.api_key, auth_method="api_key")
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    _upsert_credential(
        db=db,
        sub=auth.sub,
        provider=provider,
        auth_method="api_key",
        secret_value=payload.api_key,
        metadata_json={"source": "api_key"},
    )
    return IntegrationConnectOut(provider=provider, auth_method="api_key", connected=True, detail="Connected")


@router.get("/{provider}/oauth/start", response_model=OAuthStartOut)
def oauth_start(
    provider: Provider,
    auth: AuthContext = Depends(get_auth_context),
) -> OAuthStartOut:
    cfg = get_provider_config(provider)
    _ensure_oauth_enabled(provider)
    state = _make_oauth_state(sub=auth.sub, provider=provider)
    query = urlencode(
        {
            "client_id": cfg.oauth_client_id,
            "redirect_uri": cfg.oauth_redirect_uri,
            "response_type": "code",
            "scope": cfg.oauth_scopes,
            "state": state,
        }
    )
    return OAuthStartOut(provider=provider, auth_url=f"{cfg.oauth_auth_url}?{query}")


@router.get("/{provider}/oauth/callback", response_model=IntegrationConnectOut)
async def oauth_callback(
    provider: Provider,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> IntegrationConnectOut:
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OAuth provider error: {error}")
    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing OAuth code or state")

    sub_from_state, provider_from_state = _parse_oauth_state(state)
    if provider_from_state != provider:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth provider mismatch")

    token_payload = await _exchange_oauth_code(provider, code)
    access_token = str(token_payload.get("access_token", ""))
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing access_token in OAuth response")

    expires_in = token_payload.get("expires_in")
    expires_at: datetime | None = None
    if isinstance(expires_in, int) and expires_in > 0:
        expires_at = _utc_now() + timedelta(seconds=expires_in)

    ok, detail = await _validate_secret(provider, access_token, auth_method="oauth")
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    _upsert_credential(
        db=db,
        sub=sub_from_state,
        provider=provider,
        auth_method="oauth",
        secret_value=access_token,
        refresh_token=token_payload.get("refresh_token"),
        token_expires_at=expires_at,
        metadata_json={"source": "oauth", "token_type": token_payload.get("token_type")},
    )
    return IntegrationConnectOut(provider=provider, auth_method="oauth", connected=True, detail="Connected")


@router.post("/{provider}/test", response_model=IntegrationConnectOut)
async def test_integration(
    provider: Provider,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db_session),
) -> IntegrationConnectOut:
    row = db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.sub == auth.sub,
            IntegrationCredential.provider == provider.value,
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No credential configured for provider")

    try:
        secret_value = unseal(row.encrypted_secret)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    ok, detail = await _validate_secret(provider, secret_value, row.auth_method)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    row.last_validated_at = _utc_now()
    db.commit()
    db.refresh(row)
    return IntegrationConnectOut(provider=provider, auth_method=row.auth_method, connected=True, detail="Validated")
