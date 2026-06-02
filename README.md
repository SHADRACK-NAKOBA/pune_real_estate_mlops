# 🏘️ Pune Real Estate — End-to-End MLOps Pipeline

> **Predict property prices in Pune** using a full ML stack:  
> Data Cleaning → Feature Engineering → MLflow → PyCaret → FastAPI → Docker → AWS EC2 → DVC

---

## 📁 Project Structure

```
pune_real_estate/
├── data/
│   ├── raw/                        # Your original files go here
│   └── processed/                  # Generated: pune_features.csv
├── models/                         # Generated: best_model.pkl
├── notebooks/
│   └── Pune_Real_Estate_EndToEnd_ML.ipynb  ← OPEN IN COLAB
├── src/
│   ├── data/
│   │   └── preprocess.py           # Step 1: clean + feature engineering
│   ├── models/
│   │   ├── train.py                # Step 2: train + MLflow tracking
│   │   └── pycaret_train.py        # Step 2b: AutoML with PyCaret
│   └── api/
│       ├── fastapi_app.py          # Step 3: FastAPI deployment
│       └── flask_app.py            # Step 3b: Flask alternative
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   └── ec2/
│       └── deploy.sh               # AWS EC2 one-click deploy
├── scripts/
│   └── setup_mlflow.py             # Launch MLflow UI
├── dvc.yaml                        # DVC pipeline stages
└── requirements.txt
```

---

## ⬆️ HOW TO UPLOAD FILES TO GOOGLE COLAB (Your Question!)

You cannot drag-and-drop `.xlsx` files to the left panel in Colab reliably.
**Use the notebook's built-in upload cell instead:**

### Option A — Use the Notebook (Recommended)
1. Open `notebooks/Pune_Real_Estate_EndToEnd_ML.ipynb` in Colab
2. Run **Cell 1** — it opens a file picker dialog
3. Select **both files** at once:
   - `Pune_Real_Estate_Data__1_.xlsx`
   - `data_cleaned__1_.csv`
4. They get saved to `/content/data/raw/` automatically

### Option B — Manual Upload via Colab Sidebar
1. Open Colab → click the **📁 Files** icon on the left
2. Click **Upload** (cloud icon with ↑)
3. Select your files — they land in `/content/`
4. In a code cell: `!mv *.xlsx *.csv /content/data/raw/`

### Option C — Upload to Google Drive, then mount
```python
from google.colab import drive
drive.mount('/content/drive')
# Then copy your files from Drive to /content/data/raw/
import shutil
shutil.copy('/content/drive/MyDrive/Pune_Real_Estate_Data__1_.xlsx', '/content/data/raw/')
shutil.copy('/content/drive/MyDrive/data_cleaned__1_.csv', '/content/data/raw/')
```

### Option D — Direct URL (if files are on GitHub)
```python
!wget -O /content/data/raw/Pune_Real_Estate_Data.xlsx \
  "https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/data/raw/Pune_Real_Estate_Data.xlsx"
```

---

## 🚀 Quick Start (Local)

### 1. Setup
```bash
git clone https://github.com/YOUR_USERNAME/pune_real_estate.git
cd pune_real_estate
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the full pipeline
```bash
# Step 1: Clean data & engineer features
python src/data/preprocess.py

# Step 2: Train all models (logged to MLflow)
python src/models/train.py

# Step 2b: AutoML with PyCaret (optional, takes ~3 min)
python src/models/pycaret_train.py

# Step 3a: Start FastAPI
uvicorn src.api.fastapi_app:app --reload --port 8000
# Open: http://localhost:8000/docs

# Step 3b: Or start Flask
python src/api/flask_app.py
# Open: http://localhost:5000

# Step 4: Launch MLflow Dashboard
python scripts/setup_mlflow.py
# Open: http://localhost:5000 (MLflow UI)
```

### 3. Use DVC pipeline (run all steps in order)
```bash
dvc init
dvc repro         # runs preprocess → train → pycaret in order
dvc dag           # visualise the pipeline DAG
```

---

## 🌐 Test the API

```bash
# Health check
curl http://localhost:8000/health

# Single prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "area_sqft": 1000,
    "township_area": 80,
    "amenity_score": 5,
    "has_clubhouse": 1, "has_school": 1, "has_hospital": 1,
    "has_mall": 0,      "has_park": 1,  "has_pool": 1, "has_gym": 1,
    "location": 3, "sub_area": 5, "property_type": 1, "company_name": 2
  }'
```

**Response:**
```json
{
  "predicted_price_lakhs": 87.4,
  "predicted_price_millions": 8.74,
  "price_per_sqft_lakhs": 0.0874,
  "model_version": "1.0.0"
}
```

---

## 🐳 Docker Deployment (Local)

```bash
cd deployment/docker
docker-compose up --build
# API     → http://localhost:8000/docs
# MLflow  → http://localhost:5001
```

---

## ☁️ AWS EC2 Deployment

### Prerequisites
- AWS account with an EC2 instance (Ubuntu 22.04, t2.medium or larger)
- Security group with ports 22, 80, 8000 open

### Steps
```bash
# 1. SSH into your EC2 instance
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>

# 2. Upload deploy script (from your local machine)
scp -i your-key.pem deployment/ec2/deploy.sh ubuntu@<EC2_PUBLIC_IP>:~/

# 3. On EC2: make executable and run
chmod +x deploy.sh
./deploy.sh
# → API live at http://<EC2_PUBLIC_IP>/docs
```

### EC2 Security Group Rules
| Type  | Port | Source    |
|-------|------|-----------|
| SSH   | 22   | Your IP   |
| HTTP  | 80   | 0.0.0.0/0 |
| Custom| 8000 | 0.0.0.0/0 |
| Custom| 5001 | Your IP   |

---

## 📊 MLflow Experiment Tracking

```python
import mlflow
mlflow.set_tracking_uri("file://./mlflow_runs")
# View all runs:
runs = mlflow.search_runs(experiment_names=["pune_real_estate_price_prediction"])
print(runs[["run_id","params.model","metrics.test_r2","metrics.test_mae"]])
```

---

## 🔢 Feature Reference (for API calls)

| Feature         | Type  | Description                        |
|-----------------|-------|------------------------------------|
| `area_sqft`     | float | Property area in sq ft             |
| `township_area` | float | Total township area in acres       |
| `amenity_score` | int   | Count of amenities (0–7)           |
| `has_*`         | 0/1   | Clubhouse, school, hospital, etc.  |
| `location`      | int   | Encoded location (0–N)             |
| `sub_area`      | int   | Encoded sub-area                   |
| `property_type` | int   | Encoded: 0=Apartment, 1=Villa, etc |
| `company_name`  | int   | Encoded builder/company            |

---

## 🛠️ Tech Stack

| Layer           | Tool                              |
|-----------------|-----------------------------------|
| Data            | Pandas, NumPy, OpenPyXL           |
| ML              | Scikit-learn, PyCaret             |
| Experiment Tracking | MLflow                        |
| Data Versioning | DVC                               |
| API (primary)   | FastAPI + Uvicorn                 |
| API (alt)       | Flask                             |
| Containerisation| Docker, Docker Compose            |
| Cloud           | AWS EC2 + Nginx                   |
| Notebook        | Google Colab                      |
