from fastapi import FastAPI
from opencontractrx_api.core.config import settings
from opencontractrx_api.core.logging import configure_logging
from opencontractrx_api.db.base import Base
from opencontractrx_api.db.session import engine
import opencontractrx_api.db.models  # noqa: F401
from opencontractrx_api.routers.health import router as health_router
from opencontractrx_api.routers.contracts import router as contracts_router
from opencontractrx_api.routers.auth import router as auth_router

configure_logging()

app = FastAPI(
    title="OpenContractRx API",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(contracts_router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


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
