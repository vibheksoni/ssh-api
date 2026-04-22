import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import ConfigManager


class Logger:
    """
    Centralized logging with file rotation and console output.

    Args:
        name: Logger name for identification.
        config: Optional ConfigManager instance.
    """

    _loggers: dict = {}

    def __init__(self, name: str, config: Optional[ConfigManager] = None) -> None:
        self._name = name
        self._config = config or ConfigManager()
        self._logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        if self._name in Logger._loggers:
            return Logger._loggers[self._name]

        logger = logging.getLogger(self._name)
        level = getattr(logging, self._config.get("logging.level", "INFO"))
        logger.setLevel(level)

        if not logger.handlers:
            self._add_console_handler(logger, level)
            self._add_file_handler(logger, level)

        Logger._loggers[self._name] = logger
        return logger

    def _add_console_handler(self, logger: logging.Logger, level: int) -> None:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s] %(message)s")
        console.setFormatter(fmt)
        logger.addHandler(console)

    def _add_file_handler(self, logger: logging.Logger, level: int) -> None:
        log_dir = Path(self._config.get("logging.directory", "ssh-service-logs"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = log_dir / timestamp
        log_path.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path / f"{self._name}.log", encoding="utf-8")
        file_handler.setLevel(level)
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(funcName)s - %(message)s"
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    def debug(self, msg: str, *args, **kwargs) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self._logger.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        self._logger.exception(msg, *args, **kwargs)
