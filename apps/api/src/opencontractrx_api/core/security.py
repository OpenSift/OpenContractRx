from dataclasses import dataclass

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import hmac
import hashlib
import base64
import json
import time

from opencontractrx_api.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    sub: str
    role: str


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + padding).encode("utf-8"))


def _sign(message: bytes) -> str:
    sig = hmac.new(settings.jwt_secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url(sig)


def mint_dev_token(sub: str, role: str, ttl_seconds: int = 3600) -> str:
    """
    Dev-only token (not a full JWT implementation).
    Intended for local testing until proper OIDC/JWT verification is added.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": sub,
        "role": role,
        "iss": settings.jwt_issuer,
        "exp": int(time.time()) + ttl_seconds,
    }
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig_b64 = _sign(signing_input)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def get_auth_context(
    creds: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> AuthContext:
    """
    Bearer auth dependency with OpenAPI/Swagger integration.
    """
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = creds.credentials.strip()

    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    expected_sig = _sign(signing_input)
    if not hmac.compare_digest(sig_b64, expected_sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad signature")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))

    if payload.get("iss") != settings.jwt_issuer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad issuer")

    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    return AuthContext(sub=str(payload["sub"]), role=str(payload["role"]))