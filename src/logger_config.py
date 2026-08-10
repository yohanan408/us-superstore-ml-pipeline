import logging
import sys
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "pipeline_runtime.log"
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] \u2500\u2500\u25b8 %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _build_logger(name: str = "pipeline") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if not logger.handlers:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger = _build_logger()
