import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_opencontractrx.sqlite")

from fastapi.testclient import TestClient

from opencontractrx_api.core.security import mint_dev_token
from opencontractrx_api.db.base import Base
from opencontractrx_api.db.session import engine
from opencontractrx_api.main import app


def _auth_headers() -> dict[str, str]:
    token = mint_dev_token(sub="pytest", role="admin")
    return {"Authorization": f"Bearer {token}"}


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_contracts_requires_auth() -> None:
    with TestClient(app) as client:
        response = client.get("/contracts")
    assert response.status_code == 401


def test_upload_and_list_contracts() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/contracts/upload",
            json={
                "title": "Master Service Agreement",
                "vendor": "VendorCo",
            },
            headers=_auth_headers(),
        )
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["title"] == "Master Service Agreement"
        assert created["vendor"] == "VendorCo"
        assert created["status"] == "uploaded"
        assert created["id"].startswith("c_")
        assert created["created_at"]

        list_response = client.get("/contracts", headers=_auth_headers())
        assert list_response.status_code == 200
        payload = list_response.json()
        assert len(payload) == 1
        assert payload[0]["id"] == created["id"]
