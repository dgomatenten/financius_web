from flask import Flask, jsonify, render_template
from sqlalchemy import text

import models  # noqa: F401 - register all model metadata before create_all
from api.envelope import ok
from api.error_handler import register_error_handlers
from api.v1 import register_v1_routes
from config.database import Base, engine
from config.settings import get_settings
from utils.logging import configure_logging, init_request_context, request_id


def _ensure_sync_events_schema() -> None:
    """Backfill missing columns on existing sqlite DBs to avoid sync runtime failures."""
    with engine.begin() as conn:
        def ensure_columns(table_name: str, required_columns: dict[str, str]) -> None:
            table_exists = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
                ),
                {"table_name": table_name},
            ).first()
            if not table_exists:
                return

            columns = {
                row[1]
                for row in conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            }
            for column_name, column_ddl in required_columns.items():
                if column_name not in columns:
                    conn.execute(
                        text(
                            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_ddl}"
                        )
                    )

        # sqlite compatibility shim for existing local DBs created before new columns.
        ensure_columns(
            "sync_events",
            {
            "sync_completed_at": "DATETIME",
            "status": "VARCHAR DEFAULT 'success'",
            "receipts_count": "INTEGER DEFAULT 0",
            "line_items_count": "INTEGER DEFAULT 0",
            "categories_count": "INTEGER DEFAULT 0",
            "shops_count": "INTEGER DEFAULT 0",
            "cards_count": "INTEGER DEFAULT 0",
            "duplicates_count": "INTEGER DEFAULT 0",
            "error_message": "VARCHAR",
            },
        )

        ensure_columns(
            "categories",
            {
                "is_deleted": "BOOLEAN DEFAULT 0",
                "created_at": "DATETIME",
                "updated_at": "DATETIME",
            },
        )

        ensure_columns(
            "receipts",
            {
                "shop_id": "VARCHAR",
                "category_id": "VARCHAR",
                "payment_card_id": "VARCHAR",
                "subtotal": "FLOAT DEFAULT 0",
                "tax_amount": "FLOAT DEFAULT 0",
                "note": "VARCHAR",
            },
        )

        ensure_columns(
            "receipt_line_items",
            {
                "line_total": "FLOAT DEFAULT 0",
            },
        )

        ensure_columns(
            "shops",
            {
                "normalized_name": "VARCHAR",
                "default_category_id": "VARCHAR",
                "merged_into_shop_id": "VARCHAR",
                "is_active": "BOOLEAN DEFAULT 1",
                "created_at": "DATETIME",
                "updated_at": "DATETIME",
            },
        )

        ensure_columns(
            "payment_cards",
            {
                "network": "VARCHAR",
                "color_hex": "VARCHAR",
                "is_active": "BOOLEAN DEFAULT 1",
                "created_at": "DATETIME",
                "updated_at": "DATETIME",
            },
        )


def create_app() -> Flask:
    settings = get_settings()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["MAX_CONTENT_LENGTH"] = settings.sync_max_payload_bytes
    configure_logging(settings.log_file)
    init_request_context(app)

    # Initialize database (create tables if they don't exist)
    Base.metadata.create_all(bind=engine)
    _ensure_sync_events_schema()

    app.register_blueprint(register_v1_routes())

    @app.get("/")
    def front_page() -> str:
        return render_template("index.html")

    @app.get("/login")
    def login_page() -> str:
        google_redirect_uri = f"{settings.api_base_url.rstrip('/')}/login"
        return render_template(
            "auth/login.html",
            google_client_id=settings.google_client_id,
            google_redirect_uri=google_redirect_uri,
        )

    @app.get("/register")
    def register_page() -> str:
        return render_template("auth/register.html")

    @app.get("/dashboard")
    def dashboard_page() -> str:
        return render_template("dashboard.html")

    @app.get("/sync/status")
    def sync_status_page() -> str:
        return render_template("sync/status.html")

    @app.get("/sync/pairing")
    def sync_pairing_page() -> str:
        return render_template("sync/pairing.html")

    @app.get("/receipts")
    def receipt_list_page() -> str:
        return render_template("receipts/list.html")

    @app.get("/receipts/<receipt_id>")
    def receipt_detail_page(receipt_id: str) -> str:
        return render_template("receipts/detail.html", receipt_id=receipt_id)

    @app.get("/master-data/categories")
    def categories_page() -> str:
        return render_template("master_data/categories.html")

    @app.get("/master-data/shops")
    def shops_page() -> str:
        return render_template("master_data/shops.html")

    @app.get("/master-data/cards")
    def cards_page() -> str:
        return render_template("master_data/cards.html")

    @app.get("/budgets/settings")
    def budget_settings_page() -> str:
        return render_template("budgets/settings.html")

    @app.get("/budgets/overview")
    def budget_overview_page() -> str:
        return render_template("budgets/overview.html")

    @app.get("/analytics/dashboard")
    def analytics_dashboard_page() -> str:
        return render_template("analytics/dashboard.html")

    @app.get("/api/v1/health")
    @app.get("/health")
    def health() -> tuple:
        return jsonify(ok({"status": "ok"}, {"requestId": request_id()})), 200

    register_error_handlers(app)
    return app


if __name__ == "__main__":
    app_settings = get_settings()
    create_app().run(
        host="0.0.0.0",
        port=app_settings.backend_port,
        debug=app_settings.flask_env == "development",
    )
