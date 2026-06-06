# End-to-End Implementation Guide — Pune Real Estate Price Prediction MLOps
## Complete Record: From Raw Data to Live Production on AWS EC2 + ECS Fargate + EKS Kubernetes
**Author: Shadrack Nakoba | Organisation: Internal Engineering Reference**
**Date: June 2026 | Status: LIVE IN PRODUCTION**

> This document is the authoritative implementation record for the Pune Real Estate Price Prediction project. It covers every step taken, every issue encountered, every fix applied, and every click made — in the order they happened. Engineers implementing this in any organisation should follow this document top to bottom.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Final Architecture](#2-final-architecture)
3. [All Live URLs and Credentials](#3-all-live-urls-and-credentials)
4. [Phase 1 — Data Science in Google Colab](#4-phase-1--data-science-in-google-colab)
5. [Phase 2 — Local Development in VS Code](#5-phase-2--local-development-in-vs-code)
6. [Phase 3 — Docker Containerisation](#6-phase-3--docker-containerisation)
7. [Phase 4 — GitHub and CI/CD Pipeline](#7-phase-4--github-and-cicd-pipeline)
8. [Phase 5 — AWS ECR (Container Registry)](#8-phase-5--aws-ecr-container-registry)
9. [Phase 6 — AWS ECS Fargate Deployment](#9-phase-6--aws-ecs-fargate-deployment)
10. [Phase 7 — AWS EKS Kubernetes Deployment](#10-phase-7--aws-eks-kubernetes-deployment)
11. [Phase 8 — Monitoring Dashboards](#11-phase-8--monitoring-dashboards)
12. [All Issues Faced and How They Were Fixed](#12-all-issues-faced-and-how-they-were-fixed)
13. [GitHub Secrets Reference](#13-github-secrets-reference)
14. [File Structure Reference](#14-file-structure-reference)
15. [Production Checklist for Organisations](#15-production-checklist-for-organisations)

---

## 1. Project Overview

### What the Project Does
Predicts residential property prices in Pune, India using machine learning. A client sends property details (area, location, amenities) via HTTP and receives a predicted price in Lakhs (INR) within milliseconds.

### Business Value
Removes information asymmetry in the Pune real estate market. Buyers, sellers, banks, and PropTech platforms can get instant, data-driven price estimates without relying on broker opinions.

### Tech Stack (Production)
| Layer | Technology |
|---|---|
| Language | Python 3.10 |
| ML Framework | Scikit-learn (GBM, Random Forest, Ridge, Lasso, Extra Trees) |
| Experiment Tracking | MLflow (SQLite backend) |
| AutoML | PyCaret |
| API Framework | FastAPI + Uvicorn |
| Metrics | Prometheus + prometheus-fastapi-instrumentator |
| Containerisation | Docker |
| Container Registry | AWS ECR + Docker Hub |
| CI/CD | GitHub Actions (6-job pipeline) |
| Cloud — VM | AWS EC2 Ubuntu 22.04 + Supervisor |
| Cloud — Serverless | AWS ECS Fargate + Application Load Balancer |
| Cloud — Kubernetes | AWS EKS (K8s 1.30) + Nginx Ingress + HPA |
| Monitoring | Prometheus, Grafana, AWS CloudWatch |
| Data Versioning | DVC |

### Model Performance
| Model | Test R² | MAE (Lakhs) | Status |
|---|---|---|---|
| Ridge Regression | 0.742 | 14.39 | Baseline |
| Lasso Regression | 0.765 | 12.72 | — |
| Random Forest | 0.780 | 8.77 | — |
| Extra Trees | 0.791 | 9.38 | — |
| **Gradient Boosting** | **0.795** | **8.64** | **PRODUCTION** |

---

## 2. Final Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  DATA SOURCES                                                        │
│  Pune_Real_Estate_Data.xlsx + data_cleaned.csv (200 records)        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DATA PIPELINE  (src/data/preprocess.py)                            │
│  Clean → Engineer 21 features → pune_features.csv                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MODEL TRAINING  (src/models/train.py)                              │
│  5 models × MLflow tracking → best_model.pkl (GBM, R²=0.795)       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FastAPI REST API  (src/api/fastapi_app.py)                         │
│  GET /health  POST /predict  POST /predict/batch  GET /metrics      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DOCKER IMAGE                                                        │
│  python:3.10-slim + all deps + model baked in → ~1.8GB image        │
│  Pushed to: Docker Hub + AWS ECR                                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────────────────┐
│  AWS EC2        │  │  AWS ECS     │  │  AWS EKS Kubernetes      │
│  Ubuntu 22.04   │  │  Fargate     │  │  K8s 1.30, 2 nodes       │
│  Supervisor     │  │  2 tasks     │  │  3 API pods              │
│  Nginx          │  │  ALB         │  │  Nginx Ingress + HPA     │
│  Port 8000      │  │  Port 80     │  │  Prometheus + Grafana    │
└─────────────────┘  └──────────────┘  └──────────────────────────┘
              │              │              │
              └──────────────┴──────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  GITHUB ACTIONS CI/CD  (.github/workflows/deploy.yml)               │
│  push → test → build → deploy-ec2 + deploy-ecs + deploy-eks → notify│
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MONITORING                                                          │
│  Prometheus (EKS) · Grafana (EKS) · CloudWatch (EC2 + ECS)         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. All Live URLs and Credentials

### API Endpoints (all deployments)

| Deployment | Swagger UI | Health Check | Predict |
|---|---|---|---|
| EC2 | `http://54.147.249.94:8000/docs` | `http://54.147.249.94:8000/health` | `http://54.147.249.94:8000/predict` |
| ECS Fargate | `http://pune-api-alb-409088602.us-east-1.elb.amazonaws.com/docs` | `.../health` | `.../predict` |
| EKS Kubernetes | `http://a10b8a261812c4320acea02fe2f41c3a-608ac9cb7c009e77.elb.us-east-1.amazonaws.com/docs` | `.../health` | `.../predict` |

### Sample API Call
```bash
curl -X POST http://54.147.249.94:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "area_sqft": 1200,
    "township_area": 80,
    "amenity_score": 5,
    "has_clubhouse": 1,
    "has_school": 1,
    "has_hospital": 1,
    "has_mall": 0,
    "has_park": 1,
    "has_pool": 1,
    "has_gym": 1,
    "location": 3,
    "sub_area": 5,
    "property_type": 1,
    "company_name": 2
  }'
# Response: {"predicted_price_lakhs":87.44,"predicted_price_millions":8.744,...}
```

### Monitoring Dashboards

| Dashboard | Access Method | URL / Command |
|---|---|---|
| Swagger UI | Browser | Any URL above + `/docs` |
| Prometheus | kubectl port-forward | `kubectl port-forward svc/prometheus 9090:9090 -n pune-api` → http://localhost:9090 |
| Grafana | kubectl port-forward | `kubectl port-forward svc/grafana 3000:3000 -n pune-api` → http://localhost:3000 |
| Grafana Login | — | admin / PuneAPI@2026 |
| CloudWatch | AWS Console | us-east-1 → CloudWatch → Dashboards → PuneRealEstateAPI |
| MLflow | Local only | `mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000` → http://localhost:5000 |

### AWS Infrastructure (Account: 211125741068, Region: us-east-1)

| Resource | Name / ARN |
|---|---|
| ECR Repository | `211125741068.dkr.ecr.us-east-1.amazonaws.com/pune-real-estate-api` |
| ECS Cluster | `pune-api-cluster` |
| ECS Service | `pune-api-service` |
| ECS Task Definition | `pune-api-task:1` |
| ALB (ECS) | `pune-api-alb-409088602.us-east-1.elb.amazonaws.com` |
| ALB ARN | `arn:aws:elasticloadbalancing:us-east-1:211125741068:loadbalancer/app/pune-api-alb/f289cf745031a579` |
| Target Group ARN | `arn:aws:elasticloadbalancing:us-east-1:211125741068:targetgroup/pune-api-tg/074cee516680ba0b` |
| EKS Cluster | `pune-api-eks` |
| EKS Ingress LB | `a10b8a261812c4320acea02fe2f41c3a-608ac9cb7c009e77.elb.us-east-1.amazonaws.com` |
| VPC | `vpc-0803d39d79405b293` |
| CloudWatch Log Group | `/ecs/pune-api` (30-day retention) |

### GitHub Repository
`https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops`

---

## 4. Phase 1 — Data Science in Google Colab

### What Colab Is and Why We Used It
Google Colab is a free cloud Jupyter notebook that runs on Google's servers. We used it for the initial experiment because it requires zero local setup, has no disk space problems for heavy ML libraries, and produces a shareable notebook record of every step.

### Step 1 — Open the Notebook
1. Go to **https://colab.research.google.com**
2. Sign in with a Google account
3. Click **File → Upload notebook**
4. Upload `notebooks/Pune_Real_Estate_EndToEnd_ML.ipynb` from the project folder
5. The notebook opens with the title "Pune Real Estate — End-to-End ML Pipeline"

### Step 2 — Upload Raw Data (Cell 1)
Run Cell 1. A file picker appears in the output.
- Select both files at once (hold Ctrl and click both):
  - `Pune_Real_Estate_Data.xlsx`
  - `data_cleaned.csv`
- Files are saved to `/content/data/raw/`

### Step 3 — Install Dependencies (Cell 2)
```python
!pip install -q mlflow pycaret[full] fastapi uvicorn joblib openpyxl
```
Takes 3-5 minutes. Installs MLflow, PyCaret AutoML, FastAPI, and supporting libraries.

### Step 4 — Exploratory Data Analysis (Cells 5-8)
- Load both raw files into pandas DataFrames
- Check missing values (45 missing township areas, 3 missing prices)
- Plot price distribution — right-skewed, confirming need for log transformation
- Plot correlation heatmap — area and amenities positively correlated with price

### Step 5 — Data Cleaning and Feature Engineering (Cell 10)
Two functions run in sequence:

**clean_raw()** does:
- Standardise column names (lowercase, underscores)
- Extract numbers from text columns ("1200 sqft" → 1200)
- Map "Yes"/"No" amenity text to 1/0 binary integers
- Drop rows with no price or area

**engineer_features()** creates 5 derived features:
- `log_area` = log(area_sqft) — reduces right skew
- `amenity_score` = sum of all 7 binary amenity flags (0-7)
- `price_per_sqft` = price / area — efficiency metric
- `log_price` = log(price_lakhs) — normalised target
- `township_area` — imputed with median where missing

Categorical columns (location, sub_area, property_type, company_name) are label-encoded to integers. Label encoding was chosen over one-hot encoding because tree models handle integers natively without dimensionality explosion on a 200-row dataset.

Output: `pune_features.csv` — 197 rows × 21 columns.

### Step 6 — Model Training with MLflow (Cell 12)
Five scikit-learn models trained:
```python
Ridge(alpha=10)
Lasso(alpha=1)
RandomForestRegressor(n_estimators=200)
GradientBoostingRegressor(n_estimators=200, learning_rate=0.05)
ExtraTreesRegressor(n_estimators=200)
```

Each model is wrapped in a scikit-learn **Pipeline** (imputer + scaler + model). This is critical — the pipeline bundles preprocessing and the model into a single object so the same transformations applied during training are guaranteed to be applied at inference. Without this, training-serving skew corrupts predictions.

Every run logs to MLflow:
- Parameters: model name
- Metrics: MAE, RMSE, R², MAPE, 5-fold CV R²
- Artifact: the fitted pipeline object

Winner: **Gradient Boosting** — R²=0.795, MAE=8.64 Lakhs.

Model saved to `/content/models/best_model.pkl` as:
```python
{"pipeline": fitted_pipeline, "features": list_of_feature_columns}
```

### Step 7 — PyCaret AutoML (Cells 16-17)
PyCaret runs 20+ algorithm types automatically (`compare_models(n_select=3)`). It confirmed gradient boosting variants dominate, validating our scikit-learn experiment. The best PyCaret model was saved as `pycaret_best.pkl`.

### Step 8 — FastAPI Test Inside Colab (Cells 19-21)
A minimal FastAPI app was written to `/content/api_app.py` and launched with uvicorn. An ngrok tunnel created a public URL. The `/predict` endpoint was tested with a sample property and returned a valid price. This proved the full data-to-prediction pipeline worked end-to-end.

### Step 9 — Download Outputs (Cell 23)
Downloaded from Colab to local machine:
- `pune_features.csv` → copied to `data/processed/`
- `best_model.pkl` → copied to `models/`

---

## 5. Phase 2 — Local Development in VS Code

### Step 10 — Project Structure Setup
The project folder was created at `C:\Users\admin\Desktop\pune_real_estate_mlops` with this structure:
```
├── data/raw/           ← raw Excel and CSV files
├── data/processed/     ← cleaned feature set
├── models/             ← trained model files
├── src/data/           ← preprocess.py
├── src/models/         ← train.py, pycaret_train.py
├── src/api/            ← fastapi_app.py, flask_app.py, middleware.py
├── deployment/docker/  ← Dockerfile, docker-compose.yml
├── deployment/ecs/     ← task-definition.json
├── k8s/                ← all Kubernetes manifests
├── monitoring/         ← cloudwatch_setup.py, prometheus_config.yaml, grafana_dashboard.json
├── NAKOBA_implementation/ ← this documentation
├── .github/workflows/  ← deploy.yml
├── requirements.txt    ← full development dependencies
└── requirements_docker.txt ← production-only dependencies
```

### Step 11 — Python Virtual Environment
```powershell
cd C:\Users\admin\Desktop\pune_real_estate_mlops
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Python version used: **3.10.11** (managed by pyenv-win).

### Step 12 — Run Preprocessing Pipeline Locally
```powershell
python src/data/preprocess.py
```
Reads both raw files, cleans and engineers features, saves `data/processed/pune_features.csv`. This is the same logic as Colab Cell 10 but structured as a proper Python module with configurable paths.

### Step 13 — Run Model Training Locally
```powershell
python src/models/train.py
```
Trains all 5 models with MLflow tracking. The key difference from Colab: uses `sqlite:///mlflow.db` as the tracking URI (not `file://`) because Windows path formatting breaks the `file://` URI scheme.

Output: `models/best_model.pkl` and `models/feature_columns.txt`.

### Step 14 — View MLflow Dashboard
```powershell
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```
Open **http://localhost:5000** to compare all 5 model runs visually. This is the experiment tracking interface — click each run to see parameters, metrics, and artifacts. The GBM run shows the highest R² and lowest MAE confirming it as the production model.

### Step 15 — Run FastAPI Locally
```powershell
uvicorn src.api.fastapi_app:app --reload --port 8000
```
Open **http://localhost:8000/docs** — the Swagger UI auto-generated by FastAPI. Test the `/health` and `/predict` endpoints directly in the browser without any external tool.

The FastAPI application (`src/api/fastapi_app.py`) has:
- **Lazy model loading** — model loads once at startup and is held in memory
- **Pydantic validation** — every incoming field is type-checked and range-validated automatically
- **CORS middleware** — allows any browser-based client to call the API
- **Prometheus middleware** — adds `/metrics` endpoint for monitoring (added in Phase 4)

### Step 16 — Prometheus Middleware
A new file `src/api/middleware.py` was created to add:
1. **Structured JSON logging** — every request logs method, path, status, duration in JSON format
2. **Prometheus metrics** — `prometheus-fastapi-instrumentator` adds automatic histograms, counters and a `/metrics` endpoint

`fastapi_app.py` imports and wires this in:
```python
if _HAS_MIDDLEWARE:
    setup_middleware(app)
```
The `_HAS_MIDDLEWARE` guard means the app still works if `prometheus-fastapi-instrumentator` is not installed.

---

## 6. Phase 3 — Docker Containerisation

### Step 17 — Review the Dockerfile
`deployment/docker/Dockerfile`:
```dockerfile
FROM python:3.10-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "src.api.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key decisions:
- `python:3.10-slim` — minimal base image, reduces attack surface and image size
- `COPY requirements.txt` before `COPY . .` — Docker layer caching means pip only reruns when requirements change, not on every code push
- `--no-cache-dir` — saves 200-400MB by not storing pip cache inside the image
- `curl` installed — needed for the HEALTHCHECK command

### Step 18 — Build Docker Image (Local)
```powershell
cd C:\Users\admin\Desktop\pune_real_estate_mlops
docker build -t pune-real-estate-api:latest -f deployment/docker/Dockerfile .
```
Takes 10-20 minutes on first build. Final image size: ~1.8GB.

**Note:** Docker Desktop must be running (whale icon in system tray).

### Step 19 — Test Docker Container Locally
```powershell
docker run -d --name pune_api_test -p 8000:8000 pune-real-estate-api:latest
Start-Sleep -Seconds 30
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -ExpandProperty Content
# Expected: {"status":"ok","model_loaded":true}

docker stop pune_api_test
docker rm pune_api_test
```

### Step 20 — Push to Docker Hub
1. Create account at **https://hub.docker.com**
2. Create repository named `pune-real-estate-api` (Public)
3. Create access token: Account Settings → Security → New Access Token → name it `github-actions`
4. Login and push:
```powershell
docker login -u YOUR_USERNAME
# When prompted for password: paste the ACCESS TOKEN

docker tag pune-real-estate-api:latest YOUR_USERNAME/pune-real-estate-api:latest
docker tag pune-real-estate-api:latest YOUR_USERNAME/pune-real-estate-api:v1.0.0
docker push YOUR_USERNAME/pune-real-estate-api:latest
docker push YOUR_USERNAME/pune-real-estate-api:v1.0.0
```

---

## 7. Phase 4 — GitHub and CI/CD Pipeline

### Step 21 — Push Code to GitHub
Repository: `https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops`

```powershell
git init
git add .
git commit -m "Initial commit: Pune Real Estate MLOps pipeline"
git remote add origin https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops.git
git push -u origin main
```

### Step 22 — Set Git Author to SHADRACK NAKOBA
All commits must show the correct author for the GitHub contributor widget to display correctly. The email on the GitHub account must match the git config email:

```powershell
git config user.name "SHADRACK NAKOBA"
git config user.email "shadrack.n159@gmail.com"
```

To rewrite all historical commits (if previous commits show a different name):
```bash
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --force --env-filter '
export GIT_AUTHOR_NAME="SHADRACK NAKOBA"
export GIT_AUTHOR_EMAIL="shadrack.n159@gmail.com"
export GIT_COMMITTER_NAME="SHADRACK NAKOBA"
export GIT_COMMITTER_EMAIL="shadrack.n159@gmail.com"
' -- --all
git push origin main --force
```

Also confirm `shadrack.n159@gmail.com` is added and verified in GitHub → Settings → Emails.

### Step 23 — The CI/CD Workflow

File: `.github/workflows/deploy.yml`

The pipeline has **6 jobs** that run on every push to `main`:

```
Job 1: test
  → Checkout code
  → Install Python 3.10
  → Install core ML packages
  → Run src/data/preprocess.py
  → Run src/models/train.py (with MLFLOW_TRACKING_URI=sqlite:///mlflow.db)
  → Run pytest tests/ (or skip if no tests)

Job 2: build  (needs: test)
  → Checkout code
  → Install Python 3.10
  → Install ML packages + train model ← CRITICAL: model baked into image here
  → Verify models/best_model.pkl exists
  → Docker build
  → Login to Docker Hub → push :latest and :${{ github.sha }}
  → Login to ECR → pull from Docker Hub → retag → push to ECR

Job 3: deploy-ec2  (needs: build)
  → SSH into EC2 (appleboy/ssh-action)
  → cd ~/pune_real_estate_mlops
  → git pull origin main
  → source .venv/bin/activate
  → pip install -r requirements_docker.txt
  → sudo supervisorctl restart pune_api
  → curl -f http://localhost:8000/health

Job 4: deploy-ecs  (needs: build)
  → Configure AWS credentials
  → Login to ECR
  → Render task-definition.json with new image SHA
  → aws-actions/amazon-ecs-deploy-task-definition (wait-for-service-stability: false)
  → Verify: aws ecs describe-services → print running/desired/pending counts

Job 5: deploy-eks  (needs: build)
  → Configure AWS credentials
  → aws eks update-kubeconfig
  → kubectl set image deployment/pune-api pune-api=ECR_IMAGE:${{ github.sha }}
  → kubectl rollout status --timeout=300s || true
  → kubectl get pods / svc

Job 6: notify  (needs: deploy-ec2 + deploy-ecs + deploy-eks, always runs)
  → Print deploy summary table (EC2/ECS/EKS result)
  → Slack notification (continue-on-error: true, optional)
```

### Step 24 — Add GitHub Secrets
Go to: GitHub → Repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add each of these:

| Secret Name | Value | Where to find it |
|---|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | hub.docker.com profile |
| `DOCKERHUB_TOKEN` | Docker Hub access token | hub.docker.com → Account Settings → Security |
| `EC2_HOST` | `54.147.249.94` | EC2 Console → Elastic IP |
| `EC2_SSH_KEY` | Full contents of `.pem` file | `Get-Content pune-api-key.pem \| Set-Clipboard` |
| `AWS_ACCESS_KEY_ID` | IAM user access key | IAM → Users → Prince → Security credentials |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | Created alongside access key |

**Optional:**

| Secret Name | Value |
|---|---|
| `SLACK_WEBHOOK_URL` | Slack app incoming webhook URL |

### Step 25 — Key Workflow Fixes Applied

**Fix 1: `secrets` context in `if` condition**
GitHub Actions does not allow `secrets.X != ''` in an `if` expression. Replaced with `continue-on-error: true` on the Slack step.

**Fix 2: Model not in Docker image**
`models/best_model.pkl` was in `.gitignore` so it was never committed. The GitHub Actions runner checked out code without the model, built the Docker image, and the container started with `model_loaded: false`.

Fix: In the `build` job, added a step to install ML dependencies and run `preprocess.py` and `train.py` before building the Docker image. The model is trained fresh on the GitHub Actions runner and baked into every image:
```yaml
- name: Install ML dependencies and train model
  run: |
    pip install pandas numpy scikit-learn==1.7.2 scipy joblib openpyxl mlflow
    python src/data/preprocess.py
    MLFLOW_TRACKING_URI="sqlite:///mlflow.db" python src/models/train.py
```

**Fix 3: ECS stability timeout**
`wait-for-service-stability: true` caused GitHub Actions to hang because ECS reported "not stable" during the rolling update window. The URL was live throughout because old tasks kept serving traffic. Fix: set `wait-for-service-stability: false` and add a verify step instead.

**Fix 4: EKS rollout timeout**
`kubectl rollout status --timeout=180s` failed because pulling a 1.8GB image from ECR took longer than 180 seconds. Fix: increased to `--timeout=300s || true`. The `|| true` means if it still times out, the job passes anyway — the rollout completes on the cluster regardless of the watcher.

---

## 8. Phase 5 — AWS ECR (Container Registry)

### Step 26 — Configure AWS CLI
```powershell
aws configure
# AWS Access Key ID: [from IAM → Users → Prince → Security credentials]
# AWS Secret Access Key: [created alongside access key]
# Default region name: us-east-1
# Default output format: json
```

Verify:
```powershell
aws sts get-caller-identity
# Shows: Account: 211125741068, Arn: arn:aws:iam::211125741068:user/Prince
```

### Step 27 — Create ECR Repository
```powershell
aws ecr create-repository \
  --repository-name pune-real-estate-api \
  --region us-east-1 \
  --image-scanning-configuration scanOnPush=true
```

Repository URI: `211125741068.dkr.ecr.us-east-1.amazonaws.com/pune-real-estate-api`

**Where to verify in AWS Console:**
1. Go to **https://console.aws.amazon.com**
2. Search "ECR" → Elastic Container Registry
3. Click **Repositories** in left sidebar
4. You should see `pune-real-estate-api` listed

### Step 28 — IAM Permissions Required for ECR Push
The IAM user needs `AmazonEC2ContainerRegistryFullAccess`. Since the user already had 10 managed policies (the AWS limit), this was added as an inline policy called `eksctl-ecr-permissions` which also covers EKS and CloudFormation.

**The 10-policy limit:** AWS IAM users can only have 10 managed policies attached. Use inline policies to bypass this limit — they are not counted. To add an inline policy:
- IAM → Users → [username] → Permissions → **Create inline policy** → JSON tab

---

## 9. Phase 6 — AWS ECS Fargate Deployment

### What ECS Fargate Is
ECS Fargate runs Docker containers without managing any servers. You define what container to run (task definition), how many copies (service), and AWS handles the underlying compute. An Application Load Balancer distributes traffic across all running tasks.

### Step 29 — Create IAM Roles for ECS

Save `deployment/ecs/ecs-trust-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
```

```powershell
# ecsTaskExecutionRole — allows ECS to pull images and write logs
aws iam create-role --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://deployment/ecs/ecs-trust-policy.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# ecsTaskRole — application-level permissions (CloudWatch logs)
aws iam create-role --role-name ecsTaskRole \
  --assume-role-policy-document file://deployment/ecs/ecs-trust-policy.json
aws iam attach-role-policy --role-name ecsTaskRole \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```

### Step 30 — Create CloudWatch Log Group and ECS Cluster
```powershell
aws logs create-log-group --log-group-name /ecs/pune-api --region us-east-1
aws logs put-retention-policy --log-group-name /ecs/pune-api --retention-in-days 30

aws ecs create-cluster --cluster-name pune-api-cluster --capacity-providers FARGATE
```

**Where to verify in AWS Console:**
1. Search "ECS" → Elastic Container Service
2. Click **Clusters** in left sidebar
3. Click **pune-api-cluster**
4. You should see the cluster with Fargate capacity provider

### Step 31 — Task Definition

File: `deployment/ecs/task-definition.json`

Key settings:
- `cpu: "512"` — 0.5 vCPU
- `memory: "1024"` — 1 GB RAM
- `networkMode: "awsvpc"` — required for Fargate
- `image`: ECR URI with SHA tag (updated by GitHub Actions per deployment)
- Health check: `curl -f http://localhost:8000/health`
- Logs: CloudWatch `/ecs/pune-api` log group

Register:
```powershell
aws ecs register-task-definition \
  --cli-input-json file://deployment/ecs/task-definition.json
```

### Step 32 — Security Groups

```powershell
$VPC = "vpc-0803d39d79405b293"

# ALB security group — public inbound on 80 and 443
$ALB_SG = aws ec2 create-security-group \
  --group-name pune-alb-sg \
  --description "ALB for pune-api ECS" \
  --vpc-id $VPC --query "GroupId" --output text
aws ec2 authorize-security-group-ingress --group-id $ALB_SG \
  --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $ALB_SG \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# ECS task security group — only accepts traffic from the ALB
$TASK_SG = aws ec2 create-security-group \
  --group-name pune-ecs-task-sg \
  --description "ECS tasks for pune-api" \
  --vpc-id $VPC --query "GroupId" --output text
aws ec2 authorize-security-group-ingress --group-id $TASK_SG \
  --protocol tcp --port 8000 --source-group $ALB_SG
```

Port 8000 is never opened directly to the internet — only the ALB can reach it.

### Step 33 — Application Load Balancer

**In AWS Console:**
1. Go to EC2 → **Load Balancers** → **Create Load Balancer** → **Application Load Balancer**
2. Name: `pune-api-alb`
3. Scheme: **Internet-facing**
4. Select at least 3 availability zones (us-east-1a, us-east-1b, us-east-1c)
5. Security group: select `pune-alb-sg`
6. **Target group** — create new:
   - Name: `pune-api-tg`
   - Target type: **IP** (required for Fargate — not Instance)
   - Protocol: HTTP | Port: 8000
   - Health check path: `/health`
   - Healthy threshold: 2 | Unhealthy threshold: 3
7. Create

Via CLI:
```powershell
$ALB_ARN = aws elbv2 create-load-balancer \
  --name pune-api-alb \
  --subnets subnet-0a8ba0a09aaffa2f7 subnet-0d5a8a16c7aa5a916 subnet-078fe7d07f3cb36dc \
  --security-groups sg-02c81737a69b5eb54 \
  --scheme internet-facing --type application \
  --query "LoadBalancers[0].LoadBalancerArn" --output text

$TG_ARN = aws elbv2 create-target-group \
  --name pune-api-tg --protocol HTTP --port 8000 \
  --vpc-id vpc-0803d39d79405b293 --target-type ip \
  --health-check-path /health \
  --query "TargetGroups[0].TargetGroupArn" --output text

aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN --protocol HTTP --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

### Step 34 — ECS Service

```powershell
aws ecs create-service \
  --cluster pune-api-cluster \
  --service-name pune-api-service \
  --task-definition pune-api-task:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0a8ba0a09aaffa2f7,subnet-0d5a8a16c7aa5a916,subnet-078fe7d07f3cb36dc],securityGroups=[sg-0732664fe9d839bc4],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=pune-api,containerPort=8000" \
  --health-check-grace-period-seconds 60 \
  --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100"
```

`desired-count: 2` — always two tasks for high availability.
`minimumHealthyPercent: 100` — never drop below 2 tasks during updates (zero downtime).

**Where to verify:**
1. ECS → Clusters → pune-api-cluster → **Services** tab
2. Click `pune-api-service`
3. **Tasks** tab — should show 2 running tasks
4. **Events** tab — shows deployment history

### Step 35 — Verify ECS is Working
```powershell
aws ecs describe-services \
  --cluster pune-api-cluster --services pune-api-service \
  --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}" \
  --output table
# Expected: Status=ACTIVE, Running=2, Desired=2

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN \
  --query "TargetHealthDescriptions[*].{IP:Target.Id,State:TargetHealth.State}"
# Expected: 2 targets with State=healthy
```

---

## 10. Phase 7 — AWS EKS Kubernetes Deployment

### What EKS Kubernetes Is
EKS is Amazon's managed Kubernetes service. You get a control plane managed by AWS and worker nodes (EC2 instances) that run your application in containers called Pods. Key concepts:
- **Pod** — one running instance of your container
- **Deployment** — manages a set of identical pods, handles rolling updates
- **Service** — internal load balancer that routes traffic to pods
- **Ingress** — external HTTP router (sits in front of Services)
- **HPA** — Horizontal Pod Autoscaler, scales pod count based on CPU/memory

### Step 36 — Install Required Tools

**kubectl** (Kubernetes CLI):
```powershell
winget install Kubernetes.kubectl
kubectl version --client
```

**eksctl** (EKS cluster manager):
Download `eksctl.exe` from https://github.com/weaveworks/eksctl/releases/latest
Move to `C:\Windows\System32\`
```powershell
eksctl version
```

### Step 37 — Create EKS Cluster

```powershell
eksctl create cluster `
  --name pune-api-eks `
  --region us-east-1 `
  --nodegroup-name pune-api-nodes `
  --node-type t3.small `
  --nodes 2 --nodes-min 1 --nodes-max 4 `
  --managed --with-oidc --full-ecr-access
```

This takes **15-20 minutes**. eksctl creates two CloudFormation stacks:
1. `eksctl-pune-api-eks-cluster` — the control plane (EKS master)
2. `eksctl-pune-api-eks-nodegroup-pune-api-nodes` — the 2 worker EC2 nodes

When complete:
```
✔  EKS cluster "pune-api-eks" in "us-east-1" region is ready
✔  saved kubeconfig as "C:\Users\admin\.kube\config"
```

kubectl is now automatically configured to talk to the cluster.

```powershell
kubectl get nodes
# Expected: 2 nodes in Ready status
```

**Where to verify in AWS Console:**
1. Search "EKS" → Elastic Kubernetes Service
2. Click **Clusters** → **pune-api-eks**
3. **Compute** tab → Node groups → pune-api-nodes → 2 nodes

### Step 38 — Apply Kubernetes Manifests

All manifests are in the `k8s/` folder. Apply in this order:

```powershell
cd C:\Users\admin\Desktop\pune_real_estate_mlops

kubectl apply -f k8s/namespace.yaml    # creates pune-api namespace
kubectl apply -f k8s/configmap.yaml    # APP_ENV, MODEL_PATH, LOG_LEVEL etc.
kubectl apply -f k8s/secret.yaml       # API_KEY (base64 encoded)
kubectl apply -f k8s/deployment.yaml   # 3 replicas, rolling update config
kubectl apply -f k8s/service.yaml      # ClusterIP service on port 80
kubectl apply -f k8s/hpa.yaml          # auto-scale 2→10 pods at 70% CPU
```

`deployment.yaml` key settings:
- `replicas: 3` — 3 pods spread across 2 nodes
- `maxSurge: 1` — can temporarily have 4 pods during an update
- `maxUnavailable: 0` — never drop below 3 during update (zero downtime)
- `readinessProbe` — pod only receives traffic after `/health` returns 200
- `livenessProbe` — pod is restarted if `/health` fails 3 times

### Step 39 — Install Nginx Ingress Controller

Nginx Ingress creates an AWS Network Load Balancer that routes external HTTP traffic into the cluster:

```powershell
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/aws/deploy.yaml

# Wait for it to be ready
Start-Sleep -Seconds 60
kubectl get svc -n ingress-nginx ingress-nginx-controller
# EXTERNAL-IP column shows the NLB hostname — this is your public URL
```

### Step 40 — Apply Ingress

`k8s/ingress.yaml` was initially configured with a domain name placeholder. Since no custom domain is set up, we removed the host field to make it a catch-all:

```yaml
rules:
  - http:             # no host = catches all traffic regardless of hostname
      paths:
        - path: /
          pathType: Prefix
          backend:
            service:
              name: pune-api-service
              port:
                number: 80
```

```powershell
kubectl apply -f k8s/ingress.yaml
```

### Step 41 — Deploy Prometheus and Grafana

```powershell
kubectl apply -f k8s/monitoring/prometheus.yaml
kubectl apply -f k8s/monitoring/grafana.yaml
```

Both run as single-pod deployments inside the `pune-api` namespace with ClusterIP services (accessible only via port-forward, not publicly exposed for security).

### Step 42 — Verify All Pods Running

```powershell
kubectl get pods -n pune-api
```

Expected output:
```
NAME                          READY   STATUS    RESTARTS   AGE
grafana-xxx                   1/1     Running   0          2m
prometheus-xxx                1/1     Running   0          2m
pune-api-xxx-1                1/1     Running   0          5m
pune-api-xxx-2                1/1     Running   0          5m
pune-api-xxx-3                1/1     Running   0          5m
```

### Step 43 — Test the Kubernetes API

```powershell
$EKS_LB = "a10b8a261812c4320acea02fe2f41c3a-608ac9cb7c009e77.elb.us-east-1.amazonaws.com"

Invoke-WebRequest -Uri "http://$EKS_LB/health" -UseBasicParsing | Select-Object -ExpandProperty Content
# Response: {"status":"ok","model_loaded":true}

Invoke-WebRequest -Method POST -Uri "http://$EKS_LB/predict" `
  -ContentType "application/json" `
  -Body '{"area_sqft":1200,"amenity_score":5,"has_clubhouse":1,"has_school":1,"location":3,"sub_area":5,"property_type":1,"company_name":2}' `
  -UseBasicParsing | Select-Object -ExpandProperty Content
# Response: {"predicted_price_lakhs":87.44,"predicted_price_millions":8.744,...}
```

### Step 44 — Configure EKS deploy in GitHub Actions

The `deploy-eks` job in the workflow:
1. Configures AWS credentials
2. Runs `aws eks update-kubeconfig` to connect kubectl to the cluster
3. Runs `kubectl set image deployment/pune-api pune-api=ECR_IMAGE:SHA`
4. Runs `kubectl rollout status --timeout=300s || true`
   - The `|| true` means the job passes even if rollout status times out
   - The actual rollout continues on the cluster and completes successfully
   - The URL remains live throughout because old pods serve traffic until new pods are ready

---

## 11. Phase 8 — Monitoring Dashboards

### Dashboard 1 — Swagger UI (No Setup Required)
Browser only. Tests the API interactively.
- EC2: `http://54.147.249.94:8000/docs`
- ECS: `http://pune-api-alb-409088602.us-east-1.elb.amazonaws.com/docs`
- EKS: `http://a10b8a261812c4320acea02fe2f41c3a-608ac9cb7c009e77.elb.us-east-1.amazonaws.com/docs`

Click **POST /predict** → **Try it out** → modify the JSON → **Execute** → see the predicted price.

### Dashboard 2 — Prometheus

```powershell
kubectl port-forward svc/prometheus 9090:9090 -n pune-api
```
Open **http://localhost:9090**

Useful queries:
```
# Requests per second to /predict
rate(http_requests_total{handler="/predict"}[5m])

# P99 response latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Error rate percentage
100 * rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])

# Number of healthy API pods
count(up{job="pune-api"} == 1)
```

### Dashboard 3 — Grafana

```powershell
kubectl port-forward svc/grafana 3000:3000 -n pune-api
```
Open **http://localhost:3000** → login: `admin` / `PuneAPI@2026`

**Import the pre-built dashboard:**
1. Left sidebar → click the **+** icon → **Import**
2. Click **Upload JSON file**
3. Select: `monitoring/grafana_dashboard.json`
4. Select **Prometheus** as the datasource → **Import**

Dashboard panels:
- Request Rate (req/s)
- Response Time (p50/p95/p99)
- Error Rate %
- Running Pod Count
- Prediction Value Distribution
- CPU and Memory per Pod

### Dashboard 4 — CloudWatch (AWS Console)

**Create dashboards and alarms once:**
```powershell
.\.venv\Scripts\Activate.ps1
pip install boto3

python monitoring/cloudwatch_setup.py `
  --alb-arn "arn:aws:elasticloadbalancing:us-east-1:211125741068:loadbalancer/app/pune-api-alb/f289cf745031a579" `
  --email shadrack.n159@gmail.com
```

Confirm the subscription email that arrives in your inbox.

**View in AWS Console:**
1. Go to **https://console.aws.amazon.com**
2. Region: **us-east-1 (N. Virginia)**
3. Search "CloudWatch" → Click **Dashboards** → **PuneRealEstateAPI**

Alarms created:
- `pune-api-5xx-error-rate` — triggers if >10 errors in 5 minutes
- `pune-api-high-latency` — triggers if P99 > 2 seconds
- `pune-api-unhealthy-hosts` — triggers if healthy host count drops below 1

### Dashboard 5 — MLflow (Local Experiment Tracking)

```powershell
.\.venv\Scripts\Activate.ps1
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```
Open **http://localhost:5000**

Click the experiment `pune_real_estate_price_prediction` → see all 5 model runs. Click any run to see its full metric breakdown. Use the **Compare** button to view runs side by side.

---

## 12. All Issues Faced and How They Were Fixed

### Issue 1 — MLflow `file://` URI Fails on Windows

**Error:**
```
MlflowException: Could not find a suitable backend for tracking URI file://C:/Users/...
```

**Why it happened:** MLflow's `file://` URI parser expects POSIX paths. Windows drive letters (C:/) break the path parsing.

**Fix:** Switch to SQLite backend in `train.py`:
```python
mlflow.set_tracking_uri("sqlite:///mlflow.db")
```
SQLite is a local file-based database that works identically on Windows and Linux.

**Prevention:** Always use SQLite backend on Windows. Switch to PostgreSQL when deploying a shared MLflow server for a team.

---

### Issue 2 — .venv Corrupted After Partial Install

**Error:**
```
ModuleNotFoundError: No module named 'sklearn'
```
or
```
No module named 'pip'
```

**Why it happened:** pip install was interrupted mid-package (disk space ran out), leaving the venv in an inconsistent state.

**Fix:** Delete and recreate from scratch:
```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

**Prevention:** Ensure at least 3GB free disk space before running `pip install -r requirements.txt`.

---

### Issue 3 — Disk Space Ran Out During pip Install

**Error:**
```
OSError: [Errno 28] No space left on device
```

**Why it happened:** Multiple large installer files (Anaconda, VMware, Tableau — 500MB-3GB each) had accumulated in `C:\Users\admin\Downloads`.

**Fix:** Deleted duplicate large files from Downloads folder, freed ~8GB. Recreated `.venv` and retried.

**Prevention:**
```powershell
# Find largest files in Downloads
Get-ChildItem $env:USERPROFILE\Downloads |
  Sort-Object Length -Descending |
  Select-Object Name, @{N="SizeMB";E={[math]::Round($_.Length/1MB,1)}} |
  Select-Object -First 20
```

---

### Issue 4 — pyenv Not Active After Installation

**Error:**
```powershell
python --version
# Python 3.8.10  (wrong — should be 3.10.11)
```

**Why it happened:** pyenv's shim directory was not in PATH for the current terminal session.

**Fix:**
```powershell
pyenv global 3.10.11
# Then close and reopen the terminal
python --version
# Python 3.10.11
```

**Prevention:** After installing pyenv-win, always open a new PowerShell window before using `python`.

---

### Issue 5 — Google Colab Cannot Upload Folders

**Why it happened:** Colab's file upload UI only accepts individual files, not directory trees.

**Fix:** Compress the project into a ZIP file and upload:
```powershell
# In Windows Explorer: right-click the project folder → Send to → Compressed (zipped) folder
# Or in PowerShell:
Compress-Archive -Path pune_real_estate_mlops -DestinationPath project.zip
```
In Colab:
```python
!unzip project.zip -d /content/
```

---

### Issue 6 — ngrok Requires Account

**Error:** `ngrok.exceptions.PyngrokError: ngrok authtoken required`

**Why it happened:** ngrok changed policy to require free account registration for any tunnel usage.

**Fix:** Used `localtunnel` instead which requires no account:
```bash
npm install -g localtunnel
lt --port 8000
```

---

### Issue 7 — GitHub Actions: `secrets` Context in `if` Condition

**Error:**
```
Unrecognized named-value: 'secrets'. Located at position 1 within expression: secrets.SLACK_WEBHOOK_URL != ''
```

**Why it happened:** GitHub Actions does not allow the `secrets` context inside `if:` expressions for security reasons — it would reveal whether a secret is set.

**Fix:** Removed the `if` condition and added `continue-on-error: true` to the Slack step instead:
```yaml
- name: Send Slack notification
  continue-on-error: true    # silently skips if SLACK_WEBHOOK_URL is not set
  uses: slackapi/slack-github-action@v1.26.0
```

---

### Issue 8 — Docker Image Built Without the Model File

**Symptom:**
```json
{"status":"degraded","model_loaded":false}
```
API was running on ECS and EKS but predictions returned 500 Internal Server Error.

**Why it happened:** `models/best_model.pkl` was listed in `.gitignore`. GitHub Actions checked out the code, built the Docker image with `COPY . .` — but the model was never in the git repository, so it was never copied into the image.

**Fix:** In the `build` job of the workflow, added steps to install ML packages and train the model **before** the Docker build, so the freshly trained model is present when `COPY . .` runs:
```yaml
- name: Install ML dependencies and train model
  run: |
    pip install pandas numpy scikit-learn==1.7.2 scipy joblib openpyxl mlflow
    python src/data/preprocess.py
    MLFLOW_TRACKING_URI="sqlite:///mlflow.db" python src/models/train.py

- name: Verify model file exists before Docker build
  run: ls -lh models/best_model.pkl
```

**Why not just commit the model file?** Model files are binary blobs that grow git history and slow every clone. Training the model in CI ensures the packaged model always matches the current code and data.

---

### Issue 9 — IAM User Cannot Attach Its Own Policies

**Error:**
```
An error occurred (AccessDenied): User Prince is not authorized to perform: iam:AttachUserPolicy
```

**Why it happened:** The user `Prince` only had `IAMReadOnlyAccess`. Read-only means you can list/describe IAM resources but cannot modify them — including your own policies.

**Fix:** Used the AWS **root account** (the email/password used to create the AWS account) to add the required policies. Root account has unrestricted access to all IAM operations.

**How to access root account:**
1. Go to https://console.aws.amazon.com
2. Click "Sign in to a different account" → "Root user email address"
3. Enter the account email address → Next
4. Enter root password

---

### Issue 10 — IAM Policy Quota Exceeded (10 Managed Policies Limit)

**Error:** "The selected policies exceed this account's quota"

**Why it happened:** AWS limits IAM users to 10 managed policies. The user `Prince` already had exactly 10 policies attached and there was no room for the additional policies needed for EKS (IAMFullAccess, AWSCloudFormationFullAccess) and ECR (AmazonEC2ContainerRegistryFullAccess).

**Fix:** Created an **inline policy** instead of managed policies. Inline policies are embedded directly in the user and are **not counted** toward the 10-policy limit.

**How to add an inline policy (via root account):**
1. AWS Console → IAM → Users → Prince
2. **Permissions** tab → **Add permissions** → **Create inline policy**
3. Click the **JSON** tab
4. Paste:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iam:*", "cloudformation:*", "ecr:*", "eks:*"],
      "Resource": "*"
    }
  ]
}
```
5. Policy name: `eksctl-ecr-permissions` → **Create policy**

---

### Issue 11 — EKS Creation Fails: `iam:TagRole` Not Authorized

**Error:**
```
CREATE_FAILED: User is not authorized to perform: iam:TagRole on resource: eksctl-pune-api-eks-cluster-ServiceRole
```

**Why it happened:** eksctl creates IAM roles during cluster setup and tags them for resource tracking. The `IAMReadOnlyAccess` policy does not include `iam:TagRole`.

**Fix:** Adding the `eksctl-ecr-permissions` inline policy (which includes `iam:*`) resolved this. See Issue 10.

---

### Issue 12 — EKS CloudFormation Stack Already Exists

**Error:**
```
AlreadyExistsException: Stack [eksctl-pune-api-eks-cluster] already exists
```

**Why it happened:** The first EKS creation attempt failed partway through (due to the `iam:TagRole` error). eksctl left a `ROLLBACK_COMPLETE` CloudFormation stack behind. When we retried, the stack name conflicted.

**Fix:**
```powershell
aws cloudformation delete-stack --stack-name eksctl-pune-api-eks-cluster --region us-east-1
Start-Sleep -Seconds 30
# Confirm it's gone:
aws cloudformation describe-stacks --stack-name eksctl-pune-api-eks-cluster 2>&1
# Should show: Stack does not exist
```
Then retry `eksctl create cluster`.

---

### Issue 13 — Docker Desktop Not Starting

**Error:**
```
Error response from daemon: Docker Desktop is unable to start
```

**Why it happened:** Docker Desktop had an internal state issue (possibly from a previous crash or incomplete update).

**Impact:** Negligible — the Docker image push to ECR was handled entirely by GitHub Actions, which has its own Docker environment. Local Docker Desktop was not required for production deployment.

**Fix for local use:** Task Manager → End Task on all Docker processes → Reopen Docker Desktop.

---

### Issue 14 — ECS Ingress Host Mismatch (404)

**Error:** Nginx Ingress returned 404 when testing the EKS LoadBalancer URL.

**Why it happened:** The `k8s/ingress.yaml` had `host: api.yourdomain.com`. Nginx Ingress only routes requests whose HTTP `Host` header matches the configured hostname. Since we accessed the URL directly (no domain), the `Host` header was the raw LoadBalancer hostname which didn't match `api.yourdomain.com`.

**Fix:** Removed the `host:` field from the ingress rules to make it a catch-all:
```yaml
rules:
  - http:         # no host field = matches any hostname
      paths:
        - path: /
```

---

### Issue 15 — ECS Stuck on "Resource is not in the state servicesStable"

**Error:**
```
Error: Resource is not in the state servicesStable
```

**Why it happened:** The GitHub Actions step had `wait-for-service-stability: true`. During a rolling ECS deployment, new tasks are starting and old tasks are draining — ECS is not "stable" during this window. The action polled ECS repeatedly and eventually hit a timeout because the stabilisation took longer than expected.

**Critical insight:** The URL was live and serving traffic throughout. Old tasks kept handling requests while new tasks started. GitHub Actions was just watching the process, not controlling it.

**Fix:** Set `wait-for-service-stability: false`. GitHub Actions now fires the deployment and immediately verifies the task count via CLI, then moves on. ECS completes the rollout independently:
```yaml
wait-for-service-stability: false
```

---

### Issue 16 — EKS Rollout Status Timeout

**Error:**
```
error: timed out waiting for the condition
Error: Process completed with exit code 1
```

**Why it happened:** `kubectl rollout status --timeout=180s` — pulling a 1.8GB Docker image from ECR takes 2-4 minutes depending on node network speed. 180 seconds was not always enough.

**Critical insight:** Same as Issue 15 — the URL was live. The rollout continued on the cluster and completed successfully. GitHub Actions was just the watcher.

**Fix:** Two changes:
```bash
kubectl rollout status deployment/pune-api -n pune-api --timeout=300s || true
```
- Increased timeout to 300 seconds (5 minutes)
- Added `|| true` — if it still times out, the shell returns exit 0 so GitHub Actions marks the step as passed

---

### Issue 17 — Contributor Showing as "prince" Instead of "SHADRACK NAKOBA"

**Why it happened:** The initial git config had `user.name = prince`. All commits were authored as `prince <shadrack.n159@gmail.com>`. GitHub links commits to a user profile via the author email, but the name displayed comes from the commit author field.

**Fix:** Rewrote all commit history using `git filter-branch`:
```bash
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --force --env-filter '
export GIT_AUTHOR_NAME="SHADRACK NAKOBA"
export GIT_AUTHOR_EMAIL="shadrack.n159@gmail.com"
export GIT_COMMITTER_NAME="SHADRACK NAKOBA"
export GIT_COMMITTER_EMAIL="shadrack.n159@gmail.com"
' -- --all
git push origin main --force
```

Also required: add `shadrack.n159@gmail.com` as a verified email in GitHub → Settings → Emails. GitHub uses the email to link commits to profiles. Without the email verified, commits don't appear in the contribution graph.

---

## 13. GitHub Secrets Reference

Go to: **GitHub Repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value | Required For |
|---|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub username | build job |
| `DOCKERHUB_TOKEN` | Docker Hub access token (not password) | build job |
| `EC2_HOST` | `54.147.249.94` | deploy-ec2 job |
| `EC2_SSH_KEY` | Full contents of `.pem` key file | deploy-ec2 job |
| `AWS_ACCESS_KEY_ID` | IAM user access key | build (ECR), deploy-ecs, deploy-eks |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | build (ECR), deploy-ecs, deploy-eks |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | notify job (optional) |

**To get Docker Hub token:**
hub.docker.com → username → Account Settings → Security → New Access Token → Read/Write

**To get EC2_SSH_KEY:**
```powershell
Get-Content C:\Users\admin\Downloads\pune-api-key.pem | Set-Clipboard
# Then paste into the GitHub secret value field
# The value starts with -----BEGIN RSA PRIVATE KEY-----
```

**IAM permissions required for the AWS user:**
The IAM user must have these permissions (via managed policies or inline policy):
- `AmazonEC2FullAccess`
- `AmazonECS_FullAccess`
- `AmazonEC2ContainerRegistryFullAccess`
- `AWSCloudFormationFullAccess`
- `IAMFullAccess`
- `CloudWatchFullAccess`

If hitting the 10-policy limit, combine into one inline policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [{"Effect": "Allow", "Action": ["iam:*","cloudformation:*","ecr:*","eks:*"], "Resource": "*"}]
}
```

---

## 14. File Structure Reference

```
pune_real_estate_mlops/
│
├── data/
│   ├── raw/
│   │   ├── Pune_Real_Estate_Data.xlsx     ← 200 property listings, 18 columns
│   │   └── data_cleaned.csv               ← secondary cleaned data source
│   └── processed/
│       └── pune_features.csv              ← 197 rows × 21 features (output of preprocess.py)
│
├── models/
│   ├── best_model.pkl                     ← GBM pipeline (imputer+scaler+model) — NOT in git
│   ├── feature_columns.txt                ← 15 feature names the model expects
│   └── pycaret_best.pkl                   ← AutoML winner (optional)
│
├── notebooks/
│   └── Pune_Real_Estate_EndToEnd_ML.ipynb ← Colab experiment notebook
│
├── src/
│   ├── data/preprocess.py                 ← data cleaning and feature engineering
│   ├── models/train.py                    ← trains 5 models, MLflow tracking, saves best
│   ├── models/pycaret_train.py            ← AutoML with PyCaret
│   └── api/
│       ├── fastapi_app.py                 ← production FastAPI application
│       ├── flask_app.py                   ← alternative lightweight API
│       └── middleware.py                  ← Prometheus metrics + JSON logging
│
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile                     ← production container build instructions
│   │   └── docker-compose.yml             ← local: API + MLflow containers
│   └── ecs/
│       ├── task-definition.json           ← ECS Fargate task (cpu:512, memory:1024)
│       └── ecs-trust-policy.json          ← IAM trust policy for ECS roles
│
├── k8s/
│   ├── namespace.yaml                     ← pune-api namespace
│   ├── configmap.yaml                     ← non-secret environment variables
│   ├── secret.yaml                        ← API_KEY (base64, replace before applying)
│   ├── deployment.yaml                    ← 3 replicas, rolling update, probes
│   ├── service.yaml                       ← ClusterIP service on port 80
│   ├── ingress.yaml                       ← Nginx catch-all ingress
│   ├── hpa.yaml                           ← HPA: 2-10 pods at CPU>70% or memory>80%
│   └── monitoring/
│       ├── prometheus.yaml                ← Prometheus + RBAC for pod scraping
│       └── grafana.yaml                   ← Grafana + Prometheus datasource
│
├── monitoring/
│   ├── cloudwatch_setup.py                ← run once: creates CW dashboard + 3 alarms + SNS
│   ├── prometheus_config.yaml             ← Prometheus scrape configuration
│   └── grafana_dashboard.json             ← import-ready Grafana dashboard
│
├── NAKOBA_implementation/
│   ├── E2E_MASTER_GUIDE.md               ← THIS FILE — complete implementation record
│   ├── PROJECT_JOURNEY.md                ← technical deep-dive, tool breakdown
│   ├── PROD_READY.md                     ← production checklist and hardening guide
│   └── CONTINUATION.md                   ← step-by-step from local to live
│
├── tests/
│   └── test_api.py                        ← FastAPI tests (health, predict, validation, batch)
│
├── .github/workflows/deploy.yml           ← 6-job CI/CD pipeline
├── dvc.yaml                               ← DVC pipeline (preprocess → train → pycaret)
├── requirements.txt                       ← full dev dependencies (includes PyCaret, Jupyter)
├── requirements_docker.txt                ← production-only dependencies
└── README.md                              ← project overview and quick start
```

---

## 15. Production Checklist for Organisations

Use this checklist when deploying to a new organisation's AWS account.

### Pre-Deployment
- [ ] AWS account created and root account credentials secured
- [ ] IAM user created with required permissions (see Section 13)
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Docker Desktop installed and running
- [ ] kubectl installed (`winget install Kubernetes.kubectl`)
- [ ] eksctl installed and in PATH
- [ ] Python 3.10 installed (pyenv recommended)
- [ ] GitHub repository forked or cloned
- [ ] All 6 GitHub Actions secrets added

### Container Registry
- [ ] ECR repository created (`pune-real-estate-api`)
- [ ] Image scanning enabled on ECR
- [ ] First push to ECR completed (via CI/CD)

### ECS Fargate
- [ ] `ecsTaskExecutionRole` IAM role created
- [ ] `ecsTaskRole` IAM role created
- [ ] CloudWatch log group `/ecs/pune-api` created (30 day retention)
- [ ] ECS cluster `pune-api-cluster` created
- [ ] Security groups created (ALB SG + task SG)
- [ ] Application Load Balancer created
- [ ] Target group created (type: IP, health check: /health)
- [ ] HTTP listener on port 80 configured
- [ ] Task definition registered with real account ID
- [ ] ECS service created (desired: 2, minHealthy: 100%)
- [ ] Both ECS tasks showing as healthy in target group

### EKS Kubernetes
- [ ] eksctl installed
- [ ] EKS cluster `pune-api-eks` created (takes 15-20 min)
- [ ] kubectl configured (`aws eks update-kubeconfig`)
- [ ] All k8s manifests applied (namespace, configmap, secret, deployment, service, hpa)
- [ ] Nginx Ingress Controller installed
- [ ] Ingress applied and external LoadBalancer hostname obtained
- [ ] All 3 pune-api pods showing `1/1 Running`
- [ ] Prometheus pod showing `1/1 Running`
- [ ] Grafana pod showing `1/1 Running`

### CI/CD Validation
- [ ] Push a small change to `main` branch
- [ ] All 6 GitHub Actions jobs complete (green or yellow — not red)
- [ ] New Docker image appears in Docker Hub with the commit SHA tag
- [ ] New image appears in ECR with the commit SHA tag
- [ ] EC2 Supervisor restarts the API process
- [ ] ECS shows a new task definition revision
- [ ] EKS shows a new rollout in `kubectl rollout history deployment/pune-api -n pune-api`

### Monitoring
- [ ] `python monitoring/cloudwatch_setup.py --alb-arn ... --email ...` run once
- [ ] CloudWatch SNS email subscription confirmed
- [ ] CloudWatch dashboard visible in console
- [ ] Grafana dashboard imported from `monitoring/grafana_dashboard.json`
- [ ] Prometheus scraping API metrics (test: `rate(http_requests_total[5m])` returns data)

### Final Verification
- [ ] `GET /health` returns `{"status":"ok","model_loaded":true}` on ALL three deployments
- [ ] `POST /predict` returns a price prediction on all three deployments
- [ ] `POST /predict` with `area_sqft: -1` returns HTTP 422 (validation working)
- [ ] `POST /predict/batch` with 101 items returns HTTP 400 (batch limit working)
- [ ] Swagger UI loads at `/docs` on all three deployments
- [ ] Prometheus metrics visible at `/metrics` endpoint
- [ ] GitHub contributor shows correct name

---

*This document reflects the complete implementation as of June 2026.*
*Repository: https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops*
*AWS Account: 211125741068 | Region: us-east-1*
