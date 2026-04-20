import logging
import logging.config
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "crawler" / "data"
LOG_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "formatter": "standard",
            "level": "INFO",
            "encoding": "utf-8",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "crawler": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "app": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


def setup_logging():
    """设置全局日志配置"""
    logging.config.dictConfig(LOGGING_CONFIG)


class CrawlerSettings:
    """爬虫配置"""
    website_cookies = {
        "wiki_biligame_com": {
            "cookie_name": {
                "SESSDATA": "80e2be21%2C1789203900%2C949ca%2A32CjD2Gvwg3haOu5McOA0u_hAKlykzCa6TzdsDlON4b_h26Jc82hpLsMRb8d9OHJ6phFASVmRBOXFxcFd1QUVZUTRuVXY1LU0tSjUyTnhfZEpSdWlFeVhlVUJNZkJOVVVYT2xiV3BZZFl6czFEM2dua3BELWhYWUt5SzBSNll2OGdZS0wwemRYV1lRIIEC"
            }
        }
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    }
    time_sleep = 3
    max_retries = 15


crawler_settings = CrawlerSettings()


class Settings(BaseSettings):
    """应用配置"""
    app_name: str = "Neo4j Operations API"
    app_version: str = "1.0.0"
    debug: bool = False

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")

    rabbitmq_host: str = Field(default="localhost", alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, alias="RABBITMQ_PORT")
    rabbitmq_username: str = Field(default="guest", alias="RABBITMQ_USERNAME")
    rabbitmq_password: str = Field(default="guest", alias="RABBITMQ_PASSWORD")
    rabbitmq_queue: str = Field(default="neo4j_operations", alias="RABBITMQ_QUEUE")

    api_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()