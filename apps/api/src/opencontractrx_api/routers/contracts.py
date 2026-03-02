from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from opencontractrx_api.core.security import AuthContext, get_auth_context
from opencontractrx_api.db.deps import get_db_session
from opencontractrx_api.db.models import Contract

router = APIRouter(prefix="/contracts", tags=["contracts"])


class ContractOut(BaseModel):
    id: str
    title: str
    vendor: str
    status: str
    created_at: datetime


@router.get("", response_model=List[ContractOut])
def list_contracts(
    _: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db_session),
) -> List[ContractOut]:
    rows = db.execute(select(Contract).order_by(Contract.created_at.desc())).scalars().all()
    return [
        ContractOut(
            id=row.id,
            title=row.title,
            vendor=row.vendor,
            status=row.status,
            created_at=row.created_at,
        )
        for row in rows
    ]


class UploadPlaceholderIn(BaseModel):
    title: str
    vendor: str


@router.post("/upload", response_model=ContractOut)
def upload_placeholder(
    payload: UploadPlaceholderIn,
    _: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db_session),
) -> ContractOut:
    new_contract = Contract(
        title=payload.title,
        vendor=payload.vendor,
        status="uploaded",
    )
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)
    return ContractOut(
        id=new_contract.id,
        title=new_contract.title,
        vendor=new_contract.vendor,
        status=new_contract.status,
        created_at=new_contract.created_at,
    )
