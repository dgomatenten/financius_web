from flask import Blueprint

from api.v1 import amortization, analytics, auth, budgets, export, master_data, pairing, receipts, recurring, sync


def register_v1_routes() -> Blueprint:
    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")
    api_v1.register_blueprint(auth.bp, url_prefix="/auth")
    api_v1.register_blueprint(sync.bp, url_prefix="/sync")
    api_v1.register_blueprint(pairing.bp, url_prefix="/pairing")
    api_v1.register_blueprint(receipts.bp, url_prefix="/receipts")
    api_v1.register_blueprint(master_data.bp)
    api_v1.register_blueprint(budgets.bp, url_prefix="/budgets")
    api_v1.register_blueprint(analytics.bp, url_prefix="/analytics")
    api_v1.register_blueprint(recurring.bp, url_prefix="/recurring")
    api_v1.register_blueprint(amortization.bp, url_prefix="/amortization")
    api_v1.register_blueprint(export.bp, url_prefix="/export")
    return api_v1
