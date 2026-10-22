from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.models import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables. Call once on startup."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency - yields a session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_session():
    """Plain context-manager version for use inside LangGraph tools."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
