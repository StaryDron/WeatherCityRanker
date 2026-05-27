import logging
import os
from datetime import datetime

def get_logger(name):
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if os.environ.get("APP_ENV") == "dev" else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler(f"logs/app.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
