import os
from logging.config import dictConfig

lastinfo_path = "logs/lastinfo.log"
lastdebug_path = "logs/lastdebug.log"
info_path = "logs/info.log"
warn_path = "logs/warning.log"

if not os.path.exists("logs"):
    os.makedirs("logs")
try:
    os.remove(lastinfo_path)
except OSError:
    pass
try:
    os.remove(lastdebug_path)
except OSError:
    pass


def is_docker():
    path = "/proc/self/cgroup"
    status = os.path.exists("/.dockerenv") or os.path.isfile(path) and any("docker" in line for line in open(path))
    return status


if is_docker() is False or os.environ.get("VERBOSE_LOGGING", "FALSE") == "TRUE":
    logging_mode = "Verbose "
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": True,
        "loggers": {
            "": {
                "level": "DEBUG",
                "handlers": ["console", "all_warning", "all_info", "last_info", "last_debug"],
            },
        },
        "handlers": {
            "console": {
                "level": "WARNING",
                "formatter": "fmt",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "all_warning": {
                "level": "WARNING",
                "formatter": "fmt",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": warn_path,
                "maxBytes": 1048576,
                "backupCount": 10,
            },
            "all_info": {
                "level": "INFO",
                "formatter": "fmt",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": info_path,
                "maxBytes": 1048576,
                "backupCount": 10,
            },
            "last_info": {
                "level": "INFO",
                "formatter": "fmt",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": lastinfo_path,
                "maxBytes": 1048576,
            },
            "last_debug": {
                "level": "DEBUG",
                "formatter": "fmt",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": lastdebug_path,
                "maxBytes": 1048576,
            },
        },
        "formatters": {
            "fmt": {"format": "%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s|%(lineno)s:: %(message)s"},
        },
    }
else:
    logging_mode = ""
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": True,
        "loggers": {
            "": {
                "level": "DEBUG",
                "handlers": ["console", "all_warning"],
            },
        },
        "handlers": {
            "console": {
                "level": "WARNING",
                "formatter": "fmt",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "all_warning": {
                "level": "WARNING",
                "formatter": "fmt",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": warn_path,
                "maxBytes": 1048576,
                "backupCount": 10,
            },
        },
        "formatters": {
            "fmt": {"format": "%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s|%(lineno)s:: %(message)s"},
        },
    }
dictConfig(LOGGING_CONFIG)
import logging

logger = logging.getLogger(__name__)
logger.warning(f"***{logging_mode}Logging Started***")
