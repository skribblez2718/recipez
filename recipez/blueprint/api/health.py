"""
Health check endpoints for Docker and orchestration systems.

Provides two endpoints:
- /health - Basic health check (app + database connectivity)
- /health/ready - Readiness check (schema and tables exist)
"""

from flask import Blueprint, jsonify, current_app
from recipez.extensions import sqla_db
from sqlalchemy import text

health_api_bp = Blueprint("health_api", __name__, url_prefix="/health")


@health_api_bp.route("", methods=["GET"])
@health_api_bp.route("/", methods=["GET"])
def health_check():
    """
    Health check endpoint for Docker and orchestration systems.

    Returns:
        - 200 OK: Application is healthy
        - 503 Service Unavailable: Application or database is unhealthy
    """
    health_status = {
        "status": "healthy",
        "checks": {"app": "ok", "database": "unknown"},
    }

    # Check database connectivity
    try:
        with sqla_db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        current_app.logger.error(f"Health check database error: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = "error"
        return jsonify(health_status), 503

    return jsonify(health_status), 200


@health_api_bp.route("/ready", methods=["GET"])
def readiness_check():
    """
    Readiness check - verifies app is ready to receive traffic.

    More comprehensive than basic health check. Verifies:
    - Database connectivity
    - Schema exists with expected tables

    Returns:
        - 200 OK: Application is ready
        - 503 Service Unavailable: Application is not ready
    """
    ready_status = {"ready": True, "checks": {}}

    # Check database connectivity
    try:
        with sqla_db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        ready_status["checks"]["database"] = "ok"
    except Exception:
        ready_status["ready"] = False
        ready_status["checks"]["database"] = "error"
        return jsonify(ready_status), 503

    # Check if schema and core tables exist
    try:
        from sqlalchemy import inspect

        inspector = inspect(sqla_db.engine)
        tables = inspector.get_table_names(schema="recipez")

        # Check for essential tables
        essential_tables = ["recipez_user", "recipez_recipe", "recipez_category"]
        missing_tables = [t for t in essential_tables if t not in tables]

        if not missing_tables:
            ready_status["checks"]["schema"] = "ok"
        else:
            ready_status["ready"] = False
            ready_status["checks"]["schema"] = f"missing_tables: {missing_tables}"
    except Exception as e:
        ready_status["ready"] = False
        ready_status["checks"]["schema"] = f"error: {str(e)}"

    status_code = 200 if ready_status["ready"] else 503
    return jsonify(ready_status), status_code
