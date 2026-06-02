"""
STEP 3: FastAPI Deployment
Pune Real Estate Price Prediction API
Run: uvicorn src.api.fastapi_app:app --reload --port 8000
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ─────────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../models/best_model.pkl")

def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. "
            "Run 'python src/models/train.py' first."
        )
    return joblib.load(MODEL_PATH)

model_bundle = None

def get_model():
    global model_bundle
    if model_bundle is None:
        model_bundle = load_model()
    return model_bundle


# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────
class PropertyInput(BaseModel):
    area_sqft:      float = Field(..., gt=0,  description="Property area in sq ft",     example=900)
    township_area:  float = Field(0.0, ge=0,  description="Township area in acres",      example=50.0)
    amenity_score:  int   = Field(0,   ge=0, le=7, description="0–7 amenity count",     example=4)
    has_clubhouse:  int   = Field(0,   ge=0, le=1)
    has_school:     int   = Field(0,   ge=0, le=1)
    has_hospital:   int   = Field(0,   ge=0, le=1)
    has_mall:       int   = Field(0,   ge=0, le=1)
    has_park:       int   = Field(0,   ge=0, le=1)
    has_pool:       int   = Field(0,   ge=0, le=1)
    has_gym:        int   = Field(0,   ge=0, le=1)
    location:       int   = Field(0,   ge=0, description="Encoded location id",         example=3)
    sub_area:       int   = Field(0,   ge=0, description="Encoded sub-area id",         example=5)
    property_type:  int   = Field(0,   ge=0, description="Encoded property type id",    example=1)
    company_name:   int   = Field(0,   ge=0, description="Encoded company id",          example=2)


class PredictionResponse(BaseModel):
    predicted_price_lakhs: float
    predicted_price_millions: float
    price_per_sqft_lakhs: float
    model_version: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────
app = FastAPI(
    title="Pune Real Estate Price Predictor",
    description="ML API to predict property prices in Pune (in Lakhs ₹)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    try:
        get_model()
        print("✅  Model loaded successfully.")
    except FileNotFoundError as e:
        print(f"⚠️  {e}")


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
def health_check():
    try:
        get_model()
        loaded = True
    except Exception:
        loaded = False
    return {"status": "ok" if loaded else "degraded", "model_loaded": loaded}


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(payload: PropertyInput):
    bundle = get_model()
    pipeline = bundle["pipeline"]
    feature_cols = bundle["features"]

    # Build input DataFrame
    data = {
        "area_sqft":     payload.area_sqft,
        "log_area":      np.log1p(payload.area_sqft),
        "township_area": payload.township_area,
        "amenity_score": payload.amenity_score,
        "has_clubhouse": payload.has_clubhouse,
        "has_school":    payload.has_school,
        "has_hospital":  payload.has_hospital,
        "has_mall":      payload.has_mall,
        "has_park":      payload.has_park,
        "has_pool":      payload.has_pool,
        "has_gym":       payload.has_gym,
        "location":      payload.location,
        "sub_area":      payload.sub_area,
        "property_type": payload.property_type,
        "company_name":  payload.company_name,
    }
    df_in = pd.DataFrame([{k: data[k] for k in feature_cols if k in data}])

    try:
        pred = float(pipeline.predict(df_in)[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")

    return PredictionResponse(
        predicted_price_lakhs=round(pred, 2),
        predicted_price_millions=round(pred / 10, 3),
        price_per_sqft_lakhs=round(pred / max(payload.area_sqft, 1), 4),
        model_version="1.0.0",
    )


@app.post("/predict/batch", tags=["Prediction"])
def predict_batch(properties: list[PropertyInput]):
    if len(properties) > 100:
        raise HTTPException(status_code=400, detail="Max 100 properties per batch.")
    return [predict(p) for p in properties]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.fastapi_app:app", host="0.0.0.0", port=8000, reload=True)
