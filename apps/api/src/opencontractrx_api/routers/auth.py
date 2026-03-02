from fastapi import APIRouter
from pydantic import BaseModel

from opencontractrx_api.core.security import mint_dev_token

router = APIRouter(prefix="/auth", tags=["auth"])


class DevTokenRequest(BaseModel):
    sub: str = "matt"
    role: str = "admin"
    ttl_seconds: int = 3600


class DevTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/dev-token", response_model=DevTokenResponse)
def dev_token(payload: DevTokenRequest) -> DevTokenResponse:
    token = mint_dev_token(payload.sub, payload.role, ttl_seconds=payload.ttl_seconds)
    return DevTokenResponse(access_token=token)