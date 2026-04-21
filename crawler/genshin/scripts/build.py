from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from neo4j import GraphDatabase

from config import settings, get_business_database


def build() -> None:
    database_name = get_business_database("genshin")
    logger.info("Ensuring database exists: %s", database_name)
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )
    try:
        with driver.session(database="system") as session:
            session.run(f"CREATE DATABASE {database_name} IF NOT EXISTS").consume()
        logger.info("Database ready: %s", database_name)
    finally:
        driver.close()


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:
        logger.exception("Failed to build database: %s", exc)
        raise
