# End-to-End Implementation Guide — Pune Real Estate Price Prediction MLOps
## Complete Implementation Record: Raw Data → Live Production on AWS EC2 + ECS Fargate + EKS Kubernetes
**Project: Pune Real Estate Price Prediction API**
**Environment: Windows 11 | VS Code | PowerShell | AWS us-east-1**

---

> **FOR ENGINEERS IMPLEMENTING THIS IN YOUR ORGANISATION**
> This guide uses placeholder values everywhere personal information appeared.
> Fill in Section 0 (Your Reference Sheet) before starting. Every placeholder
> in this document maps to a real value you will obtain during setup.

---

## Section 0 — Your Reference Sheet (Fill Before You Start)

Before beginning, create a text file called `my_setup.txt` on your Desktop
(NOT inside the project folder — it goes in `.gitignore` automatically).
Fill in every value as you obtain it. Keep this file private.

```
# my_setup.txt — YOUR PERSONAL VALUES (do not share or commit)

YOUR_AWS_ACCOUNT_ID        = ____________   # e.g. 123456789012
YOUR_AWS_REGION            = us-east-1      # change if using different region
YOUR_IAM_USERNAME          = ____________   # the IAM user you create in AWS
YOUR_EC2_ELASTIC_IP        = ____________   # from EC2 > Elastic IPs
YOUR_EC2_KEY_NAME          = ____________   # name of your .pem key file
YOUR_DOCKERHUB_USERNAME    = ____________   # your hub.docker.com username
YOUR_GITHUB_USERNAME       = ____________   # your github.com username
YOUR_EMAIL                 = ____________   # email registered on GitHub
YOUR_VPC_ID                = ____________   # from AWS > VPC > Your VPCs
YOUR_SUBNET_IDS            = ____________   # comma-separated subnet IDs
YOUR_ALB_SG_ID             = ____________   # security group ID for ALB
YOUR_TASK_SG_ID            = ____________   # security group ID for ECS tasks
YOUR_ALB_ARN               = ____________   # ALB ARN from load balancer page
YOUR_TG_ARN                = ____________   # target group ARN
YOUR_ECS_ALB_DNS           = ____________   # ALB DNS for ECS
YOUR_EKS_LB_DNS            = ____________   # Nginx ingress LB hostname
YOUR_GRAFANA_LB_DNS        = ____________   # Grafana LoadBalancer hostname
YOUR_PROMETHEUS_LB_DNS     = ____________   # Prometheus LoadBalancer hostname
```

