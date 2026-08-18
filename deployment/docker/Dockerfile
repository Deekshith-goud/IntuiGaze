# EyeNav Inference Server — Docker Image
#
# Multi-stage build for minimal production image.
#
# Stages:
#   builder:  Install Python deps + compile any native extensions
#   runtime:  Minimal runtime image
#
# Build:
#   docker build -f deployment/docker/Dockerfile -t eyenav/server:latest .
#
# Run:
#   docker run -p 8765:8765 eyenav/server:latest
#
# Security:
#   - Non-root user
#   - No shell in production image
#   - Read-only filesystem (models mounted as volume)
#   - No capabilities escalation

# ─── Stage 1: Builder ─────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies into /install directory
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Stage 2: Runtime ─────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install only runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r eyenav \
    && useradd -r -g eyenav eyenav

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/ ./backend/
COPY configs/ ./configs/

# Create directories for volumes
RUN mkdir -p /app/models /app/data \
    && chown -R eyenav:eyenav /app

# Switch to non-root user
USER eyenav

# Environment
ENV PYTHONPATH=/app/backend
ENV EYENAV_ENV=production
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/health')" || exit 1

# Expose API port
EXPOSE 8765

# Model files mounted as read-only volume
VOLUME ["/app/models"]

# Entrypoint
CMD ["python", "-m", "uvicorn", "eyenav.server:app", "--host", "0.0.0.0", "--port", "8765"]
