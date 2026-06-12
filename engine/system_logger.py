"""
system_logger.py — Centralized logging for FORGE (Phase 1)
JSON-structured logs to stdout + plain lines to system_log.txt for admin UI.

Phase 5: Flask platform archived to _archive/ — stdlib `platform` no longer shadowed.
"""

import datetime
import json
import logging
import os
import sys
from typing import List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "system_log.txt")

_LEVEL_MAP = {
    "SUCCESS": logging.INFO,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "SKIP": logging.DEBUG,
}


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "action": getattr(record, "action", record.getMessage()),
            "result": getattr(record, "result", None),
            "detail": getattr(record, "detail", None),
        }
        return json.dumps({k: v for k, v in payload.items() if v is not None})


def _configure_logger() -> logging.Logger:
    logger = logging.getLogger("forge")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)
    return logger


_logger = _configure_logger()


def _append_log_file(line: str) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def log(action: str, result: str, detail: str = "") -> None:
    """
    Log a pipeline/platform event.
    Writes JSON to stdout and a plain line to system_log.txt.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level = result.upper()
    line = f"[{timestamp}] [{level}] {action}"
    if detail:
        line += f" | {detail}"
    _append_log_file(line + "\n")

    log_level = _LEVEL_MAP.get(level, logging.INFO)
    _logger.log(
        log_level,
        action,
        extra={"action": action, "result": level, "detail": detail or None},
    )


def get_last_n_lines(n: int = 50) -> List[str]:
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines[-n:]


def check_for_failures() -> List[str]:
    """Return list of CRITICAL lines from today."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    failures: List[str] = []
    if not os.path.exists(LOG_FILE):
        return failures
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if today in line and "[CRITICAL]" in line:
                failures.append(line.strip())
    return failures