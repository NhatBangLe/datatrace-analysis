import logging.config
import os


def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colorful_with_time": {
                "()": "uvicorn.logging.ColourizedFormatter",
                # This string gives you the timestamp + FastAPI colors
                "format": "{asctime} | {levelprefix:<8} | {name} | {message}",
                "datefmt": "%Y-%m-%d %H:%M:%S",  # Clean timestamp format
                "style": "{",
                "use_colors": True,
            },
        },
        "handlers": {
            "default": {
                "formatter": "colorful_with_time",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "handlers": ["default"],
            "level": log_level,
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)
