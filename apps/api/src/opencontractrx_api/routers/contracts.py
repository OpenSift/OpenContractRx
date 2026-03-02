from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from uuid import uuid4

from opencontractrx_api.core.security import AuthContext, get_auth_context

router = APIRouter(prefix="/contracts", tags=["contracts"])


class ContractOut(BaseModel):
    id: str
    title: str
    vendor: str
    status: str


# Temporary in-memory list to prove the UI + API wiring.
# Replace with Postgres models + migrations next.
_FAKE_CONTRACTS = [
    {"id": "c_001", "title": "Imaging Equipment Master Agreement", "vendor": "VendorCo", "status": "active"},
    {"id": "c_002", "title": "SaaS Analytics Addendum", "vendor": "CloudMetrics", "status": "active"},
]


@router.get("", response_model=List[ContractOut])
def list_contracts(_: AuthContext = Depends(get_auth_context)) -> List[ContractOut]:
    return [ContractOut(**c) for c in _FAKE_CONTRACTS]


class UploadPlaceholderIn(BaseModel):
    title: str
    vendor: str


@router.post("/upload", response_model=ContractOut)
def upload_placeholder(payload: UploadPlaceholderIn, _: AuthContext = Depends(get_auth_context)) -> ContractOut:
    new = {"id": f"c_{uuid4().hex[:8]}", "title": payload.title, "vendor": payload.vendor, "status": "uploaded"}
    _FAKE_CONTRACTS.append(new)
    return ContractOut(**new)