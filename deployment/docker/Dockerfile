FROM python:3.10-slim-bookworm

# Apply all OS security patches, install only what is needed
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Non-root user — reduces container attack surface
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Install production dependencies
# requirements_docker.txt is lighter than requirements.txt (no PyCaret/Jupyter)
# and explicitly lists prometheus-fastapi-instrumentator
COPY requirements_docker.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_docker.txt

# Copy application source
COPY src/ ./src/
COPY models/ ./models/

RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "2", "--log-level", "info"]
