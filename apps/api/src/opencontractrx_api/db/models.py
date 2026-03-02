from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from opencontractrx_api.db.base import Base


def _new_contract_id() -> str:
    return f"c_{uuid4().hex[:8]}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_new_contract_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
