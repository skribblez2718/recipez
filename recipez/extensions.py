from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize SQLAlchemy
sqla_db = SQLAlchemy()

# Initialize Flask-Migrate
migrate = Migrate()

# Initialize CSRF Protection
csrf = CSRFProtect()

# Issue 9 (MEDIUM): Initialize Rate Limiter
# Using memory storage for development, should use Redis in production
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
