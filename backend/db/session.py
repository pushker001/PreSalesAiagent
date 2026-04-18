import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured. Add your Supabase Postgres connection string "
        "to backend/.env before using the database layer."
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_database_connection() -> dict:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"connected": True, "database_url_configured": True}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database connectivity check failed: %s", exc)
        return {
            "connected": False,
            "database_url_configured": bool(DATABASE_URL),
            "error": str(exc),
        }
