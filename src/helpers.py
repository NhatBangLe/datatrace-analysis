import logging.config
import os
import mimetypes

# Register custom MIME types for security forensics formats
mimetypes.add_type("application/vnd.tcpdump.pcap", ".pcap")
mimetypes.add_type("application/x-pcapng", ".pcapng")
mimetypes.add_type("application/x-microsoft-procmon-pml", ".pml")
mimetypes.add_type("application/x-ms-evtx", ".evtx")


def guess_mime_type(filename: str, client_mime: str | None = None) -> str:
    """
    Attempts to guess the MIME type of a file based on its filename extension using
    the registered types, falling back to the client-provided MIME type if specified,
    and finally defaulting to application/octet-stream.
    """
    if filename:
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type:
            return guessed_type

    if client_mime and client_mime != "application/octet-stream":
        return client_mime

    return "application/octet-stream"



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
