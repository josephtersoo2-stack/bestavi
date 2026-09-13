from __future__ import annotations

import logging
from .crypto import sanitize_log_message


def _scrub_val(val: Any) -> Any:
    if isinstance(val, str):
        return sanitize_log_message(val)
    return val


class SecurityScrubberFilter(logging.Filter):
    """Logging filter that scrubs sensitive credentials, tokens, and keys from all emitted log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = sanitize_log_message(record.msg)
        if hasattr(record, "args") and record.args:
            if isinstance(record.args, dict):
                record.args = {k: _scrub_val(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(_scrub_val(a) for a in record.args)
        return True

