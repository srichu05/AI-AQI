"""CLI script to initialize the PostgreSQL 'ai_aqi' database and 'sensor_telemetry' table."""

import logging
import sys
from deployment.database import init_db, DATABASE_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"Initializing AI-AQI database using connection URL pattern: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    try:
        init_db()
        logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)
