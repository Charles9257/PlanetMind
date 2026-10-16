import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

PLACEHOLDER_SECRET_VALUES = {
    "",
    "unsafe-dev-key-change-me",
    "change-me-control-plane-secret-key-2026",
    "change-me-service-secret",
}


def get_env_value(name: str, default: str | None = None) -> str | None:
    direct = os.getenv(name)
    if direct:
        return direct

    file_path = os.getenv(f"{name}_FILE")
    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise ImproperlyConfigured(f"Secret file for {name} does not exist: {file_path}")
        return path.read_text(encoding="utf-8").strip()

    return default


SECRET_KEY = get_env_value("DJANGO_SECRET_KEY", "unsafe-dev-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if host.strip()]

INSTALLED_APPS = [
    "django_prometheus",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "apps.accounts",
    "apps.organizations",
    "apps.governance",
    "apps.workflows",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DB_ENGINE = os.getenv("DJANGO_DB_ENGINE", "sqlite")
if DB_ENGINE == "postgres":
    if not os.getenv("DJANGO_DB_PASSWORD"):
        raise ImproperlyConfigured("DJANGO_DB_PASSWORD must be set when DJANGO_DB_ENGINE=postgres")
    DATABASES = {
        "default": {
            "ENGINE": "django_prometheus.db.backends.postgresql",
            "NAME": os.getenv("DJANGO_DB_NAME", "planetmind_db"),
            "USER": os.getenv("DJANGO_DB_USER", "postgres"),
            "PASSWORD": os.environ["DJANGO_DB_PASSWORD"],
            "HOST": os.getenv("DJANGO_DB_HOST", "localhost"),
            "PORT": os.getenv("DJANGO_DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django_prometheus.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = os.getenv("DJANGO_CORS_ALLOW_ALL", "true").lower() == "true"

_csrf_origins = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").strip()
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_origins.split(",") if origin.strip()]

CONTROL_PLANE_JWT_ISSUER = os.getenv("CONTROL_PLANE_JWT_ISSUER", "planetmind-control-plane")
CONTROL_PLANE_JWT_AUDIENCE = os.getenv("CONTROL_PLANE_JWT_AUDIENCE", "planetmind-internal-services")
CONTROL_PLANE_SERVICE_CLIENT_ID = os.getenv("CONTROL_PLANE_SERVICE_CLIENT_ID", "planetmind-backend")
CONTROL_PLANE_SERVICE_CLIENT_SECRET = get_env_value("CONTROL_PLANE_SERVICE_CLIENT_SECRET", "change-me-service-secret")
CONTROL_PLANE_SERVICE_USERNAME = os.getenv("CONTROL_PLANE_SERVICE_USERNAME", "svc_planetmind_backend")

if not DEBUG:
    if SECRET_KEY in PLACEHOLDER_SECRET_VALUES or len(SECRET_KEY or "") < 32:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be provided via environment or secret file and be at least 32 characters in production")
    if CONTROL_PLANE_SERVICE_CLIENT_SECRET in PLACEHOLDER_SECRET_VALUES or len(CONTROL_PLANE_SERVICE_CLIENT_SECRET or "") < 32:
        raise ImproperlyConfigured(
            "CONTROL_PLANE_SERVICE_CLIENT_SECRET must be provided via environment or secret file and be at least 32 characters in production"
        )

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "ISSUER": CONTROL_PLANE_JWT_ISSUER,
    "AUDIENCE": CONTROL_PLANE_JWT_AUDIENCE,
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "UPDATE_LAST_LOGIN": False,
}
