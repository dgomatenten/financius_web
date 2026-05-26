from flask import Blueprint, jsonify, request

from api.envelope import ok
from services.export_service import ExportService

bp = Blueprint("export", __name__)
service = ExportService()


@bp.get("/export")
def export_data() -> tuple:
    export_format = request.args.get("format", "json")
    filters = dict(request.args)
    return jsonify(ok(service.export("demo-user", export_format, filters))), 200
