"""
STEP: MLflow Setup & Viewer
Run: python scripts/setup_mlflow.py
Then open: http://localhost:5000
"""

import os
import subprocess
import sys

MLFLOW_DIR = os.path.join(os.path.dirname(__file__), "../mlflow_runs")

def start_mlflow_ui():
    os.makedirs(MLFLOW_DIR, exist_ok=True)
    abs_path = os.path.abspath(MLFLOW_DIR)
    print(f"Starting MLflow UI...")
    print(f"  Tracking URI : file://{abs_path}")
    print(f"  Dashboard    : http://localhost:5000")
    print(f"\nPress Ctrl+C to stop.\n")
    subprocess.run([
        sys.executable, "-m", "mlflow", "ui",
        "--backend-store-uri", f"file://{abs_path}",
        "--host", "0.0.0.0",
        "--port", "5000",
    ])

if __name__ == "__main__":
    start_mlflow_ui()
