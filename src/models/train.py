"""
STEP 2: Model Training & Evaluation with MLflow
Pune Real Estate Price Prediction
Run: python src/models/train.py
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
import joblib
import mlflow
import mlflow.sklearn
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import (
    RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
)
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DATA_PATH   = os.path.join(os.path.dirname(__file__), "../../data/processed/pune_features.csv")
MODEL_DIR   = os.path.join(os.path.dirname(__file__), "../../models")
MLFLOW_URI  = os.path.join(os.path.dirname(__file__), "../../mlflow_runs")
TARGET      = "price_lakhs"
RANDOM_STATE = 42

FEATURE_COLS = [
    "area_sqft", "log_area", "township_area", "amenity_score",
    "has_clubhouse", "has_school", "has_hospital",
    "has_mall", "has_park", "has_pool", "has_gym",
    "location", "sub_area", "property_type", "company_name",
]


# ─────────────────────────────────────────────
# EVALUATION HELPERS
# ─────────────────────────────────────────────
def evaluate(y_true, y_pred, prefix=""):
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-6))) * 100
    metrics = {f"{prefix}mae": mae, f"{prefix}rmse": rmse,
               f"{prefix}r2": r2,   f"{prefix}mape": mape}
    return metrics


# ─────────────────────────────────────────────
# TRAIN ALL MODELS
# ─────────────────────────────────────────────
def train(data_path=DATA_PATH):
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(MLFLOW_URI, exist_ok=True)

    # ── Load data ──
    df = pd.read_csv(data_path)
    available_features = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available_features]
    y = df[TARGET]

    print(f"Dataset  : {X.shape[0]} rows × {X.shape[1]} features")
    print(f"Target   : {TARGET}  (mean={y.mean():.1f}, std={y.std():.1f})")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    # ── Preprocessing pipeline ──
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    preprocessor = ColumnTransformer([
        ("num", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale",  StandardScaler()),
        ]), num_cols),
    ], remainder="drop")

    # ── Models to try ──
    candidates = {
        "ridge":    Ridge(alpha=10),
        "lasso":    Lasso(alpha=1),
        "rf":       RandomForestRegressor(n_estimators=200, max_depth=10, random_state=RANDOM_STATE),
        "gbm":      GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, random_state=RANDOM_STATE),
        "extra_trees": ExtraTreesRegressor(n_estimators=200, random_state=RANDOM_STATE),
    }

    # ── MLflow experiment ──
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("pune_real_estate_price_prediction")

    results = {}
    best_r2  = -np.inf
    best_name = None

    for name, estimator in candidates.items():
        pipe = Pipeline([("prep", preprocessor), ("model", estimator)])

        with mlflow.start_run(run_name=name):
            pipe.fit(X_train, y_train)

            # Train metrics
            train_metrics = evaluate(y_train, pipe.predict(X_train), "train_")
            # Test metrics
            test_metrics  = evaluate(y_test,  pipe.predict(X_test),  "test_")

            # CV score
            cv_r2 = cross_val_score(pipe, X, y, cv=5, scoring="r2").mean()

            all_metrics = {**train_metrics, **test_metrics, "cv_r2": cv_r2}
            mlflow.log_params({"model": name})
            mlflow.log_metrics(all_metrics)
            mlflow.sklearn.log_model(pipe, artifact_path="model")

            results[name] = all_metrics
            flag = ""
            if test_metrics["test_r2"] > best_r2:
                best_r2   = test_metrics["test_r2"]
                best_name = name
                flag = " ← BEST"

            print(f"\n[{name}]{flag}")
            print(f"  Test  R²={test_metrics['test_r2']:.3f}  "
                  f"MAE={test_metrics['test_mae']:.2f}L  "
                  f"RMSE={test_metrics['test_rmse']:.2f}L  "
                  f"MAPE={test_metrics['test_mape']:.1f}%")
            print(f"  CV R²={cv_r2:.3f}")

    # ── Save best model ──
    best_pipe = Pipeline([("prep", preprocessor),
                          ("model", candidates[best_name])])
    best_pipe.fit(X_train, y_train)  # refit on train split

    model_path = os.path.join(MODEL_DIR, "best_model.pkl")
    joblib.dump({"pipeline": best_pipe, "features": available_features}, model_path)
    print(f"\n✅  Best model ({best_name}, R²={best_r2:.3f}) saved → {model_path}")

    # Save feature list
    feat_path = os.path.join(MODEL_DIR, "feature_columns.txt")
    with open(feat_path, "w") as f:
        f.write("\n".join(available_features))

    return results, best_name


if __name__ == "__main__":
    results, best = train()
    print(f"\nBest model: {best}")