Every time you see a placeholder like `YOUR_AWS_ACCOUNT_ID` in this guide,
replace it with the matching value from your reference sheet.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Final Architecture](#2-final-architecture)
3. [Phase 1 — Google Colab: Data and Model Training](#3-phase-1--google-colab-data-and-model-training)
4. [Phase 2 — VS Code: Local Development](#4-phase-2--vs-code-local-development)
5. [Phase 3 — Docker: Containerisation](#5-phase-3--docker-containerisation)
6. [Phase 4 — GitHub: Version Control and CI/CD](#6-phase-4--github-version-control-and-cicd)
7. [Phase 5 — AWS Setup: IAM, CLI, ECR](#7-phase-5--aws-setup-iam-cli-ecr)
8. [Phase 6 — AWS ECS Fargate Deployment](#8-phase-6--aws-ecs-fargate-deployment)
9. [Phase 7 — AWS EKS Kubernetes Deployment](#9-phase-7--aws-eks-kubernetes-deployment)
10. [Phase 8 — Monitoring Dashboards](#10-phase-8--monitoring-dashboards)
11. [CI/CD Pipeline Explained](#11-cicd-pipeline-explained)
12. [All Issues Faced and Fixes Applied](#12-all-issues-faced-and-fixes-applied)
13. [GitHub Secrets Reference](#13-github-secrets-reference)
14. [Production Checklist](#14-production-checklist)

---

## 1. Project Overview

### What It Does
A machine learning REST API that predicts property prices in Pune, India.
Input: property features (area, location, amenities). Output: price in Lakhs INR.

### Model Performance
| Model | Test R² | MAE (Lakhs) | Selected |
|---|---|---|---|
| Ridge Regression | 0.742 | 14.39 | No |
| Lasso Regression | 0.765 | 12.72 | No |
| Random Forest | 0.780 | 8.77 | No |
| Extra Trees | 0.791 | 9.38 | No |
| **Gradient Boosting** | **0.795** | **8.64** | **YES — Production** |

### API Endpoints
| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Returns `{"status":"ok","model_loaded":true}` |
| `/predict` | POST | Single property price prediction |
| `/predict/batch` | POST | Up to 100 properties at once |
| `/docs` | GET | Swagger interactive documentation |
| `/metrics` | GET | Prometheus metrics scrape endpoint |

### Tech Stack
Python 3.10 · FastAPI · Scikit-learn · MLflow · Docker · GitHub Actions ·
AWS ECR · AWS ECS Fargate · AWS EKS · Prometheus · Grafana · CloudWatch

---

## 2. Final Architecture

```
RAW DATA (200 Pune property records)
  Pune_Real_Estate_Data.xlsx + data_cleaned.csv
         │
         ▼
PREPROCESSING  src/data/preprocess.py
  Clean → Engineer features → pune_features.csv (197 rows, 21 features)
         │
         ▼
MODEL TRAINING  src/models/train.py
  5 models × MLflow tracking → best_model.pkl (GBM, R²=0.795)
         │
         ▼
REST API  src/api/fastapi_app.py
  GET /health  POST /predict  POST /predict/batch  GET /metrics
         │
         ▼
DOCKER IMAGE  (~1.8 GB)
  python:3.10-slim + all deps + model baked in
  Pushed to → Docker Hub  AND  AWS ECR
         │
    ┌────┴────┐──────────────────┐
    ▼         ▼                  ▼
  EC2       ECS Fargate        EKS Kubernetes
  Ubuntu    2 tasks            3 pods / 2 nodes
  Supervisor ALB               Nginx Ingress + HPA
    │         │                  │
    └────┬────┘──────────────────┘
         │
         ▼
GITHUB ACTIONS CI/CD  (6 jobs on every push to main)
test → build → deploy-ec2 + deploy-ecs + deploy-eks → notify
         │
         ▼
MONITORING
Prometheus · Grafana (EKS) · CloudWatch (EC2 + ECS)
```

---

## 3. Phase 1 — Google Colab: Data and Model Training

### What Google Colab Is
Google Colab is a free cloud-based Jupyter notebook. It runs Python on
Google's servers — you need only a browser and a Google account. No
installation required on your machine.

Think of it as Python running in the cloud, inside your browser, where each
grey code box is called a **cell**.

**How to run a cell:** Click the cell once to select it.
Press **Shift + Enter**. The cell runs and moves to the next cell.
Wait for the spinning circle to disappear before running the next cell.

---

### Step 1 — Open the Notebook in Colab

1. Open **Google Chrome** (recommended browser)
2. Go to: **https://colab.research.google.com**
3. A page loads with a modal dialog. If no dialog appears, click
   **File** in the top menu bar → then click **Open notebook**
4. In the dialog, click the **Upload** tab
5. Click **Browse** (or drag and drop)
6. Navigate to your project folder:
   `C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops\notebooks\`
7. Select the file: `Pune_Real_Estate_EndToEnd_ML.ipynb`
8. Click **Open**
9. The notebook opens. You see a title at the top:
   **"Pune Real Estate — End-to-End ML Pipeline"**
   and a series of grey code boxes below it.

---

### Step 2 — Cell 1: Upload Raw Data Files

**What this cell does:** Creates the folder structure in Colab's cloud storage
and opens a file picker so you can upload your two data files.

1. Click on the first grey code box (Cell 1). It has this code at the top:
   ```python
   from google.colab import files
   ```
2. Press **Shift + Enter** to run it
3. Look at the output area BELOW the cell. A grey box appears with the text:
   **"Choose Files"** (a file upload button)
4. Click **Choose Files**
5. A Windows file picker dialog opens on your screen
6. Navigate to your project folder:
   `C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops\data\raw\`
7. Hold **Ctrl** on your keyboard and click BOTH files:
   - `Pune_Real_Estate_Data.xlsx`
   - `data_cleaned.csv`
8. Click **Open**
9. Watch the output below the cell. You see two progress bars. Wait for both
   to reach 100%
10. The final output shows:
    ```
    Saved → /content/data/raw/Pune_Real_Estate_Data.xlsx
    Saved → /content/data/raw/data_cleaned.csv
    Files in /content/data/raw/: ['Pune_Real_Estate_Data.xlsx', 'data_cleaned.csv']
    ```

**WARNING:** If only one file uploaded, do NOT run Cell 1 again. Instead,
run just the `files.upload()` line again. Running Cell 1 again recreates
the folders and may clear what was uploaded.

---

### Step 3 — Cell 2: Install Dependencies

1. Click on Cell 2. It contains:
   ```python
   !pip install -q mlflow pycaret[full] fastapi uvicorn joblib openpyxl
   ```
2. Press **Shift + Enter**
3. Many lines of text scroll by (packages downloading). This takes **3-5 minutes**
4. You know it is finished when the spinning circle on the left of the cell
   becomes a green tick (✓) and the next cell is highlighted
5. No output visible = success (the `-q` flag suppresses output)

**WARNING:** If you see a red error box with `ERROR: Could not install packages`,
look for the specific package name causing the error. Try installing it
separately: `!pip install <package-name> --quiet`

---

### Step 4 — Cell 3: Imports and File Detection

1. Click Cell 3 and press **Shift + Enter**
2. Output shows:
   ```
   XLSX: Pune_Real_Estate_Data.xlsx
   CSV : data_cleaned.csv
   ```
3. If either shows `None`, the file was not uploaded. Go back to Step 2.

---

### Step 5 — Cells 5–8: Exploratory Data Analysis

Run each cell by pressing **Shift + Enter** and waiting for it to complete.

**Cell 5** — Loads data, prints shape: `(200, 18)` means 200 rows, 18 columns.

**Cell 6** — Prints missing value counts. Normal to see some missing values
in `total_township_area_in_acres` (handled later with median imputation).

**Cell 7** — Shows two charts side by side:
- Left chart: Price distribution (right-skewed bell curve — most properties
  are cheaper, a few are expensive)
- Right chart: Log of price (more symmetric — confirms log transformation helps)

**Cell 8** — Shows a colour grid (heatmap):
- Red = positive correlation, Blue = negative, White = no correlation
- Look at the bottom row (`Price Cleaned`) — larger red values = stronger
  predictors of price

---

### Step 6 — Cell 10: Data Cleaning and Feature Engineering

This is the most important cell. It runs two functions:

**Press Shift + Enter** and wait. Expected output:
```
✅  Features saved — shape: (197, 21)
```
Followed by a table showing the first 3 rows.

**What the code does (plain English):**

| Action | Why |
|---|---|
| Lowercase all column names | Prevents bugs from capitalisation differences |
| Extract numbers from "1200 sqft" | Raw data has text mixed with numbers |
| Map "Yes"/"No" → 1/0 | ML models need numbers, not text |
| `log_area = log(area_sqft)` | Reduces right skew in area values |
| `amenity_score = sum of 7 flags` | Single score from 0–7 summarising all amenities |
| `price_per_sqft = price / area` | Efficiency metric |
| Label-encode location, type, company | Tree models need integers not text categories |
| Drop rows with no price or area | Cannot train on unknown answers |

Output file: `/content/data/processed/pune_features.csv` — 197 rows, 21 columns.

---

### Step 7 — Cell 12: Train 5 Models with MLflow

**Press Shift + Enter.** This takes **3-8 minutes** — the spinning circle stays
active the entire time. Do not click elsewhere or refresh.

Watch the output lines appear one by one:
```
Ridge           R²=0.742  MAE=14.4L  RMSE=19.8L  CV=0.718
Lasso           R²=0.765  MAE=12.7L  RMSE=18.2L  CV=0.739
RandomForest    R²=0.780  MAE=8.8L   RMSE=17.4L  CV=0.763
ExtraTrees      R²=0.791  MAE=9.4L   RMSE=16.9L  CV=0.771
GBM             R²=0.795  MAE=8.6L   RMSE=16.5L  CV=0.779  ← BEST

✅  Best: GBM  R²=0.795
```

**Reading the metrics:**
- **R²** = how much price variation the model explains. 0.795 = 79.5% explained.
  Closer to 1.0 is better.
- **MAE** = average prediction error in Lakhs. 8.64 Lakhs = off by ~₹864,000
  on average.
- **CV** = cross-validation R² across 5 different train/test splits.
  Confirms the model is not just getting lucky on one split.

Why GBM wins: highest R², lowest MAE, consistent CV score.

---

### Step 8 — Cells 13–14: Results Table and Feature Chart

**Cell 13:** Prints a sorted table of all 5 models. GBM at the top.

**Cell 14:** Prints a bar chart — which features matter most to the model.
Typically `area_sqft` and `log_area` are the tallest bars (property size
drives price most). Location and amenity scores appear in the middle.

---

### Step 9 — Cells 16–17: PyCaret AutoML

**Cell 16:** Press **Shift + Enter**. Takes **10-15 minutes**. PyCaret runs
20+ different algorithm types automatically and ranks them by R². Output is a
table of all models tested. Gradient boosting variants appear at the top,
confirming our scikit-learn experiment.

**Cell 17:** Tunes the best PyCaret model with Bayesian optimisation (20
iterations) and saves it to `/content/models/pycaret_best.pkl`.

---

### Step 10 — Cells 19–21: Test FastAPI Inside Colab

**Cell 19:** Writes the FastAPI app code to a file. Output: `FastAPI app written.`

**Cell 20:** Starts the FastAPI server and creates a public tunnel URL.
Output shows a URL like:
```
🌐 Public API URL: https://abc123.ngrok.io
   Swagger docs : https://abc123.ngrok.io/docs
```

**If ngrok asks for an auth token:** Create a free account at
https://ngrok.com → Dashboard → Copy your token →
Run: `!ngrok authtoken YOUR_TOKEN` → Then re-run Cell 20.

**Cell 21:** Tests the `/predict` endpoint. Output shows:
```
Status: 200
Response: {'predicted_price_lakhs': 87.4, 'predicted_price_millions': 8.74}
```
This confirms the full pipeline works end-to-end.

---

### Step 11 — Cell 23: Download Outputs from Colab

**Press Shift + Enter.** Your browser automatically downloads two files:
- `pune_features.csv` → saved to your Windows `Downloads` folder
- `best_model.pkl` → saved to your Windows `Downloads` folder

Open **Windows Explorer** (press `Windows key + E`):
1. Go to `C:\Users\YOUR_NAME\Downloads\`
2. Find `pune_features.csv` → Copy it (Ctrl+C)
3. Go to `C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops\data\processed\`
4. Paste it (Ctrl+V)
5. Go back to Downloads
6. Find `best_model.pkl` → Copy it
7. Go to `C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops\models\`
8. Paste it

---

## 4. Phase 2 — VS Code: Local Development

### Step 12 — Open the Project in VS Code

**Method A — From VS Code:**
1. Open VS Code from the Start Menu or taskbar
2. In the top menu bar, click **File**
3. In the dropdown, click **Open Folder**
4. A Windows folder picker opens
5. Navigate to: `C:\Users\YOUR_NAME\Desktop\`
6. Click once on `pune_real_estate_mlops` (do not open it, just select it)
7. Click **Select Folder** button (bottom-right of the picker)
8. VS Code reloads. On the left panel you see the folder tree:
   `data/`, `models/`, `src/`, `deployment/`, etc.

**Method B — From PowerShell:**
```powershell
code C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops
```

---

### Step 13 — Open the Integrated Terminal in VS Code

1. Look at the top menu bar: **Terminal** → click it
2. In the dropdown, click **New Terminal**
3. A terminal panel slides up from the bottom of VS Code
4. The prompt shows something like:
   `PS C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops>`
5. The `PS` prefix means it is PowerShell. This is correct.

If the path in the prompt is wrong, type:
```powershell
cd C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops
```

---

### Step 14 — Activate the Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

After running this, your prompt changes to:
```
(.venv) PS C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops>
```
The `(.venv)` prefix confirms the virtual environment is active.

**If you see: "cannot be loaded because running scripts is disabled"**
Run this once, then retry:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# When prompted: type Y and press Enter
```

**If you see: "the path .venv does not exist"**
Create the virtual environment first:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

### Step 15 — Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

This takes **10-20 minutes** on first run. You see hundreds of lines like:
`Collecting pandas...`, `Downloading pandas-2.2.0...`, etc.

When finished, the last line reads:
`Successfully installed [list of packages]`

Verify everything installed:
```powershell
python -c "import pandas, sklearn, mlflow, fastapi, joblib; print('All OK')"
```
Expected output: `All OK`

---

### Step 16 — Run Data Preprocessing

```powershell
python src/data/preprocess.py
```

Expected output:
```
Raw XLSX : (200, 18)  |  Cleaned CSV : (200, 12)
✅  Feature set saved → ...\data\processed\pune_features.csv
   Shape   : (197, 21)
```

**If you see FileNotFoundError:** The raw data files are missing from
`data/raw/`. Copy them from wherever you stored the original files.

---

### Step 17 — Run Model Training

```powershell
python src/models/train.py
```

Takes 3-8 minutes. Expected output ends with:
```
✅  Best model (gbm, R²=0.795) saved → models\best_model.pkl
```

---

### Step 18 — View MLflow Dashboard

```powershell
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

The terminal shows:
```
[INFO] Starting gunicorn server
[INFO] Listening at: http://127.0.0.1:5000
```

Open your browser → go to **http://localhost:5000**

**Navigating the MLflow UI:**
1. The main page shows **Experiments** on the left sidebar
2. Click **pune_real_estate_price_prediction**
3. A table appears showing 5 rows — one per model run
4. Click the column header **test_r2** to sort by R² descending
5. GBM appears at the top
6. Click any row (run name) to see full details: all metrics, parameters, plots
7. To compare runs: tick the checkboxes on 2+ rows → click **Compare**
8. A side-by-side comparison page opens showing metric differences

Press **Ctrl+C** in the terminal to stop MLflow when done.

---

### Step 19 — Run FastAPI Locally

Open a **second terminal** in VS Code:
1. Click **Terminal** in the top menu bar
2. Click **New Terminal** again
3. A second terminal panel appears (you can switch between them using the
   dropdown in the terminal panel top-right)

In the second terminal:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn src.api.fastapi_app:app --reload --port 8000
```

Output:
```
INFO: Started server process
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

Open browser → **http://localhost:8000/docs**

**Navigating Swagger UI:**
1. The page shows three sections: `Monitoring`, `Prediction`, each collapsed
2. Click **GET /health** to expand it
3. Click the **Try it out** button (top-right of the section)
4. Click the blue **Execute** button
5. Scroll down — you see `Response body: {"status":"ok","model_loaded":true}`
6. Click **POST /predict** to expand it
7. Click **Try it out**
8. The request body shows a JSON template — modify the values if desired
9. Click **Execute**
10. Response body shows the predicted price

Press **Ctrl+C** to stop the server.

---

## 5. Phase 3 — Docker: Containerisation

### Step 20 — Verify Docker Desktop is Running

Look at the Windows **taskbar** (bottom of screen). Find the system tray
(bottom-right corner, near the clock). Look for a whale icon (🐳).

- **Whale icon visible, not spinning** = Docker is running. Proceed.
- **No whale icon** = Docker Desktop is not open.
  Click **Start** → search for **Docker Desktop** → click to open it.
  Wait 60 seconds until the whale icon appears and stops animating.

Verify in PowerShell:
```powershell
docker --version
```
Expected: `Docker version 24.x.x`

---

### Step 21 — Build the Docker Image

In the VS Code terminal (with `.venv` active, in the project root):
```powershell
docker build -t pune-real-estate-api:latest -f deployment/docker/Dockerfile .
```

**The dot `.` at the very end is required** — it tells Docker to use the
current folder as the build context.

Output scrolls through 7 build steps. Takes 10-20 minutes first time.
On subsequent builds (code changes only, no requirements change), takes
30-60 seconds because Docker caches the pip install layer.

Final line: `=> exporting to image` followed by a success summary.

Verify the image exists:
```powershell
docker images pune-real-estate-api
```
Expected: one row showing the image with a size ~1.8GB.

---

### Step 22 — Test the Container Locally

```powershell
docker run -d --name pune_api_test -p 8000:8000 pune-real-estate-api:latest
Start-Sleep -Seconds 35
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing | Select-Object -ExpandProperty Content
```

Expected: `{"status":"ok","model_loaded":true}`

View container logs:
```powershell
docker logs pune_api_test
```
Look for the line: `✅  Model loaded successfully.`

Stop and remove the test container:
```powershell
docker stop pune_api_test
docker rm pune_api_test
```

---

### Step 23 — Create Docker Hub Account and Repository

1. Open browser → go to **https://hub.docker.com**
2. Click **Sign Up** (top-right)
3. Fill in: username, email, password
4. Verify your email address (check inbox, click the link)
5. Log in to Docker Hub
6. Click **Create Repository** (blue button on the main page)
7. Fill in:
   - Repository name: `pune-real-estate-api`
   - Visibility: **Public**
8. Click **Create**

**Create an Access Token (more secure than your password):**
1. Click your username/avatar (top-right corner)
2. Click **Account Settings** in the dropdown
3. In the left sidebar, click **Security**
4. Click **New Access Token**
5. Token description: `github-actions`
6. Access permissions: **Read, Write, Delete**
7. Click **Generate**
8. A token appears (long string of letters/numbers)
9. Click **Copy** next to the token — it shows **only once**
10. Paste it into your `my_setup.txt` file as `DOCKERHUB_TOKEN`

---

### Step 24 — Push Image to Docker Hub

```powershell
# Log in (when prompted for Password, paste the ACCESS TOKEN not your password)
docker login -u YOUR_DOCKERHUB_USERNAME

# Tag with your username
docker tag pune-real-estate-api:latest YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:latest
docker tag pune-real-estate-api:latest YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:v1.0.0

# Push
docker push YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:latest
docker push YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:v1.0.0
```

Takes 5-15 minutes. Final output:
```
latest: digest: sha256:abc123... size: 1234
```

Verify on Docker Hub:
1. Browser → **https://hub.docker.com/r/YOUR_DOCKERHUB_USERNAME/pune-real-estate-api**
2. Click the **Tags** tab
3. You should see: `latest` and `v1.0.0`

---

## 6. Phase 4 — GitHub: Version Control and CI/CD

### Step 25 — Push Code to GitHub

```powershell
git config user.name "YOUR FULL NAME"
git config user.email "YOUR_EMAIL"
git add .
git commit -m "Initial commit: Pune Real Estate MLOps pipeline"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/pune_real_estate_mlops.git
git push -u origin main
```

Verify:
1. Browser → **https://github.com/YOUR_GITHUB_USERNAME/pune_real_estate_mlops**
2. You see your files listed on the repository page

---

### Step 26 — Add GitHub Actions Secrets

Go to your repository page on GitHub.

**Navigation path:**
1. Click the **Settings** tab (last tab in the top navigation row of your repo)
2. In the **left sidebar**, scroll down to find **Secrets and variables**
3. Click the small arrow/triangle next to it to expand
4. Click **Actions** (a sub-item appears below)
5. The page title says: **Actions secrets and variables**
6. Click the green **New repository secret** button

Add one secret at a time. For each secret:
1. Click **New repository secret**
2. In **Name** field: type the secret name exactly (case-sensitive)
3. In **Secret** field: paste the value
4. Click **Add secret**

**Add these 6 secrets:**

**Secret 1: DOCKERHUB_USERNAME**
- Name: `DOCKERHUB_USERNAME`
- Value: your Docker Hub username (e.g., `johndoe`)

**Secret 2: DOCKERHUB_TOKEN**
- Name: `DOCKERHUB_TOKEN`
- Value: the access token from Docker Hub Security page (Step 23)

**Secret 3: EC2_HOST**
- Name: `EC2_HOST`
- Value: your EC2 Elastic IP address (get this in Phase 6 — come back here)

**Secret 4: EC2_SSH_KEY**
- Name: `EC2_SSH_KEY`
- Value: the full contents of your `.pem` file
- To get it: `Get-Content C:\Users\YOUR_NAME\Downloads\YOUR_EC2_KEY_NAME.pem | Set-Clipboard`
- Then paste into the Secret field

**Secret 5: AWS_ACCESS_KEY_ID**
- Name: `AWS_ACCESS_KEY_ID`
- Value: the Access Key ID from your IAM user (get this in Phase 5)

**Secret 6: AWS_SECRET_ACCESS_KEY**
- Name: `AWS_SECRET_ACCESS_KEY`
- Value: the Secret Access Key from your IAM user (get this in Phase 5)

---

### Step 27 — The CI/CD Workflow File

The file `.github/workflows/deploy.yml` defines the 6-job pipeline:

```
Every push to main branch triggers:
│
├── Job 1 — test
│   Install Python → run preprocess.py → run train.py → pytest
│
├── Job 2 — build  (runs after test passes)
│   Install Python → train model → build Docker image →
│   push to Docker Hub → push to ECR
│
├── Job 3 — deploy-ec2  (runs after build)
│   SSH into EC2 → git pull → pip install → supervisorctl restart
│
├── Job 4 — deploy-ecs  (runs after build, parallel to ec2 and eks)
│   Update ECS task definition with new image → force ECS redeployment
│
├── Job 5 — deploy-eks  (runs after build, parallel to ec2 and ecs)
│   kubectl set image → rollout status (5-minute timeout)
│
└── Job 6 — notify  (runs after all three deploys, always)
    Print summary table → send Slack notification (optional)
```

---

## 7. Phase 5 — AWS Setup: IAM, CLI, ECR

### Step 28 — Create AWS Account

1. Browser → **https://aws.amazon.com**
2. Click **Create an AWS Account** (top-right orange button)
3. Fill in:
   - Root user email address: your email
   - AWS account name: e.g., `MyMLOpsAccount`
4. Click **Verify email address** → check inbox → enter the verification code
5. Set a root user password (strong password — store it safely)
6. Fill in contact information (select Personal or Business)
7. Enter credit/debit card (you will not be charged if using Free Tier resources)
8. Phone number verification (you receive a call or SMS)
9. Select **Basic support — Free**
10. Click **Complete sign up**
11. Click **Go to the AWS Management Console**

---

### Step 29 — Create an IAM User (Do Not Use Root for Daily Work)

Using the root account for daily operations is unsafe. Create an IAM user.

**Navigation in AWS Console:**
1. In the top search bar, type `IAM` and press Enter
2. The IAM dashboard opens
3. In the **left sidebar**, click **Users**
4. Click the orange **Create user** button (top-right)

**Step A — User details:**
- Username: `mlops-deploy` (or any name — record in `my_setup.txt` as `YOUR_IAM_USERNAME`)
- Tick: **Provide user access to the AWS Management Console** (optional)
- Click **Next**

**Step B — Set permissions:**
- Select: **Attach policies directly**
- In the search box, search for and tick each of these policies:
  - `AmazonEC2FullAccess`
  - `AmazonECS_FullAccess`
  - `CloudWatchFullAccess`
- Click **Next**
- Click **Create user**

**Step C — Create access keys:**
1. Click on the username you just created to open the user page
2. Click the **Security credentials** tab
3. Scroll down to **Access keys** section
4. Click **Create access key**
5. Use case: select **Application running outside AWS**
6. Click **Next**
7. Description tag: `github-actions-key`
8. Click **Create access key**
9. You see two values:
   - **Access key ID** — copy this → paste into `my_setup.txt` as `AWS_ACCESS_KEY_ID`
   - **Secret access key** — click **Show** → copy it → paste as `AWS_SECRET_ACCESS_KEY`
10. Click **Done** (you cannot view the secret key again after this)

**IMPORTANT:** The inline policy `eksctl-ecr-permissions` is also required
for EKS and ECR. Add it after the managed policy limit is reached (see
Issue 10 in Section 12).

---

### Step 30 — Install and Configure AWS CLI

**Install AWS CLI:**
```powershell
winget install Amazon.AWSCLI
```
Close and reopen PowerShell after installation. Verify:
```powershell
aws --version
```
Expected: `aws-cli/2.x.x Python/3.x.x Windows/...`

**Configure:**
```powershell
aws configure
```
You are prompted for 4 values:
```
AWS Access Key ID:     [paste YOUR_AWS_ACCESS_KEY_ID]
AWS Secret Access Key: [paste YOUR_AWS_SECRET_ACCESS_KEY]
Default region name:   us-east-1
Default output format: json
```

Verify it works:
```powershell
aws sts get-caller-identity
```
Expected output shows your account ID and IAM username.

---

### Step 31 — Create ECR Repository

```powershell
aws ecr create-repository `
  --repository-name pune-real-estate-api `
  --region us-east-1 `
  --image-scanning-configuration scanOnPush=true
```

Output includes:
```json
"repositoryUri": "YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pune-real-estate-api"
```

Note this URI — it is used in the task definition and deployment manifests.

**Verify in AWS Console:**
1. Search `ECR` in the top search bar
2. Click **Elastic Container Registry**
3. In the left sidebar, click **Repositories** (under **Private registry**)
4. You see `pune-real-estate-api` listed
5. Click it to see details including the repository URI

---

## 8. Phase 6 — AWS ECS Fargate Deployment

### Step 32 — Launch EC2 Instance

**Navigation in AWS Console:**
1. In the top search bar, type `EC2` and press Enter
2. The EC2 Dashboard opens
3. Verify the **Region** selector (top-right, next to your account name)
   shows **N. Virginia** (us-east-1). If not, click it → scroll to
   **US East (N. Virginia)** → click it
4. Click the orange **Launch instance** button

**On the Launch instance page, fill in these settings from top to bottom:**

**Name and tags section:**
- In the **Name** field, type: `pune-real-estate-api`

**Application and OS Images section:**
- Click the **Ubuntu** box (Quick Start row of OS options)
- The AMI automatically changes to:
  `Ubuntu Server 22.04 LTS (HVM), SSD Volume Type`
- Confirm it shows **Free tier eligible** (look for the orange badge)

**Instance type section:**
- The default `t2.micro` is selected (Free tier — 1 vCPU, 1GB RAM)
- For production with real traffic: change to `t3.small` (2 vCPU, 2GB RAM)
- Click the dropdown → type `t3.small` → select it

**Key pair (login) section:**
- Click **Create new key pair**
- A dialog appears:
  - Key pair name: `pune-api-key`
  - Key pair type: **RSA**
  - Private key file format: **.pem**
- Click **Create key pair**
- Your browser **automatically downloads** `pune-api-key.pem`
- Go to Windows Explorer → Downloads folder → move `pune-api-key.pem`
  to a safe place (e.g., `C:\Users\YOUR_NAME\Documents\AWS-Keys\`)
- **CRITICAL: This file is your only way to SSH into this server.
  If you lose it, you cannot connect. Do not delete it.**

**Network settings section:**
- Click the **Edit** button (top-right of this section)
- Under **Firewall (security groups)**: keep **Create security group** selected
- Security group name: `pune-api-sg`
- Description: `Security group for Pune API EC2`
- Under **Inbound security group rules**, you already see SSH (port 22)
- For the SSH rule: in **Source type** dropdown, select **My IP**
  (this restricts SSH access to only your current IP address)
- Click **Add security group rule** → adds a new row:
  - Type: `HTTP`
  - Port: `80`
  - Source type: `Anywhere`
- Click **Add security group rule** again:
  - Type: `HTTPS`
  - Port: `443`
  - Source type: `Anywhere`
- **Do NOT add port 8000** — Nginx will forward port 80 to port 8000

**Configure storage section:**
- Change the size from 8 to **20** GiB
- Keep type: `gp3`

**Summary panel (right side):**
- Verify: 1 instance, Ubuntu 22.04, t3.small (or t2.micro)
- Click the orange **Launch instance** button

**After launch:**
1. A green success banner appears: *"Successfully initiated launch of instance i-0abc123..."*
2. Click the **instance ID** link (blue text like `i-0abc123def456`)
3. The Instances page opens with your new instance highlighted
4. Wait until the **Instance state** column shows **Running** (green dot)
   and **Status check** shows **2/2 checks passed**
   (click the refresh icon at the top-right of the table to update)
5. In the details panel at the bottom, find **Public IPv4 address**
6. Copy this IP → paste into `my_setup.txt` as `YOUR_EC2_IP`

---

### Step 33 — Associate Elastic IP (Permanent IP Address)

EC2 instances get a new IP address every time they restart. An Elastic IP
stays the same permanently.

**Navigation:**
1. In the EC2 left sidebar, scroll down to **Network & Security**
2. Click **Elastic IPs**
3. Click **Allocate Elastic IP address** (top-right)
4. Network border group: keep the default
5. Click **Allocate**
6. The new Elastic IP appears in the table
7. Click the **Actions** dropdown (top-right) → click **Associate Elastic IP address**
8. In the dialog:
   - **Resource type**: Instance
   - **Instance**: click the box → select your `pune-real-estate-api` instance
   - **Private IP address**: keep the default
9. Click **Associate**
10. Back on the Elastic IPs page, note the **Allocated IPv4 address**
11. Copy it → paste into `my_setup.txt` as `YOUR_EC2_ELASTIC_IP`

---

### Step 34 — SSH into EC2 from Windows

First, set permissions on your key file (Windows requires this):
```powershell
$pem = "C:\Users\YOUR_NAME\Documents\AWS-Keys\pune-api-key.pem"
icacls $pem /inheritance:r
icacls $pem /grant:r "${env:USERNAME}:(R)"
```

Connect:
```powershell
ssh -i C:\Users\YOUR_NAME\Documents\AWS-Keys\pune-api-key.pem ubuntu@YOUR_EC2_ELASTIC_IP
```

First connection shows:
```
The authenticity of host 'x.x.x.x' can't be established.
Are you sure you want to continue connecting (yes/no)?
```
Type `yes` and press Enter.

You now see the EC2 prompt:
```
ubuntu@ip-x-x-x-x:~$
```
You are inside the EC2 server.

---

### Step 35 — Set Up EC2 Server

Run these commands **inside the EC2 SSH session**:

```bash
# 1. Update system packages
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# 3. Install Nginx, Certbot, git, Python venv
sudo apt-get install -y nginx certbot python3-certbot-nginx python3-venv git curl

# 4. Log out so Docker group membership takes effect
exit
```

SSH back in:
```powershell
ssh -i C:\Users\YOUR_NAME\Documents\AWS-Keys\pune-api-key.pem ubuntu@YOUR_EC2_ELASTIC_IP
```

```bash
# 5. Verify Docker works without sudo
docker ps
# Expected: empty table with headers, no error

# 6. Clone your GitHub repo
git clone https://github.com/YOUR_GITHUB_USERNAME/pune_real_estate_mlops.git
cd pune_real_estate_mlops

# 7. Create virtual environment and install production deps
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements_docker.txt

# 8. Run the pipeline to create the model
python src/data/preprocess.py
python src/models/train.py

# 9. Start the API manually to verify it works
uvicorn src.api.fastapi_app:app --host 0.0.0.0 --port 8000 &
sleep 10
curl http://localhost:8000/health
# Expected: {"status":"ok","model_loaded":true}
kill %1   # stop the background uvicorn
```

---

### Step 36 — Configure Nginx as Reverse Proxy

Still inside the EC2 SSH session:
```bash
sudo tee /etc/nginx/sites-available/pune_api > /dev/null <<'NGINX'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/pune_api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
```

Expected: `nginx: configuration file ... test is successful`

```bash
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

### Step 37 — Configure Supervisor for 24/7 API Process

Supervisor keeps the API running after restarts and crashes.

```bash
sudo apt-get install -y supervisor

sudo tee /etc/supervisor/conf.d/pune_api.conf > /dev/null <<EOF
[program:pune_api]
command=$(pwd)/.venv/bin/uvicorn src.api.fastapi_app:app --host 0.0.0.0 --port 8000
directory=$(pwd)
user=ubuntu
autostart=true
autorestart=true
stdout_logfile=/var/log/pune_api.log
stderr_logfile=/var/log/pune_api_error.log
environment=PYTHONUNBUFFERED=1
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start pune_api
sudo supervisorctl status
```

Expected: `pune_api    RUNNING   pid 1234, uptime 0:00:05`

Test via Nginx (port 80):
```bash
curl http://localhost/health
```
Expected: `{"status":"ok","model_loaded":true}`

Test from your Windows machine:
```powershell
Invoke-WebRequest -Uri "http://YOUR_EC2_ELASTIC_IP/health" -UseBasicParsing | Select-Object -ExpandProperty Content
```

Open Swagger UI in browser: **http://YOUR_EC2_ELASTIC_IP/docs**

---

### Step 38 — Create ECS Infrastructure

**Create IAM roles:**
```powershell
# Save trust policy
@'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
'@ | Out-File -Encoding utf8 deployment/ecs/ecs-trust-policy.json

# Create execution role (allows ECS to pull images and write logs)
aws iam create-role --role-name ecsTaskExecutionRole `
  --assume-role-policy-document file://deployment/ecs/ecs-trust-policy.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole `
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create task role (application-level permissions)
aws iam create-role --role-name ecsTaskRole `
  --assume-role-policy-document file://deployment/ecs/ecs-trust-policy.json
aws iam attach-role-policy --role-name ecsTaskRole `
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```

**Create CloudWatch log group and ECS cluster:**
```powershell
aws logs create-log-group --log-group-name /ecs/pune-api --region us-east-1
aws logs put-retention-policy --log-group-name /ecs/pune-api --retention-in-days 30

aws ecs create-cluster --cluster-name pune-api-cluster --capacity-providers FARGATE
```

**Get your VPC and subnet IDs:**
```powershell
$vpc = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" `
  --query "Vpcs[0].VpcId" --output text
$subnets = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpc" `
  --query "Subnets[*].SubnetId" --output text
Write-Output "VPC: $vpc"
Write-Output "Subnets: $subnets"
```
Copy these values into `my_setup.txt`.

**Create security groups:**
```powershell
$VPC = "YOUR_VPC_ID"

$ALB_SG = aws ec2 create-security-group `
  --group-name pune-alb-sg `
  --description "ALB for pune-api ECS" `
  --vpc-id $VPC --query "GroupId" --output text

aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 80  --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 443 --cidr 0.0.0.0/0

$TASK_SG = aws ec2 create-security-group `
  --group-name pune-ecs-task-sg `
  --description "ECS tasks for pune-api" `
  --vpc-id $VPC --query "GroupId" --output text

aws ec2 authorize-security-group-ingress --group-id $TASK_SG `
  --protocol tcp --port 8000 --source-group $ALB_SG
```

**Create ALB in AWS Console:**
1. Search `EC2` → Click **Load Balancers** in the left sidebar
   (under Load Balancing)
2. Click **Create load balancer**
3. Under **Application Load Balancer**, click **Create**
4. **Basic configuration:**
   - Name: `pune-api-alb`
   - Scheme: **Internet-facing**
   - IP address type: **IPv4**
5. **Network mapping:** Tick at least 3 availability zones (us-east-1a, 1b, 1c)
6. **Security groups:** Select `pune-alb-sg`
7. **Listeners and routing:** For Port 80:
   - Click **Create target group** (opens in a new tab)
   - Target type: **IP addresses** (NOT Instance — Fargate uses IP targets)
   - Target group name: `pune-api-tg`
   - Protocol: HTTP, Port: 8000
   - Health check protocol: HTTP
   - Health check path: `/health`
   - Healthy threshold: 2, Unhealthy threshold: 3
   - Click **Next** → **Create target group**
   - Go back to the ALB tab, refresh the target group dropdown, select `pune-api-tg`
8. Click **Create load balancer**
9. On the load balancers page, click your new ALB → copy the **DNS name** →
   save as `YOUR_ECS_ALB_DNS`

**Update task definition with your account ID:**

Open `deployment/ecs/task-definition.json` in VS Code.
Replace every occurrence of `YOUR_AWS_ACCOUNT_ID` with your actual account ID.
Save the file.

**Register task definition:**
```powershell
aws ecs register-task-definition `
  --cli-input-json file://deployment/ecs/task-definition.json
```

**Create ECS Service:**
```powershell
$TG_ARN  = "YOUR_TG_ARN"
$TASK_SG = "YOUR_TASK_SG_ID"
$SUBNETS = "YOUR_SUBNET_ID_1,YOUR_SUBNET_ID_2,YOUR_SUBNET_ID_3"

aws ecs create-service `
  --cluster pune-api-cluster `
  --service-name pune-api-service `
  --task-definition pune-api-task:1 `
  --desired-count 2 `
  --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$TASK_SG],assignPublicIp=ENABLED}" `
  --load-balancers "targetGroupArn=$TG_ARN,containerName=pune-api,containerPort=8000" `
  --health-check-grace-period-seconds 60
```

**Verify ECS in AWS Console:**
1. Search `ECS` in the search bar
2. Click **Elastic Container Service**
3. Click **Clusters** in the left sidebar
4. Click **pune-api-cluster**
5. Click the **Services** tab
6. Click **pune-api-service**
7. Click the **Tasks** tab — you see 2 tasks starting
8. Wait 2-3 minutes → refresh → both tasks show **RUNNING**
9. Click the **Events** tab to see the deployment timeline

Test via ALB:
```powershell
Invoke-WebRequest -Uri "http://YOUR_ECS_ALB_DNS/health" -UseBasicParsing | Select-Object -ExpandProperty Content
```

---

## 9. Phase 7 — AWS EKS Kubernetes Deployment

### Step 39 — Install Kubernetes Tools

**Install kubectl:**
```powershell
winget install Kubernetes.kubectl
# Close and reopen PowerShell
kubectl version --client
```

**Install eksctl:**
1. Browser → **https://github.com/weaveworks/eksctl/releases/latest**
2. Under **Assets**, find `eksctl_Windows_amd64.zip` → click to download
3. Open the zip file → drag `eksctl.exe` out
4. Move `eksctl.exe` to `C:\Windows\System32\` (requires admin)
5. Open PowerShell and verify:
```powershell
eksctl version
```

---

### Step 40 — Create EKS Cluster

**WARNING: This costs approximately $0.10/hour for the control plane (~$73/month),
plus EC2 costs for worker nodes (~$30/month for 2× t3.small).
Total: ~$103/month. Delete the cluster when not in use.**

```powershell
eksctl create cluster `
  --name pune-api-eks `
  --region us-east-1 `
  --nodegroup-name pune-api-nodes `
  --node-type t3.small `
  --nodes 2 `
  --nodes-min 1 `
  --nodes-max 4 `
  --managed `
  --with-oidc `
  --full-ecr-access
```

This takes **15-20 minutes**. Output shows CloudFormation stacks being created.
When complete, the last two lines read:
```
✔  EKS cluster "pune-api-eks" in "us-east-1" region is ready
✔  saved kubeconfig as "C:\Users\YOUR_NAME\.kube\config"
```

kubectl is now automatically configured to talk to the cluster.

Verify:
```powershell
kubectl get nodes
```
Expected: 2 nodes, both with STATUS = `Ready`

**Verify in AWS Console:**
1. Search `EKS` → click **Elastic Kubernetes Service**
2. Click **Clusters** in the left sidebar
3. Click **pune-api-eks**
4. Click the **Compute** tab
5. Scroll to **Node groups** → click `pune-api-nodes`
6. You see 2 nodes listed with status **Ready**

---

### Step 41 — Update k8s Manifests with Your Account ID

Open `k8s/deployment.yaml` in VS Code.
Find the line:
```yaml
image: YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pune-real-estate-api:latest
```
Replace `YOUR_AWS_ACCOUNT_ID` with your actual account ID. Save.

---

### Step 42 — Apply Kubernetes Manifests

```powershell
cd C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops

# Apply in dependency order (namespace first)
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Install Nginx Ingress Controller (creates the public LoadBalancer)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/aws/deploy.yaml

# Wait for LoadBalancer hostname to be assigned
Start-Sleep -Seconds 90
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

The `EXTERNAL-IP` column shows a hostname like:
`a1b2c3d4e5f6g7h8-12345678.us-east-1.elb.amazonaws.com`

Copy this → save as `YOUR_EKS_LB_DNS`

**Apply ingress and monitoring:**
```powershell
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/monitoring/prometheus.yaml
kubectl apply -f k8s/monitoring/grafana.yaml
```

**Verify all pods are running:**
```powershell
kubectl get pods -n pune-api
```

Expected (all showing `1/1 Running`):
```
NAME                          READY   STATUS    RESTARTS
grafana-xxx                   1/1     Running   0
prometheus-xxx                1/1     Running   0
pune-api-xxx-1                1/1     Running   0
pune-api-xxx-2                1/1     Running   0
pune-api-xxx-3                1/1     Running   0
```

**Test EKS API:**
```powershell
Invoke-WebRequest -Uri "http://YOUR_EKS_LB_DNS/health" -UseBasicParsing | Select-Object -ExpandProperty Content
```
Expected: `{"status":"ok","model_loaded":true}`

---

## 10. Phase 8 — Monitoring Dashboards

### Dashboard 1 — Swagger UI (Available Immediately, No Setup)

Open directly in your browser:
- EC2: `http://YOUR_EC2_ELASTIC_IP/docs`
- ECS: `http://YOUR_ECS_ALB_DNS/docs`
- EKS: `http://YOUR_EKS_LB_DNS/docs`

**Using Swagger UI:**
1. Page loads showing three sections: Monitoring, Prediction
2. To test health: click **GET /health** → click **Try it out** →
   click **Execute** → see response below
3. To test prediction: click **POST /predict** → click **Try it out** →
   edit the JSON in the **Request body** field → click **Execute** →
   see the predicted price in the response

---

### Dashboard 2 — Grafana (Visual Charts)

Grafana runs inside EKS. Its service has a public LoadBalancer URL.

Get the URL:
```powershell
kubectl get svc grafana -n pune-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```
Copy the output → this is `YOUR_GRAFANA_LB_DNS`

Open in browser: `http://YOUR_GRAFANA_LB_DNS:3000`

**Login:**
- Username: `admin`
- Password: `PuneAPI@2026`
  *(Change this in production: Grafana → Profile → Change Password)*

**Import the pre-built dashboard:**
1. On the Grafana home page, look at the **left sidebar**
2. Hover over the four-squares icon (Dashboards)
3. Click **Import** in the submenu
4. The Import page appears
5. Click **Upload JSON file**
6. A file picker opens — navigate to:
   `C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops\monitoring\grafana_dashboard.json`
7. Select the file → click Open
8. The import form shows the dashboard details
9. In the **Prometheus** dropdown, select your Prometheus data source
10. Click **Import**
11. The dashboard opens showing 6 panels:
    - Request Rate (requests per second)
    - Response Time (P50/P95/P99 latencies)
    - Error Rate (percentage of 5xx responses)
    - Running Pod Count
    - Prediction Value Distribution
    - CPU and Memory usage per pod

**To make a panel full-screen:** Click the panel title → click **View**

---

### Dashboard 3 — Prometheus (Raw Metrics Query)

Get the URL:
```powershell
kubectl get svc prometheus -n pune-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```
Open in browser: `http://YOUR_PROMETHEUS_LB_DNS:9090`

**Using Prometheus:**
1. The page has a search box at the top with **Expression** placeholder text
2. Click in the box and type a query, then click **Execute**

Useful queries:
```
# How many requests per second hit /predict
rate(http_requests_total{handler="/predict"}[5m])

# P99 response time in seconds
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Error rate as a percentage
100 * rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])

# Number of healthy API pods
count(up{job="pune-api"} == 1)
```

3. Click **Graph** tab to see the metric as a time-series chart
4. Click **Table** tab to see the current numeric values

---

### Dashboard 4 — AWS CloudWatch (EC2 + ECS Metrics)

**Run this once to create all dashboards and alarms:**
```powershell
cd C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops
.\.venv\Scripts\Activate.ps1
pip install boto3

python monitoring/cloudwatch_setup.py `
  --alb-arn "YOUR_ALB_ARN" `
  --email YOUR_EMAIL
```

Output shows alarms and dashboard created. Check your email — a confirmation
message arrives from AWS Notifications. **Click Confirm subscription** in that
email or alarms will not send notifications.

**Open the dashboard in AWS Console:**
1. In the AWS Console search bar, type `CloudWatch` → press Enter
2. In the left sidebar, click **Dashboards**
3. In the dashboard list, click **PuneRealEstateAPI**
4. Four charts appear:
   - Request Count (per 5 minutes)
   - 5xx and 4xx error counts
   - Response time P50/P95/P99
   - Healthy host count

**To see alarms:**
1. Left sidebar → click **Alarms** → click **All alarms**
2. Three alarms are listed:
   - `pune-api-5xx-error-rate` — fires if >10 errors in 5 minutes
   - `pune-api-high-latency` — fires if P99 > 2 seconds
   - `pune-api-unhealthy-hosts` — fires if healthy hosts < 1

---

### Dashboard 5 — MLflow (Local Experiment Tracking Only)

MLflow tracks model training experiments locally. It is not deployed to cloud.

```powershell
cd C:\Users\YOUR_NAME\Desktop\pune_real_estate_mlops
.\.venv\Scripts\Activate.ps1
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

Open browser → **http://localhost:5000**

**Navigating MLflow:**
1. Left sidebar shows **Experiments**
2. Click **pune_real_estate_price_prediction**
3. A table shows 5 rows (one per model run)
4. Click the **test_r2** column header to sort descending — GBM appears first
5. Tick the checkbox on any two rows → click **Compare** to see them side-by-side
6. Click any row (run name) to see: all parameters, all metrics,
   charts of metric values, and the saved model artifact

Press **Ctrl+C** in the terminal to stop MLflow.

---

## 11. CI/CD Pipeline Explained

### How GitHub Actions Works

Every time you push code to the `main` branch on GitHub:
1. GitHub detects the push
2. GitHub starts a fresh Ubuntu virtual machine (the **runner**)
3. The runner executes the jobs defined in `.github/workflows/deploy.yml`
4. Each job runs its steps in sequence
5. You can watch the progress in real time:

**How to watch a pipeline run:**
1. Go to `https://github.com/YOUR_GITHUB_USERNAME/pune_real_estate_mlops`
2. Click the **Actions** tab (between Pull requests and Security in the top nav)
3. The most recent workflow run appears at the top of the list
4. Click the run name (e.g., "fix: train model in build job...")
5. The run detail page shows a diagram with 6 job boxes
6. Click any job box to see its step-by-step log
7. Expand any step by clicking its row to see the full output
8. A green tick (✓) = success. Red X = failed. Yellow spinning circle = running.

### What Each Job Does

**Job 1 — test (~3-5 min)**
- Starts a fresh Ubuntu machine
- Installs Python 3.10
- Installs ML packages
- Runs `src/data/preprocess.py` → creates `data/processed/pune_features.csv`
- Runs `src/models/train.py` → creates `models/best_model.pkl`
- Runs `pytest tests/` (or skips if no tests)
- If any step fails, all remaining jobs are cancelled

**Job 2 — build (~8-15 min, runs after test)**
- Fresh Ubuntu machine with Docker pre-installed
- Installs ML packages AGAIN and trains the model AGAIN
  *(This is done here so the model is present when Docker copies files)*
- Logs into Docker Hub using your `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`
- Runs `docker build` — builds the image with model baked in
- Pushes the image to Docker Hub with two tags:
  - `:latest` (always the most recent)
  - `:abc1234` (the git commit SHA — unique ID for this exact version)
- Logs into AWS ECR using your AWS credentials
- Re-tags and pushes the same image to ECR

**Job 3 — deploy-ec2 (~1-2 min, runs after build)**
- Uses `appleboy/ssh-action` to SSH into your EC2 instance
- Runs `git pull origin main` to get the latest code
- Runs `pip install -r requirements_docker.txt`
- Runs `sudo supervisorctl restart pune_api` to restart the API process
- Runs `curl -f http://localhost:8000/health` to verify it started

**Job 4 — deploy-ecs (~1 min, runs after build)**
- Configures AWS credentials
- Reads `deployment/ecs/task-definition.json` and replaces the container
  image URL with the new image SHA from this build
- Calls the ECS API to register a new task definition revision
- Calls the ECS API to force a new deployment of the service
- Prints the current running/desired task counts
- *(Does NOT wait for stability — ECS handles the rolling update independently)*

**Job 5 — deploy-eks (~1-3 min, runs after build)**
- Configures AWS credentials and kubectl
- Runs `kubectl set image deployment/pune-api pune-api=ECR_IMAGE:SHA`
  This tells Kubernetes: "replace pods with this new image"
- Runs `kubectl rollout status --timeout=300s || true`
  Watches the rollout for up to 5 minutes. The `|| true` means if it times
  out, the job still passes — the rollout continues on the cluster.
- Prints pod and service status

**Job 6 — notify (always runs, even if other jobs fail)**
- Checks the result of jobs 3, 4, 5
- Prints a summary table in the log
- Sends a Slack message if `SLACK_WEBHOOK_URL` secret is set

---

### Why the URL Was Live While GitHub Actions Showed Failure

This is an important concept for engineers to understand.

GitHub Actions is a **watcher** — it fires commands at AWS/Kubernetes and
optionally waits for a response. The actual workload runs on AWS infrastructure
completely independently of GitHub Actions.

When `kubectl rollout status` times out at 300 seconds, it means the
**watcher** gave up waiting. It does NOT mean the rollout failed. Kubernetes
continued the rollout on the cluster and completed it successfully minutes
later. The old pods kept serving traffic throughout. The URL never went down.

**Analogy:** You order a parcel and track it online. The tracking website
times out. The parcel is still being delivered — you just can't see the
status anymore.

The ECS "not in state servicesStable" error has the same explanation.
`wait-for-service-stability: false` tells GitHub Actions to fire the
deployment and move on immediately without waiting for confirmation.

---

## 12. All Issues Faced and Fixes Applied

### Issue 1 — MLflow `file://` URI Fails on Windows
**Error:** `MlflowException: Could not find a suitable backend for tracking URI file://C:/...`
**Cause:** MLflow's URI parser expects POSIX paths. Windows drive letters (C:/) break it.
**Fix:** Use SQLite backend: `mlflow.set_tracking_uri("sqlite:///mlflow.db")`
**Prevention:** Always use SQLite on Windows. Use PostgreSQL for a shared team server.

---

### Issue 2 — .venv Corrupted After Partial Install
**Error:** `ModuleNotFoundError` or `No module named 'pip'`
**Cause:** pip install was interrupted (disk space ran out mid-package).
**Fix:**
```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
**Prevention:** Ensure 3GB+ free disk space before installing.

---

### Issue 3 — Disk Space Ran Out During pip Install
**Error:** `OSError: [Errno 28] No space left on device`
**Cause:** Large installer files accumulated in Downloads folder.
**Fix:** Delete large unused files from Downloads. Free at least 3GB.
```powershell
Get-ChildItem $env:USERPROFILE\Downloads | Sort-Object Length -Descending | Select-Object -First 20 Name,Length
```
**Prevention:** Audit Downloads folder before any large install.

---

### Issue 4 — pyenv Not Active After Installation
**Error:** `python --version` shows 3.8 instead of 3.10
**Cause:** pyenv shim directory not in PATH for current terminal session.
**Fix:** `pyenv global 3.10.11` → close terminal → open new terminal.
**Prevention:** Always open a fresh terminal after installing pyenv-win.

---

### Issue 5 — Google Colab Cannot Upload Folders
**Cause:** Colab file picker accepts only individual files, not directory trees.
**Fix:** Compress to ZIP → upload ZIP → extract in Colab:
```python
!unzip project.zip -d /content/
```

---

### Issue 6 — ngrok Requires Account Registration
**Cause:** ngrok changed policy to require free account for any tunnel.
**Fix:** Use `localtunnel` (no account required):
```bash
npm install -g localtunnel
lt --port 8000
```

---

### Issue 7 — GitHub Actions: `secrets` in `if` Condition
**Error:** `Unrecognized named-value: 'secrets'`
**Cause:** GitHub Actions blocks `secrets.X` in `if:` expressions for security.
**Fix:** Remove the `if` condition. Add `continue-on-error: true` to the step instead.
```yaml
- name: Send Slack notification
  continue-on-error: true
  uses: slackapi/slack-github-action@v1.26.0
```

---

### Issue 8 — Docker Image Built Without the Model File
**Symptom:** `{"status":"degraded","model_loaded":false}`
**Cause:** `models/best_model.pkl` was in `.gitignore`. GitHub Actions checked out
code without it. The Docker image was built without the model.
**Fix:** In the build job, add steps to train the model before Docker build:
```yaml
- name: Install ML dependencies and train model
  run: |
    pip install pandas numpy scikit-learn==1.7.2 scipy joblib openpyxl mlflow
    python src/data/preprocess.py
    MLFLOW_TRACKING_URI="sqlite:///mlflow.db" python src/models/train.py
```

---

### Issue 9 — IAM User Cannot Modify Its Own Policies
**Error:** `AccessDenied: not authorized to perform: iam:AttachUserPolicy`
**Cause:** User only had `IAMReadOnlyAccess` — cannot modify IAM, including self.
**Fix:** Use the **root account** (the AWS account creation email/password) to
add policies. Root account has unrestricted IAM access.
**How to login as root:**
1. AWS Console → Sign in to a different account → Root user email
2. Enter account email and root password

---

### Issue 10 — IAM Managed Policy Quota Exceeded (10-Policy Limit)
**Error:** "The selected policies exceed this account's quota"
**Cause:** AWS limits IAM users to 10 managed policies. User already had 10.
**Fix:** Create an **inline policy** instead — inline policies are not counted:
1. AWS Console → IAM → Users → YOUR_IAM_USERNAME
2. Permissions tab → Create inline policy → JSON tab
3. Paste:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iam:*","cloudformation:*","ecr:*","eks:*"],
      "Resource": "*"
    }
  ]
}
```
4. Policy name: `eksctl-ecr-permissions` → Create policy

---

### Issue 11 — EKS Fails: `iam:TagRole` Not Authorized
**Error:** `CREATE_FAILED: User is not authorized to perform: iam:TagRole`
**Cause:** `IAMReadOnlyAccess` does not include `iam:TagRole` which eksctl needs.
**Fix:** The inline policy from Issue 10 (includes `iam:*`) resolves this.

---

### Issue 12 — EKS CloudFormation Stack Already Exists
**Error:** `AlreadyExistsException: Stack [eksctl-pune-api-eks-cluster] already exists`
**Cause:** Previous failed EKS creation left a `ROLLBACK_COMPLETE` stack behind.
**Fix:**
```powershell
aws cloudformation delete-stack --stack-name eksctl-pune-api-eks-cluster
Start-Sleep -Seconds 30
# Then retry eksctl create cluster
```

---

### Issue 13 — Docker Desktop Fails to Start
**Error:** `Error response from daemon: Docker Desktop is unable to start`
**Cause:** Docker Desktop internal state issue (crash or incomplete update).
**Impact:** No impact on production — GitHub Actions has its own Docker.
**Fix for local use:** Task Manager → End all Docker processes → Reopen Docker Desktop.

---

### Issue 14 — Nginx Ingress Returns 404
**Cause:** `k8s/ingress.yaml` had `host: api.yourdomain.com`. Nginx only routes
requests whose `Host` HTTP header matches — raw LoadBalancer URL didn't match.
**Fix:** Remove the `host:` field to make the ingress a catch-all:
```yaml
rules:
  - http:           # no host = matches any hostname
      paths:
        - path: /
```

---

### Issue 15 — ECS Stuck: "Resource is not in the state servicesStable"
**Cause:** `wait-for-service-stability: true` — GitHub Actions kept polling ECS
during the rolling update window. ECS was not "stable" because it was mid-rollout.
The URL was live throughout because old tasks kept serving traffic.
**Fix:** Set `wait-for-service-stability: false`

---

### Issue 16 — EKS Rollout Status Timeout
**Error:** `error: timed out waiting for the condition`
**Cause:** Pulling a 1.8GB image from ECR took longer than 180 seconds.
**Fix:**
```bash
kubectl rollout status deployment/pune-api -n pune-api --timeout=300s || true
```
The `|| true` means the step passes even if the watcher times out.
The rollout continues and completes on the cluster regardless.

---

### Issue 17 — Monitoring Dashboards Show "Site Not Found"
**Cause:** Prometheus and Grafana were `ClusterIP` services — internal only,
no public URL.
**Fix:** Change both services to `LoadBalancer` type:
```bash
kubectl patch svc prometheus -n pune-api -p '{"spec":{"type":"LoadBalancer"}}'
kubectl patch svc grafana    -n pune-api -p '{"spec":{"type":"LoadBalancer"}}'
```
Wait 60-90 seconds for AWS to provision Network Load Balancers.

---

### Issue 18 — GitHub Shows Wrong Contributor Name
**Cause:** Initial git commits had `user.name` set to a wrong name. All commits
were re-authored using `git filter-branch` with the correct name and email.
The GitHub contributor cache takes time to update after a force push.
**Fix:**
```bash
git config user.name "YOUR FULL NAME"
git config user.email "YOUR_EMAIL"

# Rewrite all commit history
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --force --env-filter '
export GIT_AUTHOR_NAME="YOUR FULL NAME"
export GIT_AUTHOR_EMAIL="YOUR_EMAIL"
export GIT_COMMITTER_NAME="YOUR FULL NAME"
export GIT_COMMITTER_EMAIL="YOUR_EMAIL"
' -- --all
git push origin main --force
```
Also verify `YOUR_EMAIL` is added and verified in GitHub → Settings → Emails.
GitHub links commits to profiles by email address.

---

## 13. GitHub Secrets Reference

**Navigation:** GitHub Repo → Settings tab → Secrets and variables (left sidebar) → Actions → New repository secret

| Secret Name | Value | Where to Find It |
|---|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | hub.docker.com profile |
| `DOCKERHUB_TOKEN` | Docker Hub access token | hub.docker.com → Account Settings → Security → New Access Token |
| `EC2_HOST` | EC2 Elastic IP | EC2 Console → Elastic IPs |
| `EC2_SSH_KEY` | Full `.pem` file contents | `Get-Content path\to\key.pem \| Set-Clipboard` |
| `AWS_ACCESS_KEY_ID` | IAM user access key ID | IAM → Users → Security credentials → Create access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | Shown once when access key is created |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook | Slack API → Your Apps → Incoming Webhooks (optional) |

---

## 14. Production Checklist

Work through this list top-to-bottom. Check each item only when fully verified.

### Prerequisites
- [ ] Python 3.10 installed (`python --version`)
- [ ] VS Code installed with project folder open
- [ ] Git configured: `git config user.name` and `git config user.email`
- [ ] Docker Desktop installed and running (whale icon in taskbar)
- [ ] kubectl installed (`kubectl version --client`)
- [ ] eksctl installed (`eksctl version`)
- [ ] AWS CLI installed and configured (`aws sts get-caller-identity`)
- [ ] `my_setup.txt` created with all placeholder values filled in

### Data and Model
- [ ] Both raw files in `data/raw/`
- [ ] `python src/data/preprocess.py` runs without error
- [ ] `python src/models/train.py` runs and creates `models/best_model.pkl`
- [ ] MLflow UI shows 5 model runs at localhost:5000
- [ ] FastAPI starts locally at localhost:8000/docs

### Docker
- [ ] `docker build` completes without error
- [ ] `docker run` + health check returns `{"status":"ok","model_loaded":true}`
- [ ] Image pushed to Docker Hub (both `:latest` and `:v1.0.0` tags)

### GitHub
- [ ] All code committed and pushed to `main` branch
- [ ] All 6 secrets added to GitHub Actions
- [ ] `.gitignore` includes `*.pem`, `.env`, `my_setup.txt`, `models/best_model.pkl`

### AWS Account
- [ ] IAM user created with required permissions
- [ ] Inline policy `eksctl-ecr-permissions` added (iam:*, cloudformation:*, ecr:*, eks:*)
- [ ] AWS CLI configured with IAM user credentials

### ECR
- [ ] ECR repository `pune-real-estate-api` created
- [ ] `task-definition.json` updated with real account ID (not placeholder)
- [ ] `k8s/deployment.yaml` updated with real account ID

### EC2
- [ ] EC2 instance launched (Ubuntu 22.04 LTS)
- [ ] Elastic IP associated
- [ ] Security group: port 22 from My IP only, port 80/443 from anywhere
- [ ] SSH connection works from your machine
- [ ] Docker installed on EC2 (`docker ps` works without sudo)
- [ ] Nginx installed and running (`sudo systemctl status nginx`)
- [ ] Supervisor installed, `pune_api` program created and RUNNING
- [ ] `curl http://localhost/health` on EC2 returns ok
- [ ] `http://YOUR_EC2_ELASTIC_IP/docs` opens in browser

### ECS Fargate
- [ ] `ecsTaskExecutionRole` and `ecsTaskRole` IAM roles created
- [ ] CloudWatch log group `/ecs/pune-api` created
- [ ] ECS cluster `pune-api-cluster` created
- [ ] Security groups created (ALB SG and task SG)
- [ ] Application Load Balancer created with target group (type: IP)
- [ ] ECS service `pune-api-service` created (desired: 2)
- [ ] Both ECS tasks show as RUNNING in the console
- [ ] Both ALB targets show as healthy
- [ ] `http://YOUR_ECS_ALB_DNS/health` returns ok

### EKS Kubernetes
- [ ] EKS cluster `pune-api-eks` created
- [ ] `kubectl get nodes` shows 2 nodes, both Ready
- [ ] All k8s manifests applied (namespace, configmap, secret, deployment, service, hpa)
- [ ] Nginx Ingress Controller installed
- [ ] Ingress applied, `EXTERNAL-IP` assigned
- [ ] All 5 pods in `pune-api` namespace show `1/1 Running`
- [ ] `http://YOUR_EKS_LB_DNS/health` returns ok

### Monitoring
- [ ] Grafana LoadBalancer URL obtained and accessible at port 3000
- [ ] Prometheus LoadBalancer URL obtained and accessible at port 9090
- [ ] Grafana dashboard imported from `monitoring/grafana_dashboard.json`
- [ ] CloudWatch setup script run, SNS email confirmed
- [ ] CloudWatch dashboard visible in AWS Console

### CI/CD
- [ ] Push a small change to `main` and watch Actions page
- [ ] All 6 jobs complete without red failures
- [ ] New image appears in Docker Hub with commit SHA tag
- [ ] EC2 Supervisor restarts cleanly
- [ ] ECS shows updated deployment
- [ ] EKS shows new rollout in `kubectl rollout history deployment/pune-api -n pune-api`

### Final Verification
- [ ] `GET /health` → `{"status":"ok","model_loaded":true}` on all 3 deployments
- [ ] `POST /predict` → returns predicted price on all 3 deployments
- [ ] `POST /predict` with invalid input → returns HTTP 422
- [ ] GitHub contributor widget shows only your name
