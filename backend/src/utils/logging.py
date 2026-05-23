import logging
from pathlib import Path
import uuid

from flask import Flask, Request, g, has_request_context, request


_REQUEST_ID_HEADER = "X-Request-ID"


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id()
        record.path = request.path if has_request_context() else "-"
        record.method = request.method if has_request_context() else "-"
        return True


def configure_logging(log_file: str) -> None:
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s "
        "request_id=%(request_id)s method=%(method)s path=%(path)s %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)

    root_logger = logging.getLogger()
    context_filter = RequestContextFilter()
    for handler in root_logger.handlers:
        handler.addFilter(context_filter)


def init_request_context(app: Flask) -> None:
    @app.before_request
    def bind_request_id() -> None:
        rid = request.headers.get(_REQUEST_ID_HEADER) or str(uuid.uuid4())
        g.request_id = rid

    @app.after_request
    def attach_request_id_header(response):
        response.headers[_REQUEST_ID_HEADER] = request_id()
        return response


def request_id() -> str:
    if has_request_context() and hasattr(g, "request_id"):
        return g.request_id
    return "-"
