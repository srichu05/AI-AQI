"""Database Migration & Schema Alignment Module for AI-AQI PostgreSQL & SQLite.

Ensures that new tables (users, user_profiles, health_profiles, user_prediction_history,
user_locations, user_preferences, audit_logs) are created alongside existing telemetry
and AI tables without dropping data or breaking backward compatibility.
"""

import logging
from sqlalchemy import text
from deployment.database import Base, engine, get_engine, init_db

logger = logging.getLogger(__name__)


def run_migrations(db_url: str = None) -> None:
    """Executes safe schema migration alignment on target database."""
    target_engine = get_engine(db_url) if db_url else engine
    logger.info("Verifying database schema alignment and applying migrations...")

    # Create all missing tables safely
    Base.metadata.create_all(bind=target_engine)

    # Perform table presence audit
    with target_engine.connect() as conn:
        if target_engine.name == "postgresql":
            res = conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            tables = [row[0] for row in res.fetchall()]
        else:
            res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in res.fetchall()]

    logger.info(f"Active Database Tables Audit ({len(tables)} tables verified): {', '.join(tables)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migrations()
