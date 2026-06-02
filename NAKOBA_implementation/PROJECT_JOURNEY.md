# Pune Real Estate Price Prediction — Complete Project Journey
**Author: Shadrack Nakoba | Data Scientist**
**Date: June 2026 | Status: Local Complete → Cloud Deployment In Progress**

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Step-by-Step Journey](#3-step-by-step-journey)
4. [Tool Breakdown](#4-tool-breakdown)
5. [All Problems Encountered](#5-all-problems-encountered)
6. [Key Decisions Made](#6-key-decisions-made)
7. [Model Performance Summary](#7-model-performance-summary)
8. [Lessons Learned](#8-lessons-learned)

---

## 1. Project Overview

### What This Project Does
This project is a **production-grade Machine Learning system** that predicts residential property prices in Pune, India. A user provides property features (location, area, amenities, property type, builder) and the system returns the predicted price in Indian Rupees (Lakhs).

**One Lakh = 100,000 INR ≈ $1,200 USD**

The system is exposed as a REST API, meaning any website, mobile app, or business tool can call it over HTTP and receive a price estimate in real time.

### What Problem It Solves
Pune is one of India's fastest-growing real estate markets. Buyers overpay, sellers underprice, and brokers make information asymmetry their business model. This project removes that asymmetry by giving anyone — buyer, seller, developer, investor — an instant, data-driven price estimate based on 15 objective features.

**Before this project:** A buyer relies on a broker's word, which is inherently biased.
**After this project:** A buyer calls the API with property details and gets an ML-backed price estimate within milliseconds.

### Who Benefits From It
| Stakeholder | Benefit |
|---|---|
| Home buyers | Independent price check before negotiating |
| Property sellers | Data-backed pricing without broker bias |
| Real estate developers | Portfolio valuation automation |
| Banks and NBFCs | Loan-to-value ratio verification |
| PropTech startups | Embeddable pricing engine via API |
| Data scientists | Reference MLOps implementation for regression problems |

### Dataset
- **200 Pune property records** scraped and compiled from public listings
- Raw files: `Pune_Real_Estate_Data.xlsx` + `data_cleaned.csv`
- 18 raw features → 15 engineered production features after preprocessing
- Target variable: `price_lakhs` (property price in Lakhs INR)

---

## 2. Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    PUNE REAL ESTATE MLOPS ARCHITECTURE                   ║
╚══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│  DATA LAYER                                                              │
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐                           │
│  │  Pune_Real_      │    │  data_cleaned    │                           │
│  │  Estate_Data     │    │  .csv            │                           │
│  │  .xlsx           │    │  (secondary)     │                           │
│  │  (primary)       │    │                  │                           │
│  └────────┬─────────┘    └────────┬─────────┘                          │
│           │                       │                                      │
│           └───────────┬───────────┘                                     │
│                       ▼                                                  │
│           ┌───────────────────────┐                                     │
│           │   src/data/           │  ← DVC tracks this file             │
│           │   preprocess.py       │                                     │
│           │   • Clean columns     │                                     │
│           │   • Binary amenities  │                                     │
│           │   • log_area feature  │                                     │
│           │   • amenity_score     │                                     │
│           └───────────┬───────────┘                                     │
│                       │                                                  │
│                       ▼                                                  │
│           ┌───────────────────────┐                                     │
│           │  data/processed/      │                                     │
│           │  pune_features.csv    │  ← 200 rows × 16 columns            │
│           └───────────┬───────────┘                                     │
└───────────────────────┼─────────────────────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────────────────────┐
│  TRAINING LAYER       ▼                                                  │
│                                                                          │
│           ┌───────────────────────┐                                     │
│           │  src/models/train.py  │                                     │
│           │  • 80/20 train-test   │                                     │
│           │  • 5 model candidates │                                     │
│           │  • 5-fold CV per model│                                     │
│           └──────────┬────────────┘                                     │
│                      │                                                   │
│          ┌───────────┴───────────┐                                      │
│          ▼           ▼           ▼                                       │
│  ┌──────────────┐ ┌──────────┐ ┌──────────────────┐                   │
│  │  MLflow      │ │  5 Model │ │  models/          │                   │
│  │  Tracking    │ │  Runs    │ │  best_model.pkl   │                   │
│  │  sqlite:///  │ │  Logged  │ │  (GBM winner)     │                   │
│  │  mlflow.db   │ │          │ │  feature_columns  │                   │
│  └──────────────┘ └──────────┘ │  .txt             │                   │
│                                 └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────────────────────┐
│  API LAYER            ▼                                                  │
│                                                                          │
│           ┌───────────────────────────────┐                            │
│           │    src/api/fastapi_app.py      │                            │
│           │                               │                            │
│           │  GET  /health    → status ok  │                            │
│           │  POST /predict   → price (L)  │                            │
│           │  POST /predict/batch → list   │                            │
│           │  GET  /docs      → Swagger UI │                            │
│           └───────────────────────────────┘                            │
│                     ↕ Port 8000                                         │
└─────────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────────────────────┐
│  CONTAINER LAYER      ▼                                                  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────┐               │
│  │  Docker Compose                                       │               │
│  │                                                       │               │
│  │  ┌─────────────────────┐  ┌────────────────────┐   │               │
│  │  │  pune_re_api        │  │  pune_re_mlflow     │   │               │
│  │  │  Port: 8000         │  │  Port: 5001         │   │               │
│  │  │  FastAPI + Uvicorn  │  │  MLflow UI          │   │               │
│  │  └─────────────────────┘  └────────────────────┘   │               │
│  └─────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────────────────────┐
│  CI/CD LAYER          ▼                                                  │
│                                                                          │
│  git push → GitHub Actions → Tests → Docker Build → Push Hub           │
│                                    → Deploy to EC2 / ECS                │
└─────────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────────────────────┐
│  CLOUD LAYER          ▼                                                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │  AWS Options (in order of complexity)                       │        │
│  │                                                              │        │
│  │  Option A: EC2 + Nginx + Docker Compose (simplest)          │        │
│  │  Option B: ECS Fargate + ALB (managed, no server ops)       │        │
│  │  Option C: EKS Kubernetes (full orchestration)              │        │
│  └────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘

CLIENT REQUEST FLOW
───────────────────
Browser / curl / App
        │
        ▼ HTTPS (Port 443)
   Nginx / ALB / Ingress
        │
        ▼ HTTP (Port 8000)
   FastAPI Application
        │
        ▼
   joblib.load(best_model.pkl)
        │
        ▼
   Scikit-learn Pipeline
   [Imputer → Scaler → GBM]
        │
        ▼
   {"predicted_price_lakhs": 87.4}
        │
        ▼
   Back to client (JSON)
```

---

## 3. Step-by-Step Journey

### Phase 0 — Problem Definition and Data Collection
**Step 0.1 — Define the ML problem**
The problem was defined as a supervised regression task: given property features, predict a continuous target variable (price in Lakhs). Regression was chosen over classification because we want an exact price, not a price range bucket.

**Step 0.2 — Collect raw data**
Two data sources were compiled into the `data/raw/` folder:
- `Pune_Real_Estate_Data.xlsx` — primary dataset with property listings
- `data_cleaned.csv` — secondary cleaned dataset with overlapping and additional records

The raw data contained 200 records with 18 raw columns including: location, sub-area, property type, company name, township name, township area, price, area in sqft, and seven amenity columns (clubhouse, school, hospital, mall, park, pool, gym).

Data was collected by browsing Pune real estate portals (MagicBricks, 99acres, Housing.com) and compiling structured records into an Excel sheet. This is common in Indian PropTech where structured APIs are not available.

---

### Phase 1 — Development Environment Setup (Windows 11)
**Step 1.1 — Install Python 3.10**
Python 3.10 was installed via pyenv-win on Windows. The exact version matters because scikit-learn and PyCaret have version-specific compatibility constraints.

Command used:
```powershell
pyenv install 3.10.11
pyenv global 3.10.11
```

**Step 1.2 — Create virtual environment**
```powershell
cd C:\Users\admin\Desktop\pune_real_estate_mlops
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Step 1.3 — Install dependencies**
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

The `.venv` got corrupted twice due to disk space and partial installs. Each time it was recreated from scratch using the full Python path.

**Step 1.4 — Set up project folder structure**
Created the folder layout: `data/`, `src/`, `models/`, `deployment/`, `scripts/`, `.github/workflows/`. The structure was designed around separation of concerns — data ingestion separate from modeling, modeling separate from serving.

---

### Phase 2 — Data Preprocessing (`src/data/preprocess.py`)
**Step 2.1 — Load raw data**
Both raw files (XLSX and CSV) were loaded using pandas. The XLSX required `openpyxl` as engine; the CSV was loaded with standard `pd.read_csv()`.

**Step 2.2 — Standardize column names**
All column names were lowercased, stripped of whitespace, and spaces replaced with underscores. This prevents case-sensitivity bugs downstream.

**Step 2.3 — Clean numeric columns**
The `area_sqft` and `price_lakhs` columns contained mixed string-and-number data (e.g., "1200 sqft", "85 Lakhs"). Regex extraction pulled the numeric part from these strings. Non-parseable rows were dropped.

**Step 2.4 — Engineer binary amenity features**
Seven amenity columns (clubhouse, school, hospital, mall, park, pool, gym) contained text values like "Yes"/"No"/"Available"/"NA". These were mapped to 0 or 1 integers, creating clean binary features:
- `has_clubhouse`, `has_school`, `has_hospital`, `has_mall`, `has_park`, `has_pool`, `has_gym`

**Step 2.5 — Encode categorical features**
Four categorical columns — location, sub_area, property_type, company_name — were label-encoded to integers. This was done with a simple `{value: index}` mapping. Label encoding was chosen over one-hot encoding because tree-based models (which dominated the leaderboard) handle ordinal integers natively without the dimensionality explosion of OHE.

**Step 2.6 — Engineer numerical features**
Three derived numerical features were created:
- `log_area = np.log1p(area_sqft)` — reduces right skew; log transformation is standard for area/price features
- `amenity_score = sum of all 7 binary amenity flags` — single score capturing overall amenity quality (0-7 scale)
- `township_area` — already present in raw data; missing values imputed with column median

**Step 2.7 — Save processed data**
The cleaned and engineered DataFrame was saved to `data/processed/pune_features.csv` — the input to all downstream model training steps.

**Step 2.8 — DVC tracking**
The preprocessing step was registered in `dvc.yaml` so DVC could track which input files produced which output files, enabling reproducible reruns and data versioning.

---

### Phase 3 — Model Training (`src/models/train.py`)
**Step 3.1 — Load processed data**
The 15 feature columns defined in `FEATURE_COLS` were extracted from `pune_features.csv`. The target `price_lakhs` was separated from features.

**Step 3.2 — Train/test split**
An 80/20 split with `random_state=42` was used. With 200 records, this gives 160 training samples and 40 test samples. The random state ensures reproducible splits — any team member running the script gets identical results.

**Step 3.3 — Build preprocessing pipeline**
A scikit-learn `ColumnTransformer` was built:
- Numerical columns: `SimpleImputer(strategy="median")` → `StandardScaler()`
- The pipeline was embedded inside each model's `Pipeline` so preprocessing and prediction always travel together as a single object

Embedding preprocessing inside the pipeline is critical for production. It guarantees the same transformations applied during training are applied at inference time, eliminating training-serving skew.

**Step 3.4 — Define 5 candidate models**
| Model | Key Hyperparameters |
|---|---|
| Ridge Regression | alpha=10 |
| Lasso Regression | alpha=1 |
| Random Forest | n_estimators=200, max_depth=10 |
| Gradient Boosting | n_estimators=200, learning_rate=0.05 |
| Extra Trees | n_estimators=200 |

**Step 3.5 — Set up MLflow tracking**
```python
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("pune_real_estate_price_prediction")
```
Each model training run was wrapped in `with mlflow.start_run(run_name=name):` to automatically log parameters, metrics, and model artifacts.

**Step 3.6 — Train and evaluate all 5 models**
For each model:
1. Fit on training split
2. Predict on training and test splits
3. Calculate: MAE, RMSE, R², MAPE
4. Run 5-fold cross-validation and log `cv_r2`
5. Log everything to MLflow
6. Compare test R² to current best

**Step 3.7 — Save the winner**
The model with highest test R² (Gradient Boosting, R²=0.795) was saved as:
```python
joblib.dump({"pipeline": best_pipe, "features": available_features}, "models/best_model.pkl")
```
The feature list was also saved to `models/feature_columns.txt` to prevent feature mismatch errors at inference time.

---

### Phase 4 — AutoML with PyCaret (`src/models/pycaret_train.py`)
**Step 4.1 — PyCaret setup**
PyCaret's `setup()` was called with:
- `normalize=True` — scales features
- `transformation=True` — applies Box-Cox or Yeo-Johnson transformation
- `remove_outliers=True` — drops statistical outliers from training
- `fold=5` — 5-fold cross-validation benchmark

**Step 4.2 — compare_models()**
PyCaret ran every available regression model (20+) in a single call, ranked by R². This provided a second opinion on which algorithms work best for this data.

**Step 4.3 — tune_best_model()**
The top model was further tuned with Bayesian optimization (20 iterations). The tuned model was saved to `models/pycaret_best.pkl`.

PyCaret's results confirmed the scikit-learn experiment: gradient boosting variants consistently dominated.

---

### Phase 5 — FastAPI REST API (`src/api/fastapi_app.py`)
**Step 5.1 — Define Pydantic input schema**
```python
class PropertyInput(BaseModel):
    area_sqft: float = Field(..., gt=0)
    township_area: float = Field(0.0, ge=0)
    amenity_score: int = Field(0, ge=0, le=7)
    has_clubhouse: int = Field(0, ge=0, le=1)
    # ... 11 more fields
```
Pydantic automatically validates every incoming request. If a field is missing or out of range, FastAPI returns a `422 Unprocessable Entity` error with a clear JSON explanation — no manual validation code needed.

**Step 5.2 — Lazy model loading**
The model is loaded once at startup via a global singleton:
```python
model_bundle = None
def get_model():
    global model_bundle
    if model_bundle is None:
        model_bundle = load_model()
    return model_bundle
```
This avoids reloading the ~50MB model on every request, keeping response times below 50ms.

**Step 5.3 — Prediction endpoint**
The `/predict` endpoint:
1. Receives validated JSON
2. Constructs a pandas DataFrame with the 15 features (computing `log_area` from `area_sqft` inline)
3. Calls `pipeline.predict(df_in)` — the pipeline applies imputation, scaling, and GBM inference
4. Returns price in Lakhs, Millions, and per-sqft

**Step 5.4 — CORS middleware**
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```
CORS allows any website (running in a browser) to call this API without cross-origin policy errors. Essential for browser-based PropTech apps.

**Step 5.5 — Swagger UI**
FastAPI auto-generates `/docs` (Swagger UI) and `/redoc`. These let developers explore and test the API in a browser without writing any code.

---

### Phase 6 — Docker Containerization
**Step 6.1 — Dockerfile**
```dockerfile
FROM python:3.10-slim
RUN apt-get update && apt-get install -y build-essential curl git
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "src.api.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key decisions:
- `python:3.10-slim` — minimal base image; reduces attack surface and image size
- `COPY requirements.txt` before `COPY . .` — Docker layer caching means pip install only reruns when requirements change, not on every code change
- `--no-cache-dir` — avoids storing pip cache inside the image (saves 200-400MB)

**Step 6.2 — Docker Compose**
Two services defined:
- `pune_re_api` — FastAPI on port 8000, with `models/` and `data/` mounted read-only
- `pune_re_mlflow` — MLflow UI on port 5001 (5000 inside container, mapped to 5001 to avoid conflict with local MLflow)

The `restart: unless-stopped` policy ensures containers restart after EC2 reboots.

---

### Phase 7 — GitHub and Version Control
**Step 7.1 — Initialize git and create .gitignore**
The `.gitignore` excludes:
- `.venv/` — virtual environment (recreatable)
- `mlruns/`, `mlflow.db` — MLflow tracking data (regeneratable by running train.py)
- `models/best_model.pkl` — large binary file (would slow git; use DVC for this)
- `data/raw/` — raw data (tracked by DVC, not git)
- `.env` — secrets (never commit)

**Step 7.2 — Push to GitHub**
```powershell
git init
git add .
git commit -m "Initial commit: Pune Real Estate MLOps pipeline"
git remote add origin https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops.git
git push -u origin main
```

---

### Phase 8 — AWS Cloud Deployment (In Progress)
See `CONTINUATION.md` for the exact step-by-step continuation guide for:
- Docker Hub push
- GitHub Actions CI/CD
- AWS EC2 deployment
- AWS ECS Fargate
- Kubernetes
- Live public URL verification

---

## 4. Tool Breakdown

### Python 3.10
**What it is:** The programming language used for the entire project.
**What it does in this project:** Runs preprocessing, model training, the FastAPI server, and all scripts.
**Why chosen over alternatives:** Python 3.10 specifically because PyCaret 3.x and scikit-learn 1.3+ have tested compatibility with this version. Python 3.11+ had dependency conflicts with PyCaret at time of development. Python 3.9 lacks some type hint syntax used in the codebase.
**Where in architecture:** Every layer — data, training, API.

---

### Pandas
**What it is:** Python's primary data manipulation library.
**What it does in this project:** Loads XLSX and CSV files, cleans columns, creates engineered features, saves processed CSV. At inference time, constructs the DataFrame fed to the scikit-learn pipeline.
**Why chosen:** Industry standard for tabular data in Python. No viable alternative for XLSX + CSV workflows at this scale.
**Where in architecture:** Data layer (preprocessing) and API layer (inference).

---

### Scikit-learn
**What it is:** Python's foundational machine learning library.
**What it does in this project:** Provides Ridge, Lasso, Random Forest, Gradient Boosting, and Extra Trees models. Provides `Pipeline` (combines preprocessing + model into one object), `ColumnTransformer` (applies different transforms to different columns), `SimpleImputer` (fills NaN), and `StandardScaler` (normalizes features).
**Why chosen over alternatives:** Scikit-learn pipelines are the gold standard for production ML. XGBoost/LightGBM would likely give marginally better results but introduce heavier dependencies. For 200 rows, scikit-learn's GBM is sufficient and simpler to deploy.
**Where in architecture:** Training layer exclusively. The fitted `Pipeline` object inside `best_model.pkl` is what the API calls at inference time.

---

### MLflow
**What it is:** An open-source platform for managing the ML lifecycle.
**What it does in this project:** Tracks every model training run. Logs hyperparameters (model name), metrics (MAE, RMSE, R², MAPE, CV R²), and model artifacts. Provides a web UI at localhost:5000 to compare runs visually.
**Why chosen over alternatives:** MLflow is tool-agnostic — it works with scikit-learn, XGBoost, TensorFlow, PyTorch, etc. Alternatives like Weights & Biases (W&B) and Neptune.ai require cloud accounts and internet connectivity. MLflow runs entirely locally.
**Why SQLite backend:** On Windows, MLflow's default `file://` tracking URI fails due to path format differences between Windows and POSIX systems. SQLite (`sqlite:///mlflow.db`) is a local file-based database that works identically on Windows and Linux. This was a critical fix found during development.
**Where in architecture:** Training layer — records all experiments for comparison and reproducibility.

---

### PyCaret
**What it is:** A low-code AutoML library that wraps scikit-learn, XGBoost, LightGBM, and others.
**What it does in this project:** Runs a broad model comparison (20+ algorithms) in a single `compare_models()` call. Used as a second opinion to confirm the scikit-learn experiment's winner. The best PyCaret model is saved as `models/pycaret_best.pkl` as an alternative serving option.
**Why chosen over alternatives:** Auto-sklearn is Linux-only. H2O requires JVM. TPOT is slow. PyCaret is the fastest and most Windows-friendly AutoML option with minimal setup.
**Where in architecture:** Training layer (optional, parallel to main training pipeline).

---

### FastAPI
**What it is:** A modern Python web framework for building REST APIs.
**What it does in this project:** Hosts the prediction API. Receives JSON requests, validates them with Pydantic, runs inference, returns JSON responses. Auto-generates /docs (Swagger UI) and /redoc.
**Why chosen over Flask:** FastAPI is 2-3x faster than Flask due to async support and Starlette underneath. It has built-in request validation via Pydantic (Flask requires manual validation). It auto-generates interactive API documentation. For a production ML API serving real clients, FastAPI is the modern standard.
**Why not Django REST Framework:** Django is a full web framework (ORM, admin panel, templating) — far too heavy for a single ML inference endpoint.
**Where in architecture:** API layer — the only user-facing component.

---

### Uvicorn
**What it is:** An ASGI (Async Server Gateway Interface) server for Python.
**What it does in this project:** Runs the FastAPI application. Handles HTTP connections, routes requests to FastAPI handlers, and manages worker processes.
**Why chosen:** FastAPI is ASGI-based and requires an ASGI server. Uvicorn is FastAPI's recommended server. Gunicorn (WSGI) cannot run ASGI apps natively.
**Where in architecture:** API layer — sits between Nginx (or Docker's port mapping) and the FastAPI application.

---

### Joblib
**What it is:** A Python serialization library optimized for large numpy arrays and scikit-learn objects.
**What it does in this project:** Serializes the fitted scikit-learn `Pipeline` object to `models/best_model.pkl` after training. Deserializes it at API startup.
**Why chosen over pickle:** Joblib is faster and more memory-efficient than pickle for large numpy arrays (which scikit-learn models contain internally). It is the recommended serialization method in scikit-learn's own documentation.
**Where in architecture:** Bridge between training layer and API layer.

---

### DVC (Data Version Control)
**What it is:** A version control system for data and ML pipelines, built on top of git.
**What it does in this project:** Defines the pipeline in `dvc.yaml` (preprocess → train → pycaret stages). Tracks which input files produce which output files. Enables `dvc repro` to rerun only changed stages. Locks reproducibility of the entire data pipeline.
**Why chosen over alternatives:** DVC integrates with git — every code commit can reference an exact data state. Alternatives like Pachyderm require Kubernetes. MLflow's artifact tracking can track model files but not the full data pipeline graph.
**Where in architecture:** Data layer and training layer — orchestrates the pipeline but does not serve production traffic.

---

### Docker
**What it is:** A containerization platform that packages an application and all its dependencies into a portable image.
**What it does in this project:** Packages the FastAPI app, Python runtime, all pip dependencies, model file, and data into a single Docker image. The image can run identically on a developer's laptop, CI server, EC2 instance, or ECS container.
**Why chosen:** Containers eliminate "works on my machine" problems. The model trained on Windows runs in a Linux container in production. Docker is the industry standard for this.
**Where in architecture:** Container layer — wraps the entire API layer.

---

### Docker Compose
**What it is:** A tool for running multi-container Docker applications.
**What it does in this project:** Spins up two containers with a single command: the FastAPI API container and the MLflow UI container. Manages port mappings, volume mounts, and restart policies.
**Why chosen:** For development and single-server deployment, Docker Compose is the simplest way to manage multiple containers. For ECS and Kubernetes, the individual Dockerfile is used instead.
**Where in architecture:** Container layer — orchestration for local development and EC2 deployment.

---

### GitHub Actions
**What it is:** A CI/CD platform built into GitHub.
**What it does in this project:** On every git push, automatically runs: tests, Docker build, Docker push to Docker Hub, and deployment to AWS EC2 or ECS.
**Why chosen over alternatives:** GitHub Actions is free for public repos, requires no separate CI server, and integrates directly with the GitHub repository. Jenkins requires self-hosting. CircleCI and Travis CI have free tier limits.
**Where in architecture:** CI/CD layer — between git push and cloud deployment.

---

### AWS EC2
**What it is:** Amazon Elastic Compute Cloud — virtual machines in AWS.
**What it does in this project:** Hosts the Docker container running the FastAPI API. An EC2 instance is a Linux server (Ubuntu 22.04 LTS) that runs 24/7 and serves HTTP traffic.
**Why chosen:** EC2 gives complete control over the server. It is the simplest entry point to AWS for developers. t3.small (2 vCPU, 2GB RAM) is sufficient for this API's load.
**Where in architecture:** Cloud layer — physical compute for the API.

---

### AWS ECS Fargate
**What it is:** Amazon Elastic Container Service with Fargate launch type — serverless container execution.
**What it does in this project:** Runs the Docker container without managing any EC2 instances. AWS manages the underlying infrastructure. An Application Load Balancer (ALB) distributes traffic to Fargate tasks.
**Why chosen over EC2:** No server management. Scales automatically. Pay only for actual container runtime. No patching, no SSH keys, no instance sizing decisions.
**Where in architecture:** Cloud layer — alternative to EC2 for production deployment.

---

### Nginx
**What it is:** A high-performance HTTP server and reverse proxy.
**What it does in this project:** On EC2, Nginx sits in front of the FastAPI/Uvicorn server. It handles port 80/443, forwards requests to Uvicorn on port 8000, terminates SSL (HTTPS), and serves as a buffer against slow clients.
**Why chosen:** Uvicorn is an application server, not a web server — it should not be exposed directly to the internet. Nginx is the industry standard reverse proxy. It is faster than Apache for this use case and easier to configure.
**Where in architecture:** EC2 deployment only — between internet and FastAPI.

---

### Kubernetes
**What it is:** An open-source container orchestration system.
**What it does in this project:** (To be deployed) Will run the API as a `Deployment` with multiple replicas across multiple nodes. A `Service` exposes it internally. An `Ingress` (with Nginx Ingress Controller) exposes it externally with routing and TLS.
**Why chosen:** Kubernetes is the industry standard for large-scale container orchestration. It provides auto-scaling, self-healing (restarts failed pods), rolling deployments (zero downtime updates), and resource management.
**Where in architecture:** Cloud layer — alternative to EC2 and ECS for enterprise-grade deployment.

---

## 5. All Problems Encountered

### Problem 1 — Google Colab: Could Not Upload Folders with Subfolders
**Error:** Google Colab's file upload UI only accepts individual files, not folder hierarchies.
**Why it happened:** Colab's browser-based uploader is a simple file picker — it does not recurse into subdirectories.
**How it was fixed:** The entire project folder was compressed into a ZIP file using Windows Explorer right-click → "Compress to ZIP". The ZIP was uploaded to Colab and extracted with `!unzip project.zip`.
**Prevention:** Always ZIP project folders before uploading to Colab. Alternatively use `from google.colab import drive; drive.mount('/content/drive')` and upload to Google Drive first.

---

### Problem 2 — Colab ZIP Extracted into `/content/` Instead of a Subfolder
**Error:** After `!unzip project.zip`, all files appeared directly in `/content/` instead of `/content/project_name/`.
**Why it happened:** The ZIP was created from inside the project folder, so paths inside the ZIP were relative (e.g., `src/`, `data/`) rather than absolute (e.g., `project/src/`, `project/data/`).
**How it was fixed:** Treated `/content/` as the project root. All `os.path` references were updated to use `/content/` as base. Alternatively: `!unzip project.zip -d /content/project_name/`.
**Prevention:** When creating the ZIP, right-click the parent folder (not inside it) so the ZIP contains a top-level folder.

---

### Problem 3 — requirements.txt Caused Dependency Conflicts in Colab
**Error:** `pip install -r requirements.txt` failed with version conflict errors, particularly between PyCaret and scikit-learn versions.
**Why it happened:** Google Colab pre-installs specific versions of numpy, scikit-learn, and other libraries. `requirements.txt` specified pinned versions that conflicted with Colab's pre-installed packages.
**How it was fixed:** Installed packages individually in a specific order, skipping ones already available:
```bash
pip install mlflow fastapi uvicorn pycaret joblib python-dotenv openpyxl
```
**Prevention:** Use `>=` version constraints in requirements.txt rather than `==` pinned versions. Add `--quiet` flag to suppress Colab's verbose dependency warnings.

---

### Problem 4 — ngrok Required Account Signup
**Error:** Running `ngrok http 8000` in Colab prompted for authentication token — free anonymous tunnels no longer available.
**Why it happened:** ngrok changed its policy and now requires a free account to use any tunnel.
**How it was fixed:** Used `localtunnel` instead:
```bash
npm install -g localtunnel
lt --port 8000
```
localtunnel provides a public URL without account registration.
**Prevention:** Use localtunnel or Cloudflare Tunnel for quick demos. For production, always use proper cloud deployment (EC2, ECS) rather than tunnels.

---

### Problem 5 — Disk Space Ran Out During pip Install
**Error:** `pip install` failed mid-way with `OSError: [Errno 28] No space left on device`. Only 130MB free on system disk.
**Why it happened:** Multiple large installer files (duplicate Anaconda, Tableau, VMware installers) had accumulated in the Downloads folder, each 500MB-3GB in size.
**How it was fixed:** Located and deleted duplicate large files in Windows Explorer from `C:\Users\admin\Downloads`. Freed up ~8GB. Recreated `.venv` and ran pip install again.
**Prevention:** Regularly audit the Downloads folder. Use `Get-ChildItem -Path $env:USERPROFILE\Downloads | Sort-Object Length -Descending | Select-Object -First 20` in PowerShell to find large files.

---

### Problem 6 — .venv Got Corrupted Twice
**Error:** After partial pip installs (due to disk space errors), activating `.venv` produced import errors and missing module errors.
**Why it happened:** pip installs were interrupted mid-package, leaving the venv in an inconsistent state — some packages partially installed.
**How it was fixed:** Completely deleted the venv and recreated it:
```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```
**Prevention:** Ensure sufficient disk space (at least 3GB free) before running pip install. Never interrupt a pip install — if it fails, delete and recreate the venv rather than retrying on a broken state.

---

### Problem 7 — MLflow `file://` Path Not Supported on Windows
**Error:** `mlflow.set_tracking_uri("file://C:/Users/admin/...")` raised a `MlflowException` because Windows absolute paths with drive letters are not valid POSIX URIs.
**Why it happened:** MLflow's URI parsing is POSIX-centric. `file://C:/path` is not a valid RFC 3986 URI on Windows (valid form would need `file:///C:/path` with three slashes, but MLflow's path-joining code doesn't handle Windows drive letters correctly).
**How it was fixed:** Switched to SQLite backend:
```python
mlflow.set_tracking_uri("sqlite:///mlflow.db")
```
This stores tracking data in a local `mlflow.db` SQLite file, which works identically on Windows and Linux.
**Prevention:** Always use SQLite backend for local Windows development. Use a proper MLflow tracking server (or `file:///` triple-slash) for Linux production deployments.

---

### Problem 8 — Wrong Git Command Used
**Error:** Accidentally typed `git add origin https://...` instead of `git remote add origin https://...`.
**Why it happened:** Typo in a command typed from memory.
**How it was fixed:** Ran the correct command immediately.
**Prevention:** Copy-paste git remote URLs from GitHub's repository page rather than typing from memory.

---

### Problem 9 — pyenv Not Set (Python Version Not Active)
**Error:** `python --version` showed system Python 3.8 instead of pyenv-managed 3.10.11 even after installing it.
**Why it happened:** pyenv's shim was not in PATH, or `pyenv global` was not run after installation.
**How it was fixed:**
```powershell
pyenv global 3.10.11
```
Then reopened the terminal to refresh PATH.
**Prevention:** After installing pyenv-win, restart the terminal before running `pyenv global`. Verify with `pyenv version` before creating any venv.

---

## 6. Key Decisions Made

### Decision 1 — Gradient Boosting as Production Model (not Random Forest or Extra Trees)
**Context:** Random Forest (R²=0.780), Extra Trees (R²=0.791), and Gradient Boosting (R²=0.795) all performed similarly.
**Decision:** Selected Gradient Boosting.
**Reasoning:**
- Highest test R² (0.795) on held-out test set
- Lowest MAE (8.64 Lakhs) — most important metric for real estate buyers who care about absolute price error
- Sequential boosting gives GBM a systematic error-reduction advantage over Random Forest's parallel bagging
- PyCaret's AutoML experiment independently confirmed gradient boosting variants as top performers
- With 200 training samples, GBM's bias-variance profile (moderate bias, low variance) is better suited than deep random forests

---

### Decision 2 — FastAPI Over Flask as Primary API
**Context:** Both FastAPI (`src/api/fastapi_app.py`) and Flask (`src/api/flask_app.py`) were implemented.
**Decision:** FastAPI is the primary serving layer; Flask is kept as a fallback.
**Reasoning:**
- FastAPI auto-validates requests via Pydantic — no manual `if "area_sqft" not in request.json` code
- FastAPI auto-generates `/docs` (Swagger UI) — clients can explore and test without Postman
- FastAPI is ASGI-based and 2-3x faster under concurrent load
- FastAPI handles type hints natively, making the codebase self-documenting
- FastAPI is the industry standard for new ML APIs in 2024-2026

---

### Decision 3 — SQLite Backend for MLflow on Windows
**Context:** MLflow supports file://, SQLite, PostgreSQL, and MySQL backends.
**Decision:** SQLite (`sqlite:///mlflow.db`).
**Reasoning:**
- File:// URI scheme has Windows path compatibility issues (see Problem 7)
- SQLite requires zero infrastructure — just a local file
- For a solo developer with 5 model runs, SQLite's single-file storage is sufficient
- PostgreSQL/MySQL overkill for this scale and adds dependency complexity
- SQLite can be replaced with RDS PostgreSQL when scaling to production team use

---

### Decision 4 — Label Encoding Over One-Hot Encoding for Categorical Features
**Context:** Four categorical columns (location, sub_area, property_type, company_name) needed encoding.
**Decision:** Label encoding (integer mapping) rather than one-hot encoding (binary columns).
**Reasoning:**
- The best models (GBM, Extra Trees, Random Forest) are all tree-based and handle integer-encoded categoricals natively
- One-hot encoding would expand 4 columns into potentially 50+ binary columns, which causes the curse of dimensionality on a 200-row dataset
- With 200 rows, adding 50+ dummy columns would likely lead to overfitting in linear models and unnecessary computation in tree models

---

### Decision 5 — localtunnel Over ngrok for Colab Demos
**Context:** Needed to expose the FastAPI server running in Google Colab to the public internet for demonstration.
**Decision:** localtunnel.
**Reasoning:**
- ngrok now requires account registration and auth token for any usage
- localtunnel requires only `npm install -g localtunnel && lt --port 8000`
- For short-lived demo tunnels (1-2 hours), localtunnel is sufficient
- For production, neither tool is used — real cloud deployment (EC2/ECS) is used instead

---

### Decision 6 — Scikit-learn Pipeline as Serving Object
**Context:** The model could be saved as a raw estimator (just the GBM) or as a Pipeline (imputer + scaler + GBM).
**Decision:** Save the complete Pipeline.
**Reasoning:**
- Prevents training-serving skew: the same StandardScaler fitted on training data is always applied at inference
- If only the raw GBM were saved, the API would need to re-implement the imputation and scaling steps — any deviation would produce wrong predictions
- Single `pipeline.predict(df)` call handles all preprocessing automatically
- Industry best practice for scikit-learn production deployment

---

## 7. Model Performance Summary

| Model | Test R² | Test MAE (Lakhs) | Test RMSE (Lakhs) | CV R² (5-fold) | Status |
|---|---|---|---|---|---|
| Ridge Regression | 0.742 | 14.39 | 19.84 | 0.718 | Baseline |
| Lasso Regression | 0.765 | 12.72 | 18.21 | 0.739 | Improved |
| Random Forest | 0.780 | 8.77 | 17.43 | 0.763 | Good |
| Extra Trees | 0.791 | 9.38 | 16.89 | 0.771 | Better |
| **Gradient Boosting** | **0.795** | **8.64** | **16.52** | **0.779** | **WINNER** |

**Key Insights:**
- GBM has the highest R² AND lowest MAE — it is unambiguously the best model
- The gap between Ridge (0.742) and GBM (0.795) is meaningful: GBM explains 5.3% more variance
- MAE improvement from Ridge (14.39L) to GBM (8.64L) = 5.75 Lakhs better accuracy per prediction
- All tree models (RF, ET, GBM) dramatically outperform linear models (Ridge, Lasso) — strong evidence of non-linear relationships in the data
- CV R² is consistently below test R², suggesting mild overfitting due to the small dataset (200 rows)

**Business Interpretation:**
On average, the GBM model's predictions are within **8.64 Lakhs** (~8.64 × 100,000 INR ≈ $10,400 USD) of actual prices. For properties in the 50-200 Lakh range, this is a 4-17% error rate — acceptable for an initial ML-based estimate.

---

## 8. Lessons Learned

### Technical Lessons

**1. Always embed preprocessing inside the sklearn Pipeline**
Saving just the model weights is not enough. Save the entire pipeline (imputer + scaler + model) so the transformation state is preserved. A StandardScaler fitted on training data must be the one applied at inference — not a fresh unfitted one.

**2. SQLite is the right MLflow backend for Windows**
The `file://` URI scheme does not work reliably on Windows. SQLite is a one-line fix that works identically on Windows and Linux. Switch to PostgreSQL when you need a shared tracking server for teams.

**3. Label encoding is correct for tree models**
Do not reflexively apply one-hot encoding to all categoricals. Tree-based models split on feature values numerically — they handle label-encoded integers fine. OHE creates unnecessary feature explosion on small datasets.

**4. Docker layer caching is critical for fast builds**
Put `COPY requirements.txt .` and `RUN pip install` before `COPY . .`. This ensures pip install is cached and only reruns when requirements.txt changes, not on every code change. On a 100-package requirements file, this saves 5-10 minutes per build.

**5. Validate inputs at the API boundary only**
Don't validate inside the prediction function — validate at the FastAPI layer with Pydantic. The model pipeline itself handles NaN values (SimpleImputer). Only user-facing inputs need explicit validation.

**6. DVC pipeline stages force reproducibility**
By defining `dvc.yaml` stages with explicit deps and outs, any team member can run `dvc repro` and get the exact same processed data and model. Without DVC, the pipeline is a collection of scripts that may or may not be run in the right order.

### Process Lessons

**7. Disk space must be checked before major installs**
Heavy ML libraries (scikit-learn, PyCaret, mlflow) consume 2-3GB. Always check available disk space before running `pip install -r requirements.txt`.

**8. Virtual environments must be created fresh after interruption**
A partially installed venv is unusable. Do not try to resume a broken venv — delete it and start fresh. It takes less time than debugging a corrupted installation.

**9. pyenv requires a new terminal session after installation**
Environment changes (PATH updates) from pyenv installation require a new terminal window. Never assume pyenv is active in the same terminal where you installed it.

**10. ZIP from parent directory, not from inside the folder**
When creating a ZIP to upload to Colab or share, right-click the project folder's parent and compress it — so the ZIP contains `/project/` rather than extracting files directly to the target directory.

**11. Tunnels (ngrok, localtunnel) are for demos only**
Never use a tunnel for production traffic. They are unstable, slow, and have bandwidth limits. For anything beyond a 5-minute demo, deploy to a real cloud environment.

**12. Git remote commands are typed differently from git add**
`git remote add origin <url>` is the command to link a local repository to GitHub. `git add` stages files. These are completely different commands. Use GitHub's "Quick Setup" page for copy-paste accuracy.
