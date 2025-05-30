import logging
from pathlib import Path

from .config import logging_config

_log_dir = Path(logging_config.LOG_DIRECTORY)
_log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename=str(Path(logging_config.LOG_FILE)),
    encoding="utf-8",
)


def get_logger(name: str | None = None) -> logging.Logger:
    """設定されたロガーを返します。"""
    return logging.getLogger(name)
