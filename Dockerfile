FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir pandas numpy scikit-learn \
    joblib fastapi uvicorn flask pydantic requests openpyxl mlflow

# Copy project files
COPY src/ ./src/
COPY models/ ./models/
COPY data/ ./data/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]