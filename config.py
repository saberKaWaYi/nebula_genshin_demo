import logging
import logging.config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CRON_LOG_DIR = BASE_DIR / 'crontab_task'
CRON_LOG_FILE = CRON_LOG_DIR / 'crontab.log'

CRON_LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'crontab_task': {
            'class': 'logging.FileHandler',
            'filename': str(CRON_LOG_FILE),
            'formatter': 'standard',
            'level': 'INFO',
            'encoding': 'utf-8',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'cron_task': {
            'handlers': ['crontab_task', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}


def setup_logging():
    """设置全局日志配置"""
    logging.config.dictConfig(LOGGING_CONFIG)