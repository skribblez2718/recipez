# =============================================================================
# RECIPEZ DOCKER IMAGE
# =============================================================================
# Production-ready multi-stage build with security hardening
#
# Usage:
#   docker build -t recipez .
#   docker-compose up
#
# Or for development:
#   docker build --target development -t recipez:dev .

# -----------------------------------------------------------------------------
# Stage 1: Build dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and build wheels
COPY requirements.txt .

# Build wheels for all dependencies (excluding dev dependencies)
RUN pip wheel --no-cache-dir --wheel-dir /wheels \
    $(grep -v '^\s*#' requirements.txt | grep -v 'pytest' | tr '\n' ' ')

# -----------------------------------------------------------------------------
# Stage 2: Production image
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r recipez && useradd -r -g recipez recipez

WORKDIR /app

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY --chown=recipez:recipez . .

# Create required directories with proper permissions
RUN mkdir -p /app/recipez/static/uploads \
    && mkdir -p /app/recipez/certs \
    && chown -R recipez:recipez /app/recipez/static/uploads \
    && chown -R recipez:recipez /app/recipez/certs

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh

# Switch to non-root user
USER recipez

# Expose application port
EXPOSE 5000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Use entrypoint script for startup orchestration
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command: run Gunicorn with Docker config
CMD ["gunicorn", "-c", "gunicorn.docker.conf.py", "wsgi:app"]

# -----------------------------------------------------------------------------
# Stage 3: Development image (optional)
# -----------------------------------------------------------------------------
FROM production AS development

USER root

# Install development dependencies
RUN pip install --no-cache-dir pytest>=8.4.2

USER recipez

# Override command for development (use Flask dev server with reload)
CMD ["flask", "--app", "recipez", "run", "--host", "0.0.0.0", "--reload"]
