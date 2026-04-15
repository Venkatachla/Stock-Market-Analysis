import logging
from pathlib import Path


def get_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(log_level)
    fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)
    log_dir = Path('logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / 'pipeline.log')
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    return logger
