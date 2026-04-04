import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-gateway-key")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.proxy",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# No database needed for the gateway
DATABASES = {}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ]
        },
    }
]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Service registry — resolved via Docker internal DNS
SERVICE_URLS = {
    "auth":      os.environ.get("AUTH_SERVICE_URL",      "http://auth:8001"),
    "products":  os.environ.get("PRODUCT_SERVICE_URL",   "http://product:8002"),
    "inventory": os.environ.get("INVENTORY_SERVICE_URL", "http://inventory:8003"),
    "cart":      os.environ.get("CART_SERVICE_URL",      "http://cart:8004"),
    "orders":    os.environ.get("ORDER_SERVICE_URL",     "http://order:8005"),
    "payments":  os.environ.get("PAYMENT_SERVICE_URL",   "http://payment:8006"),
    "promotions":os.environ.get("PROMOTION_SERVICE_URL", "http://promotion:8007"),
    "reviews":   os.environ.get("REVIEW_SERVICE_URL",    "http://review:8008"),
    "shipping":  os.environ.get("SHIPPING_SERVICE_URL",  "http://shipping:8009"),
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
