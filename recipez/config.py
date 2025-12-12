import os
import secrets
import re
import logging
from datetime import timedelta
from pathlib import Path


def _validate_model_id(model_id: str) -> str:
    """
    Validate OpenAI model ID format.

    Allows alphanumeric characters, hyphens, colons, dots, and underscores.
    Rejects invalid formats and returns safe default to prevent injection attacks.

    Args:
        model_id: The model ID to validate

    Returns:
        Validated model ID or safe default

    Example:
        >>> _validate_model_id("gpt-4")
        "gpt-4"
        >>> _validate_model_id("../../../etc/passwd")
        "gpt-3.5-turbo"  # Returns safe default
    """
    if not model_id or not isinstance(model_id, str):
        return "gpt-3.5-turbo"

    # Allow safe characters only: alphanumeric, hyphens, colons, dots, underscores
    # Max length 100 to prevent abuse
    if not re.match(r'^[a-zA-Z0-9._:-]{1,100}$', model_id):
        logging.warning(
            f"Invalid OPENAI model ID format detected: {model_id[:50]}, using safe default"
        )
        return "gpt-3.5-turbo"

    return model_id


class Config:
    """
    Base configuration class. Contains default configuration settings + configuration settings applicable to all environments.
    """

    # Application settings
    DOMAIN = os.environ.get("DOMAIN", "recipez.local")
    BASE_PATH = Path(__file__).resolve().parent

    # Security settings
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SESSION_TYPE = "sqlalchemy"
    SESSION_SQLALCHEMY_TABLE = "recipez_session"
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "max_overflow": 15,
        "echo": False,
        "connect_args": {"application_name": "recipez", "client_encoding": "utf8"},
    }

    # Argon2 settings
    RECIPEZ_ARGON_TIME_COST = 4
    RECIPEZ_ARGON_MEMORY_COST = 65536
    RECIPEZ_ARGON_PARALLELISM = 4
    RECIPEZ_ARGON_HASH_LEN = 64
    RECIPEZ_ARGON_SALT_LEN = 16

    # Encryption and JWT settings
    RECIPEZ_ENCRYPTION_KEY = os.environ.get("RECIPEZ_ENCRYPTION_KEY", "")
    RECIPEZ_HMAC_SECRET = os.environ.get("RECIPEZ_HMAC_SECRET", "")
    RECIPEZ_JWT_EXPIRE_TIME = timedelta(hours=12)

    # System user settings
    SYSTEM_USER_CREATED = False
    RECIPEZ_PRIVATE_KEY_SECRET = secrets.token_hex(64)
    RECIPEZ_SYSTEM_USER_JWT = None

    # Application paths and URLs
    RECIPEZ_APP_BASE_DIR = BASE_PATH

    # SMTP settings
    RECIPEZ_SMTP_HOSTNAME = "smtp.gmail.com"
    RECIPEZ_SMTP_PORT = 587
    RECIPEZ_SENDER_EMAIL = "recipeznotifications@gmail.com"
    RECIPEZ_SENDER_PASSWORD = os.environ.get("RECIPEZ_SENDER_PASSWORD")

    # OpenAI configuration
    RECIPEZ_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    RECIPEZ_OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "")
    RECIPEZ_OPENAI_RECIPE_MODEL_ID = _validate_model_id(
        os.environ.get("OPENAI_RECIPE_MODEL_ID", "gpt-3.5-turbo")
    )
    RECIPEZ_OPENAI_GROCERY_MODEL_ID = _validate_model_id(
        os.environ.get("OPENAI_GROCERY_MODEL_ID", "gpt-3.5-turbo")
    )

    # Frontend settings
    RECIPEZ_BOOTSTRAP_VERSION = "5.3.3"

    # JWT scopes
    RECIPEZ_SYSTEM_USER_JWT_SCOPES = [
        "code:create",
        "code:read",
        "code:update",
        "code:verify",
        "code:delete",
        "email:code:create",
        "user:create",
        "user:read",
    ]
    RECIPEZ_USER_JWT_SCOPES = [
        "category:create",
        "category:read",
        "category:update",
        "category:delete",
        "image:create",
        "image:read",
        "image:update",
        "image:delete",
        "ingredient:create",
        "ingredient:read",
        "ingredient:update",
        "ingredient:delete",
        "recipe:create",
        "recipe:read",
        "recipe:update",
        "recipe:delete",
        "step:create",
        "step:read",
        "step:update",
        "step:delete",
        "ai:create-recipe",
        "ai:modify-recipe",
        "ai:speech-to-text",
        "ai:grocery-list",
        "email:recipe:share",
    ]

    # Error handling
    RECIPEZ_ERROR_MESSAGE = "An error occured"

    # Logging settings
    LOG_LEVEL = logging.INFO  # Show INFO, WARNING, ERROR logs


class DevelopmentConfig(Config):
    """
    Development configuration. Insecure settings, debug output.
    """

    DOMAIN = "recipez.local"
    SESSION_COOKIE_SECURE = False
    TRUSTED_HOSTS = ["localhost", "127.0.0.1", "recipez.local"]
    RECIPEZ_WEB_HOSTNAME = f"http://{DOMAIN}:5000"
    RECIPEZ_JWT_ISSUER = f"http://{DOMAIN}:5000"
    RECIPEZ_JWT_AUDIENCE = f"http://{DOMAIN}:5000"


class ProductionConfig(Config):
    """
    Production configuration. Secure settings, no debug output.
    """

    DOMAIN = "recipez.skribblez.net"
    SESSION_COOKIE_SECURE = True
    TRUSTED_HOSTS = [f"{DOMAIN}"]
    RECIPEZ_WEB_HOSTNAME = f"https://{DOMAIN}"
    RECIPEZ_JWT_ISSUER = f"https://{DOMAIN}"
    RECIPEZ_JWT_AUDIENCE = f"https://{DOMAIN}"


config = {"development": DevelopmentConfig, "production": ProductionConfig}
