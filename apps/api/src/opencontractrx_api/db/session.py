from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencontractrx_api.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)