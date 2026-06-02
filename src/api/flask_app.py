"""
STEP 3b: Flask API (alternative to FastAPI)
Run: python src/api/flask_app.py
"""

import os
import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../models/best_model.pkl")

app = Flask(__name__)

# ── Load model once at startup ──
bundle = None
def get_model():
    global bundle
    if bundle is None:
        bundle = joblib.load(MODEL_PATH)
    return bundle


@app.route("/health", methods=["GET"])
def health():
    try:
        get_model()
        return jsonify({"status": "ok", "model": "loaded"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


@app.route("/predict", methods=["POST"])
def predict():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    required = ["area_sqft"]
    for field in required:
        if field not in payload:
            return jsonify({"error": f"Missing field: {field}"}), 422

    b = get_model()
    pipeline     = b["pipeline"]
    feature_cols = b["features"]

    area = float(payload["area_sqft"])
    data = {
        "area_sqft":     area,
        "log_area":      np.log1p(area),
        "township_area": float(payload.get("township_area", 0)),
        "amenity_score": int(payload.get("amenity_score", 0)),
        "has_clubhouse": int(payload.get("has_clubhouse", 0)),
        "has_school":    int(payload.get("has_school", 0)),
        "has_hospital":  int(payload.get("has_hospital", 0)),
        "has_mall":      int(payload.get("has_mall", 0)),
        "has_park":      int(payload.get("has_park", 0)),
        "has_pool":      int(payload.get("has_pool", 0)),
        "has_gym":       int(payload.get("has_gym", 0)),
        "location":      int(payload.get("location", 0)),
        "sub_area":      int(payload.get("sub_area", 0)),
        "property_type": int(payload.get("property_type", 0)),
        "company_name":  int(payload.get("company_name", 0)),
    }
    df_in = pd.DataFrame([{k: data[k] for k in feature_cols if k in data}])
    pred  = float(pipeline.predict(df_in)[0])

    return jsonify({
        "predicted_price_lakhs":   round(pred, 2),
        "predicted_price_millions": round(pred / 10, 3),
        "price_per_sqft_lakhs":    round(pred / max(area, 1), 4),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
