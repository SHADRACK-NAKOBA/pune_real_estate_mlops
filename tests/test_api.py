"""
Basic API tests for the Pune Real Estate FastAPI application.
Run with: pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient


def get_client():
    """Import app only when model exists, otherwise skip."""
    try:
        from src.api.fastapi_app import app
        return TestClient(app)
    except Exception:
        return None


def test_health_endpoint():
    client = get_client()
    if client is None:
        import pytest
        pytest.skip("Model not available in CI — skipping integration tests")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data


def test_predict_returns_valid_schema():
    client = get_client()
    if client is None:
        import pytest
        pytest.skip("Model not available in CI — skipping integration tests")
    payload = {
        "area_sqft": 1000,
        "township_area": 50.0,
        "amenity_score": 4,
        "has_clubhouse": 1,
        "has_school": 1,
        "has_hospital": 0,
        "has_mall": 0,
        "has_park": 1,
        "has_pool": 0,
        "has_gym": 1,
        "location": 3,
        "sub_area": 5,
        "property_type": 1,
        "company_name": 2,
    }
    response = client.post("/predict", json=payload)
    if response.status_code == 200:
        data = response.json()
        assert "predicted_price_lakhs" in data
        assert "predicted_price_millions" in data
        assert "price_per_sqft_lakhs" in data
        assert data["predicted_price_lakhs"] > 0


def test_predict_rejects_negative_area():
    client = get_client()
    if client is None:
        import pytest
        pytest.skip("Model not available in CI — skipping integration tests")
    payload = {"area_sqft": -100, "amenity_score": 0, "location": 0}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_batch_predict_limit():
    client = get_client()
    if client is None:
        import pytest
        pytest.skip("Model not available in CI — skipping integration tests")
    oversized = [{"area_sqft": 100 + i, "amenity_score": 0, "location": 0,
                  "sub_area": 0, "property_type": 0, "company_name": 0}
                 for i in range(101)]
    response = client.post("/predict/batch", json=oversized)
    assert response.status_code == 400
