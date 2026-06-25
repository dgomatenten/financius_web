import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-only-replace-in-prod")

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
    "ledger",
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "financius_web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "src" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "financius_web.wsgi.application"

def _normalize_sqlite_url(db_url: str) -> str:
    prefix = "sqlite:///"
    if not db_url.startswith(prefix):
        return db_url

    path_part = db_url[len(prefix):]
    if not path_part.startswith("./"):
        return db_url

    abs_path = (BASE_DIR.parent / path_part[2:]).resolve()
    return f"{prefix}{abs_path}"


_default_db = f"sqlite:///{BASE_DIR.parent / 'data' / 'django_dev.db'}"
_db_url = os.environ.get("DJANGO_DATABASE_URL") or os.environ.get("DATABASE_URL") or _default_db
_db_url = _normalize_sqlite_url(_db_url)
DATABASES = {"default": dj_database_url.parse(_db_url, conn_max_age=600)}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "accounts.hashers.WerkzeugPasswordHasher",  # algorithm="werkzeug", handles scrypt + pbkdf2
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.auth.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "EXCEPTION_HANDLER": "financius_web.exception_handler.envelope_exception_handler",
}

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-prod")
ACCESS_TOKEN_TTL_SECONDS = int(os.environ.get("ACCESS_TOKEN_TTL_SECONDS", "3600"))
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "replace-me")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8001")
QR_PAIRING_TOKEN_TTL_SECONDS = int(os.environ.get("QR_PAIRING_TOKEN_TTL_SECONDS", "300"))
SYNC_MAX_PAYLOAD_BYTES = int(os.environ.get("SYNC_MAX_PAYLOAD_BYTES", str(50 * 1024 * 1024)))
SYNC_MAX_ITEMS_PER_REQUEST = int(os.environ.get("SYNC_MAX_ITEMS_PER_REQUEST", "10000"))

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "src" / "static"]
WHITENOISE_KEEP_ONLY_HASHED_FILES = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
