"""
Централизованная настройка логирования и глобальных исключений.
"""

from __future__ import annotations

import logging
import sys
import threading
import traceback
from pathlib import Path


def configure_logging(log_file: str = "ahk_manipulator.log") -> None:
    """Настроить logging один раз на всё приложение."""
    root = logging.getLogger()
    if root.handlers:
        return

    log_path = Path(log_file).expanduser()
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    stream_handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)


def install_global_exception_hooks() -> None:
    """Установить перехват необработанных исключений."""

    def _sys_excepthook(exc_type, exc_value, exc_tb):
        logging.getLogger("global").critical(
            "Unhandled exception:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )

    def _thread_excepthook(args):
        logging.getLogger("global").critical(
            "Unhandled thread exception in %s:\n%s",
            getattr(args.thread, "name", "unknown"),
            "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)),
        )

    sys.excepthook = _sys_excepthook
    threading.excepthook = _thread_excepthook
