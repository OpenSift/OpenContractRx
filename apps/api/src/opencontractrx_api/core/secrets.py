import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from opencontractrx_api.core.config import settings


def _get_fernet() -> Fernet:
    key = settings.credentials_encryption_key
    if key:
        return Fernet(key.encode("utf-8"))

    derived_key = base64.urlsafe_b64encode(hashlib.sha256(settings.jwt_secret.encode("utf-8")).digest())
    return Fernet(derived_key)


def seal(secret: str) -> str:
    return _get_fernet().encrypt(secret.encode("utf-8")).decode("utf-8")


def unseal(cipher_text: str) -> str:
    try:
        return _get_fernet().decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt credential") from exc
