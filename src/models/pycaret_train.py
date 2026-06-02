"""
STEP 2b: AutoML with PyCaret
Pune Real Estate Price Prediction
Run: python src/models/pycaret_train.py
"""

import os
import warnings
import pandas as pd
import numpy as np
import joblib
warnings.filterwarnings("ignore")

DATA_PATH  = os.path.join(os.path.dirname(__file__), "../../data/processed/pune_features.csv")
MODEL_DIR  = os.path.join(os.path.dirname(__file__), "../../models")
TARGET     = "price_lakhs"

FEATURE_COLS = [
    "area_sqft", "log_area", "township_area", "amenity_score",
    "has_clubhouse", "has_school", "has_hospital",
    "has_mall", "has_park", "has_pool", "has_gym",
    "location", "sub_area", "property_type", "company_name",
    TARGET,
]


def run_pycaret():
    try:
        from pycaret.regression import (
            setup, compare_models, tune_model, finalize_model,
            save_model, pull, predict_model
        )
    except ImportError:
        print("PyCaret not installed. Run: pip install pycaret[full]")
        return

    os.makedirs(MODEL_DIR, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    available = [c for c in FEATURE_COLS if c in df.columns]
    df = df[available].dropna(subset=[TARGET])

    print(f"PyCaret dataset: {df.shape}")
    print("Setting up PyCaret experiment...")

    # ── Setup ──
    exp = setup(
        data=df,
        target=TARGET,
        session_id=42,
        train_size=0.8,
        normalize=True,
        transformation=True,
        remove_outliers=True,
        fold=5,
        verbose=False,
        html=False,
    )

    print("\nComparing all models (this takes ~1–3 minutes)...")
    best_models = compare_models(n_select=3, sort="R2", verbose=True)

    # ── Pull leaderboard ──
    leaderboard = pull()
    print("\n=== PyCaret Leaderboard ===")
    print(leaderboard[["Model", "R2", "MAE", "RMSE"]].head(5))

    # Save leaderboard
    leaderboard.to_csv(os.path.join(MODEL_DIR, "pycaret_leaderboard.csv"), index=False)

    # ── Tune best model ──
    best = best_models[0] if isinstance(best_models, list) else best_models
    print(f"\nTuning best model: {type(best).__name__}...")
    tuned = tune_model(best, optimize="R2", n_iter=20)

    # ── Finalize & save ──
    final = finalize_model(tuned)
    out_path = os.path.join(MODEL_DIR, "pycaret_best")
    save_model(final, out_path)
    print(f"\n✅  PyCaret best model saved → {out_path}.pkl")

    # ── Evaluate on hold-out ──
    preds = predict_model(final)
    metrics = pull()
    print("\n=== Final Model Metrics ===")
    print(metrics)

    return final


if __name__ == "__main__":
    run_pycaret()
