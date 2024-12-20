# Build stage
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Create non-root user with specific UID/GID
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash -m appuser && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copy application code
COPY --chown=appuser:appgroup . .

# Create uploads directory and set permissions
RUN mkdir -p /app/static/uploads && \
    chown -R appuser:appgroup /app/static/uploads

# Switch to non-root user
USER appuser

# Set environment variables
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Use entrypoint script for better signal handling
COPY --chown=appuser:appgroup docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
