from flask import Blueprint, jsonify, request

from api.envelope import ok
from config.database import SessionLocal
from services.auth_service import AuthService
from services.google_oauth_service import GoogleOAuthService

bp = Blueprint("auth", __name__)


@bp.post("/register")
def register() -> tuple:
    """
    Register a new user.
    Request: {email: string, password: string}
    Response: {data: {user, accessToken, refreshToken, expiresIn}, error: null}
    """
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        service = AuthService(db)
        data = service.register(body.get("email", ""), body.get("password", ""))
        return jsonify(ok(data)), 201
    finally:
        db.close()


@bp.post("/login")
def login() -> tuple:
    """
    Login with email and password.
    Request: {email: string, password: string}
    Response: {data: {user, accessToken, refreshToken, expiresIn}, error: null}
    """
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        service = AuthService(db)
        data = service.login(body.get("email", ""), body.get("password", ""))
        return jsonify(ok(data)), 200
    finally:
        db.close()


@bp.post("/google")
def google_login() -> tuple:
    """
    Login with Google OAuth token.
    Request: {idToken: string}
    Response: {data: {user, accessToken, refreshToken, expiresIn}, error: null}
    """
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        service = GoogleOAuthService(db)
        data = service.login_with_google(body.get("idToken", ""))
        return jsonify(ok(data)), 200
    finally:
        db.close()


@bp.post("/refresh")
def refresh() -> tuple:
    """
    Refresh access token using refresh token.
    Request: {refreshToken: string}
    Response: {data: {accessToken, expiresIn}, error: null}
    """
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        service = AuthService(db)
        data = service.refresh(body.get("refreshToken", ""))
        payload = ok(data)
        # Backward-compatible aliases for mobile clients that parse tokens
        # from top-level or snake_case fields.
        payload.update(
            {
                "accessToken": data.get("accessToken"),
                "refreshToken": data.get("refreshToken"),
                "expiresIn": data.get("expiresIn"),
                "access_token": data.get("accessToken"),
                "refresh_token": data.get("refreshToken"),
                "expires_in": data.get("expiresIn"),
            }
        )
        return jsonify(payload), 200
    finally:
        db.close()


@bp.post("/logout")
def logout() -> tuple:
    """
    Revoke the current refresh token.
    Request: {refreshToken: string}
    Response: {data: {loggedOut: true}, error: null}
    """
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        service = AuthService(db)
        service.logout(body.get("refreshToken", ""))
        return jsonify(ok({"loggedOut": True})), 200
    finally:
        db.close()
