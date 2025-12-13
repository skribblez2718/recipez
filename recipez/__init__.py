import os
import sys

try:
    import requests
except Exception:  # pragma: no cover - fallback for environments without requests
    import types

    requests = types.SimpleNamespace(Session=lambda: None, RequestException=Exception)
import uuid
import threading
import time

from flask import (
    Flask,
    request,
)
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from pathlib import Path
from werkzeug.middleware.proxy_fix import ProxyFix

from recipez.extensions import sqla_db
from recipez.config import config

load_dotenv()


#########################[ start create_app ]#########################
def create_app(test_config: dict = None) -> Flask:
    """
    Create and configure an instance of the Flask application.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    env = os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config[env])

    # Apply test config if provided
    if test_config:
        app.config.update(test_config)

    # Configure logging
    import logging
    log_level = app.config.get("LOG_LEVEL", logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    app.logger.setLevel(log_level)

    # Add ProxyFix middleware for Cloudflare
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Set derived config values
    domain = app.config["DOMAIN"]
    base_path = app.config["BASE_PATH"]
    app.config.update(
        SESSION_SQLALCHEMY=sqla_db,
        TRUSTED_HOSTS=["localhost", "127.0.0.1", domain],
        RECIPEZ_SYSTEM_USER_ID=uuid.uuid4(),
        RECIPEZ_SYSTEM_USER_NAME="yeschef",
        RECIPEZ_SYSTEM_USER_EMAIL=f"yeschef@{domain}",
        RECIPEZ_HTTP_SESSION=requests.Session(),
    )

    #########################[ start load user ]########################
    @app.before_request
    def load_user():
        """
        Load user from session.
        """
        if request.path.startswith("/static/") or request.path.startswith("/api/"):
            return None

        from recipez.utils import RecipezSessionUtils

        RecipezSessionUtils.load_user()

    #########################[ end before_request ]########################

    # Init SQLAlchemy
    sqla_db.init_app(app)

    # Init CSRF Protection
    from recipez.extensions import csrf
    csrf.init_app(app)

    # Issue 9 (MEDIUM): Init Rate Limiter
    from recipez.extensions import limiter
    limiter.init_app(app)

    # Register all models before migrations
    from recipez.model import RecipezSessionModel
    from recipez.interface import UUIDSqlAlchemySessionInterface

    # Migrations
    from recipez.extensions import migrate

    migrate.init_app(app, sqla_db)

    # Detect CLI / env guards
    is_db_cli = len(sys.argv) > 1 and sys.argv[1] == "db"
    skip_bootstrap_env = os.environ.get("SKIP_DB_BOOTSTRAP") == "1"

    # Custom session interface to avoid Flask-Session’s auto-table
    if not is_db_cli:
        app.session_interface = UUIDSqlAlchemySessionInterface(
            app, sqla_db, RecipezSessionModel, "session:"
        )

    from recipez.cli import init_app as init_cli_app

    init_cli_app(app)

    from recipez.db import init_app as db_init_app

    db_init_app(app)

    # ----- Non-DB bootstrap tasks (safe at init time) -----
    with app.app_context():
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        # Create certs directory if it doesn't exist
        certs_dir = base_path / "certs"
        os.makedirs(certs_dir, exist_ok=True)

        jwt_cert_path = certs_dir / "jwt_cert.pem"
        jwt_key_path = certs_dir / "jwt_key.pem"

        # Generate JWT keys if they don't exist
        if not jwt_key_path.exists() or not jwt_cert_path.exists():
            # Generate a private key
            jwt_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)

            # Write JWT private key without password protection
            with open(jwt_key_path, "wb") as key_file:
                key_file.write(
                    jwt_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )

            # Write JWT public key
            with open(jwt_cert_path, "wb") as cert_file:
                cert_file.write(
                    jwt_key.public_key().public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                )

            app.logger.info(
                f"Generated new JWT keys at {jwt_key_path} and {jwt_cert_path}"
            )

        # Load the JWT private key without password
        with open(jwt_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(), password=None
            )

        # Load the JWT public key
        with open(jwt_cert_path, "rb") as cert_file:
            public_key = serialization.load_pem_public_key(cert_file.read())

        # Store keys in app config
        app.config["RECIPEZ_JWT_PRIVATE_KEY"] = private_key
        app.config["RECIPEZ_JWT_PUBLIC_KEY"] = public_key

    # ----- DB-dependent bootstrap (deferred to first real request) -----
    _bootstrap_lock = threading.Lock()
    app.config.setdefault("_BOOTSTRAPPED", False)

    def _bootstrap_system_user_and_jwt() -> None:
        """
        Ensure the system user JWT is available.
        Runs only once (on first non-static/API request), and is skipped for CLI/env guard.
        """
        if is_db_cli or skip_bootstrap_env:
            app.logger.info("Skipping DB bootstrap due to CLI/env guard.")
            return

        from sqlalchemy import inspect, text

        insp = inspect(sqla_db.engine)
        try:
            table_exists = "recipez_user" in insp.get_table_names(schema="recipez")
            if not table_exists:
                app.logger.warning(
                    "Skipping system JWT bootstrap: recipez.recipez_user table does not exist."
                )
                return

            with sqla_db.engine.connect() as conn:
                result = conn.execute(
                    text('SELECT COUNT(*) FROM "recipez"."recipez_user"')
                )
                user_count = result.scalar()

            # If table is empty, create system user first
            if not user_count or user_count == 0:
                app.logger.info("User table empty; creating system user...")
                from recipez.db import _load_initial_data
                _load_initial_data()

            # Now find system user and generate JWT (always runs when table exists)
            try:
                from recipez.utils import RecipezSecretsUtils
                from recipez.repository import UserRepository

                system_user_email = app.config["RECIPEZ_SYSTEM_USER_EMAIL"]
                system_user_email_hmac = RecipezSecretsUtils.generate_hmac(
                    system_user_email
                )

                system_user = UserRepository.get_user_by_email_hmac(
                    system_user_email_hmac
                )
                if system_user is not None:
                    system_user_jwt = RecipezSecretsUtils.generate_jwt(
                        user_sub=system_user.user_sub,
                        scopes=app.config["RECIPEZ_SYSTEM_USER_JWT_SCOPES"],
                    )
                    app.config["RECIPEZ_SYSTEM_USER_JWT"] = system_user_jwt
                    app.logger.info("System JWT successfully generated.")
                else:
                    app.logger.warning(
                        "System user not found after creation attempt. Check _load_initial_data()."
                    )
                    app.config["RECIPEZ_SYSTEM_USER_JWT"] = None
            except Exception as e:
                app.logger.warning(f"System user bootstrap failed: {e}")
                app.config["RECIPEZ_SYSTEM_USER_JWT"] = None
        except Exception as e:
            app.logger.warning(f"Skipping system JWT bootstrap due to error: {e}")

    @app.before_request
    def _bootstrap_once():
        # Only run for real app routes (not static/api), once
        if request.path.startswith("/static/") or request.path.startswith("/api/"):
            return None
        if app.config.get("_BOOTSTRAPPED"):
            return None
        with _bootstrap_lock:
            if app.config.get("_BOOTSTRAPPED"):
                return None
            _bootstrap_system_user_and_jwt()
            app.config["_BOOTSTRAPPED"] = True

    from recipez.blueprint.blueprint import register_blueprints

    register_blueprints(app)

    # Issue 5 (HIGH): Add security headers middleware
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        # HSTS: Enforce HTTPS for 1 year (31536000 seconds) - only in production
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Prevent MIME-sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # XSS Protection (legacy but defense-in-depth)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Referrer policy (limit information leakage)
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Fix CSS MIME type for static files
        if request.path.endswith('.css'):
            response.headers['Content-Type'] = 'text/css; charset=utf-8'

        return response

    @app.context_processor
    def js_loader() -> dict:
        return {
            "js_modules": {
                "search": False,
                "recipe": False,
                "verify": False,
                "modal": False,
            }
        }

    def _code_cleanup_task() -> None:
        """Background task to remove expired codes every 24 hours."""
        with app.app_context():
            # Check if recipez_code table exists
            from sqlalchemy import inspect

            inspector = inspect(sqla_db.engine)
            table_exists = "recipez_code" in inspector.get_table_names(schema="recipez")

            if not table_exists:
                app.logger.warning(
                    "Skipping code cleanup: recipez.recipez_code table does not exist"
                )
                return

            while True:
                try:
                    from recipez.utils import RecipezCodeUtils

                    removed = RecipezCodeUtils.cleanup_codes()
                    if removed:
                        app.logger.info(f"Removed {removed} expired codes")
                except Exception as e:
                    app.logger.error(f"Error cleaning codes: {e}")
                time.sleep(24 * 60 * 60)

    if not is_db_cli:
        threading.Thread(target=_code_cleanup_task, daemon=True).start()

    return app


#########################[ end create_app ]#########################
