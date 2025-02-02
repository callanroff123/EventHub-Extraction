import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from src.config import LOG_PATH, LOGGING_PARAMS


def setup_logging(logger_name, logging_params = LOGGING_PARAMS):

    # Get existing logger (by logger_name), or creates one if the logger doesn;t yet exist
    # Then clears all handlers to avoid duplicate logging/adding handlers multiple times
    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Rotating File handler
    rf_handler = RotatingFileHandler(
        LOG_PATH / logger_name,
        maxBytes = logging_params["max_bytes"],
        backupCount = logging_params["backup_count"]
    )
    rf_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    rf_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Add the separate formatters
    logger.addHandler(rf_handler)
    logger.addHandler(console_handler)
    
    logger.setLevel(logging.INFO)
    return(logger)


