from flask import Flask, Response, jsonify

from api.envelope import err
from utils.logging import request_id
from utils.exceptions import AppError


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError) -> tuple[Response, int]:
        rid = request_id()
        app.logger.warning("App error %s: %s rid=%s", exc.code, exc.message, rid)
        return jsonify(err(exc.code, exc.message, {"requestId": rid})), exc.status_code

    @app.errorhandler(Exception)
    def handle_exception(exc: Exception) -> tuple[Response, int]:
        rid = request_id()
        app.logger.exception("Unhandled exception rid=%s", rid)
        return jsonify(err("internal_error", "Unexpected server error", {"requestId": rid})), 500
