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

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Add the separate formatters
    logger.addHandler(console_handler)
    
    logger.setLevel(logging.INFO)
    return(logger)


