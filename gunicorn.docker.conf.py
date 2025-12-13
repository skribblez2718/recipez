"""
Docker-specific Gunicorn configuration for Recipez.

This configuration is optimized for containerized deployments with:
- Binding to all interfaces (required for Docker port mapping)
- Environment-variable configurable settings
- stdout/stderr logging for Docker log collection
- Memory management for long-running containers
"""

import os
import multiprocessing

# =============================================================================
# SERVER SOCKET
# =============================================================================
# Bind to all interfaces in container (required for Docker port mapping)
bind = "0.0.0.0:5000"

# =============================================================================
# WORKER CONFIGURATION
# =============================================================================
# Use environment variable or calculate based on CPU cores
# In containers, limit workers to prevent resource exhaustion
workers = int(
    os.environ.get(
        "GUNICORN_WORKERS", min(multiprocessing.cpu_count() * 2 + 1, 4)
    )
)
worker_class = "sync"

# Thread count per worker (for sync workers, this is 1)
threads = int(os.environ.get("GUNICORN_THREADS", 1))

# =============================================================================
# TIMEOUTS
# =============================================================================
# Extended timeout for AI-powered features (recipe generation, grocery lists)
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 300))  # 5 minutes default

# Keep-alive connections
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", 5))

# Graceful shutdown timeout
graceful_timeout = 30

# =============================================================================
# LOGGING
# =============================================================================
# Log to stdout/stderr for Docker log collection
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")

# Access log format with timing information
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
)

# =============================================================================
# PROCESS NAMING
# =============================================================================
proc_name = "recipez"

# =============================================================================
# SERVER MECHANICS
# =============================================================================
# Preload app for faster worker spawning and shared memory
preload_app = True

# Worker tmp directory (use memory for performance in containers)
worker_tmp_dir = "/dev/shm"

# Maximum requests before worker restart (prevents memory leaks)
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = 50

# =============================================================================
# SECURITY
# =============================================================================
# Limit request line size
limit_request_line = 4094

# Limit header field size
limit_request_field_size = 8190

# =============================================================================
# FORK SAFETY HOOKS
# =============================================================================
# Reset SQLAlchemy connection pool after fork to prevent connection sharing
# across worker processes. This fixes:
# - DuplicatePreparedStatement errors (psycopg3 statement cache conflicts)
# - StaleDataError (session identity map corruption)
# - ResourceClosedError (shared connection file descriptors)


def post_fork(server, worker):
    """
    Called after a worker has been forked.
    Disposes the SQLAlchemy engine to create fresh connections for this worker.
    """
    from recipez import create_app
    from recipez.extensions import sqla_db

    app = create_app()
    with app.app_context():
        sqla_db.engine.dispose()
        server.log.info(f"Worker {worker.pid}: Database connection pool reset")


def worker_exit(server, worker):
    """
    Called when a worker is about to exit.
    Ensures clean shutdown of database connections.
    """
    from recipez import create_app
    from recipez.extensions import sqla_db

    app = create_app()
    with app.app_context():
        sqla_db.session.remove()
        sqla_db.engine.dispose()
