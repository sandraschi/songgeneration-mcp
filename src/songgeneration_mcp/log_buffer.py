"""In-memory ring buffer for process logs, exposed via ``GET /api/logs`` on the ASGI server."""

from __future__ import annotations

import logging
import os
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any

_lock = threading.Lock()
_MAX_LINES = max(50, min(50_000, int(os.getenv("SONGGEN_LOG_BUFFER_LINES", "500"))))
_buffer: deque[dict[str, Any]] = deque(maxlen=_MAX_LINES)
_setup_done = False


class RingBufferHandler(logging.Handler):
    """Append formatted log records to a fixed-size deque (thread-safe)."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            entry: dict[str, Any] = {
                "ts": datetime.fromtimestamp(record.created, tz=timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z"),
                "level": record.levelname.lower(),
                "logger": record.name,
                "message": msg,
            }
            with _lock:
                _buffer.append(entry)
        except Exception:
            self.handleError(record)


def setup_process_log_buffer() -> None:
    """Attach a ring-buffer handler to the root logger (once).

    Captures std library logs emitted in this process.
    """
    global _setup_done
    if _setup_done:
        return
    handler = RingBufferHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )

    root = logging.getLogger()
    if not any(isinstance(h, RingBufferHandler) for h in root.handlers):
        root.addHandler(handler)
    if root.level > logging.DEBUG:
        root.setLevel(logging.INFO)

    _setup_done = True
    logging.getLogger(__name__).info(
        "Process log buffer active (max %s lines, env SONGGEN_LOG_BUFFER_LINES).",
        _MAX_LINES,
    )


def get_recent_lines(limit: int) -> list[dict[str, Any]]:
    """Return up to ``limit`` most recent entries (oldest first within the slice)."""
    with _lock:
        lines = list(_buffer)
    if limit <= 0:
        return []
    return lines[-limit:]


def clear_buffer() -> int:
    """Clear the in-memory buffer. Returns number of entries removed."""
    with _lock:
        n = len(_buffer)
        _buffer.clear()
    return n
