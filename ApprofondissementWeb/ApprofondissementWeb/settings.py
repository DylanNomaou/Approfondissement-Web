"""
Django settings for ApprofondissementWeb project — prod-ready (PythonAnywhere).
"""

from pathlib import Path
import os

# --- Chemins de base
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Sécurité & debug (pilotés par variables d'environnement)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
DEBUG = os.getenv("DJANGO_DEBUG", "0") in ("1", "true", "True")

# Domaines autorisés (ajoute/retire selon ton déploiement)
ALLOWED_HOSTS = [
    "hasanaldulaimi.com",
    "www.hasanaldulaimi.com",
    "hasansyria15.pythonanywhere.com",
    "www.hasansyria15.pythonanywhere.com",
    "127.0.0.1",
    "localhost",
]

# Origines CSRF de confiance (schéma https obligatoire en prod)
CSRF_TRUSTED_ORIGINS = [
    "https://hasanaldulaimi.com",
    "https://www.hasanaldulaimi.com",
    "https://hasansyria15.pythonanywhere.com",
    "https://www.hasansyria15.pythonanywhere.com",
    "http://www.hasanaldulaimi.com",
    "http://hasanaldulaimi.com",
    "http://hasansyria15.pythonanywhere.com",

]

# --- Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "restoplus",
]

# --- Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ApprofondissementWeb.urls"

# --- Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "ApprofondissementWeb.wsgi.application"

# --- Base de données (SQLite par défaut)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalisation
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Fichiers statiques & médias
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

# Dossier de collecte (pour `collectstatic`) — pointera dans PA : /static -> STATIC_ROOT
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

# Dossiers de sources (facultatif — tes assets d’app)
STATICFILES_DIRS = [
    BASE_DIR / "restoplus" / "static",
]

# --- Auth / User
AUTH_USER_MODEL = "restoplus.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_REDIRECT_URL = "/accueil/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
LOGIN_URL = "/accounts/login/"

# --- Sécurité HTTP (activée quand DEBUG=False)
# PythonAnywhere termine TLS devant ton app --> respecte X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True          # redirige HTTP -> HTTPS
    SECURE_HSTS_SECONDS = 31536000      # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Optionnel : renforce XSS/ContentType sniffing
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True

# --- Logs minimum (utile sur PA)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
