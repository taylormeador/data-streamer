"""Simple ELK logging setup for Python services. Sends logs to Logstash via TCP while keeping console logging."""

import json
import logging
import socket
import os
from datetime import datetime
from contextvars import ContextVar
from typing import Optional

# Context variable for trace_id (set by middleware)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def set_trace_id(trace_id: str):
    """Set trace_id for current request context"""
    trace_id_var.set(trace_id)


def get_trace_id() -> Optional[str]:
    """Get trace_id from current request context"""
    return trace_id_var.get()


class LogstashHandler(logging.Handler):
    """Logging handler that sends JSON logs to Logstash via TCP.
    Fails silently if Logstash is unavailable (logs still go to console).
    """

    def __init__(self, service_name: str, host: str = "localhost", port: int = 5000):
        super().__init__()
        self.service_name = service_name
        self.host = host
        self.port = port

    def emit(self, record):
        try:
            # Build log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname.lower(),
                "message": record.getMessage(),
                "service": self.service_name,
                "logger": record.name,
            }

            # Add trace_id if available
            trace_id = get_trace_id()
            if trace_id:
                log_entry["trace_id"] = trace_id

            # Add any extra fields passed via extra={} parameter
            if hasattr(record, "__dict__"):
                for key, value in record.__dict__.items():
                    # Skip standard logging attributes
                    if key not in [
                        "name",
                        "msg",
                        "args",
                        "created",
                        "filename",
                        "funcName",
                        "levelname",
                        "levelno",
                        "lineno",
                        "module",
                        "msecs",
                        "message",
                        "pathname",
                        "process",
                        "processName",
                        "relativeCreated",
                        "thread",
                        "threadName",
                        "exc_info",
                        "exc_text",
                        "stack_info",
                        "getMessage",
                    ]:
                        log_entry[key] = value

            # Send to Logstash
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)  # Don't block forever
            sock.connect((self.host, self.port))
            sock.sendall(json.dumps(log_entry).encode() + b"\n")
            sock.close()

        except Exception as e:
            import sys

            print(f"Failed to send log to Logstash: {e}", file=sys.stderr)


def setup_logging(service_name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup logging with both console and Logstash handlers.

    Args:
        service_name: Name of your service (e.g., 'producer-service')
        level: Logging level (default: INFO)

    Returns:
        Configured root logger

    Example:
        logger = setup_logging('producer-service')
        logger.info('Service started')
        logger.info('User logged in', extra={'user_id': '123'})
    """
    # Get environment variables
    logstash_host = os.getenv("LOGSTASH_HOST", "localhost")
    logstash_port = int(os.getenv("LOGSTASH_PORT", "5000"))

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler (for local development and docker logs)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter("%(levelname)s [%(name)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Logstash handler (for ELK stack)
    try:
        logstash_handler = LogstashHandler(
            service_name=service_name, host=logstash_host, port=logstash_port
        )
        logstash_handler.setLevel(level)
        logger.addHandler(logstash_handler)
        logger.info(f"ELK logging enabled: {logstash_host}:{logstash_port}")
    except Exception as e:
        logger.warning(f"Could not connect to Logstash: {e}")

    return logger
