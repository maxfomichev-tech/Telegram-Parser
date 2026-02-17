import logging
import os
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """Create a simple console logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def read_text_from_file(path: str) -> str:
    """Read text content from a file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def choose_input(text_arg: Optional[str], file_arg: Optional[str]) -> str:
    """Choose text input prioritizing text argument over file path."""
    if text_arg:
        return text_arg
    if file_arg:
        return read_text_from_file(file_arg)
    raise ValueError("Нужно указать --text или --file.")



