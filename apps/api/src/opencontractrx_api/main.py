from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from opencontractrx_api.core.config import settings
from opencontractrx_api.core.logging import configure_logging
from opencontractrx_api.db.base import Base
from opencontractrx_api.db.session import engine
import opencontractrx_api.db.models  # noqa: F401
from opencontractrx_api.routers.health import router as health_router
from opencontractrx_api.routers.contracts import router as contracts_router
from opencontractrx_api.routers.auth import router as auth_router
from opencontractrx_api.routers.integrations import router as integrations_router

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="OpenContractRx API", version="0.1.0", lifespan=lifespan)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(contracts_router)
app.include_router(integrations_router)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "opencontractrx_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
