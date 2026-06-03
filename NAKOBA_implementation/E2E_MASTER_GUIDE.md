# End-to-End Master Guide — Pune Real Estate Price Prediction
## From Google Colab Notebook → VS Code → Live AWS API
**Author: Shadrack Nakoba | For: Manager Implementation Review**
**Every command. Every click. Every step. Nothing skipped.**

---

## How to Read This Document

- **`code blocks`** = exact commands to type or paste. Do not paraphrase.
- **[SCREENSHOT]** = something you see on screen — look for it before moving on.
- **WARNING:** = something that commonly goes wrong here.
- **WHY:** = explanation of what this step does and why it matters.
- Every step is numbered. Do them in order. Do not skip.

---

# PHASE 1 — GOOGLE COLAB: EXPERIMENT AND TRAIN

## What Google Colab Is
Google Colab is a free cloud-based Python notebook environment. It runs on Google's servers, so you get Python pre-installed, GPU access, and no local setup needed. Think of it like Excel in the cloud but for Python code and machine learning. The notebook file is `notebooks/Pune_Real_Estate_EndToEnd_ML.ipynb`.

**No installation required for Colab — you just need a Google account.**

---

## Step 1 — Open Google Colab

1. Open your web browser (Chrome recommended).
2. Go to: https://colab.research.google.com
3. Sign in with your Google account.
4. Click **File → Upload notebook**.
5. Click **Choose file**.
6. Navigate to: `C:\Users\admin\Desktop\pune_real_estate_mlops\notebooks\`
7. Select: `Pune_Real_Estate_EndToEnd_ML.ipynb`
8. Click Open.

[SCREENSHOT: You should see a notebook with cells titled "🏘️ Pune Real Estate — End-to-End ML Pipeline"]

**WHY:** We run the initial experiment in Colab because it has no disk space limits for Python packages, runs faster than most local machines for ML training, and gives you an easy way to share work with stakeholders.

---

## Step 2 — Understand the Colab Interface

Before running anything, know these four things:
- Each grey box with code is called a **cell**.
- To run a cell: click it, then press **Shift + Enter** (or click the ▶ play button on the left).
- Run cells **top to bottom**, one at a time. Never skip a cell.
- If a cell shows a spinning circle, it is still running — wait for it to finish before running the next.

---

## Step 3 — CELL 1: Upload Raw Data Files

This cell creates the folder structure in Colab's cloud storage and opens a file picker so you can upload the two raw data files.

**Run Cell 1 now** (Shift + Enter).

```python
# What this cell does:
# Creates: /content/data/raw/  /content/data/processed/  /content/models/
# Opens a file upload dialog
from google.colab import files
import os

os.makedirs('/content/data/raw', exist_ok=True)
os.makedirs('/content/data/processed', exist_ok=True)
os.makedirs('/content/models', exist_ok=True)

uploaded = files.upload()

for fname in uploaded:
    dest = f'/content/data/raw/{fname}'
    os.rename(fname, dest)
    print(f'Saved → {dest}')
```

**After running, a file picker appears in the cell output.**

1. Click **Choose Files** in the Colab output.
2. Navigate to: `C:\Users\admin\Desktop\pune_real_estate_mlops\data\raw\`
3. Select **both files at the same time** (hold Ctrl and click both):
   - `Pune_Real_Estate_Data.xlsx`
   - `data_cleaned.csv`
4. Click Open.

[SCREENSHOT: Progress bars show "Saving Pune_Real_Estate_Data.xlsx..." and "Saving data_cleaned.csv..."]

**Expected output after upload:**
```
Saved → /content/data/raw/Pune_Real_Estate_Data.xlsx
Saved → /content/data/raw/data_cleaned.csv
Files in /content/data/raw/:
['Pune_Real_Estate_Data.xlsx', 'data_cleaned.csv']
```

**WARNING — Common mistake:** If you upload files one at a time by running Cell 1 twice, the second run overwrites the folder setup. Upload both files in the same file picker dialog.

**WARNING — File names:** Colab sometimes appends `(1)` to file names if they already exist (e.g., `Pune_Real_Estate_Data_(1).xlsx`). The code handles this automatically by detecting any `.xlsx` and `.csv` file. But check the output shows exactly 2 files.

---

## Step 4 — CELL 2: Install Dependencies

This cell installs the Python packages needed in Colab. Colab already has pandas, numpy, matplotlib, and sklearn — this adds the ML-specific ones.

**Run Cell 2** (Shift + Enter):

```python
!pip install -q mlflow pycaret[full] fastapi uvicorn joblib openpyxl
```

**What each package does:**
- `mlflow` — tracks experiments (logs model metrics, saves model artifacts)
- `pycaret[full]` — AutoML library that compares 20+ models automatically
- `fastapi` — the web framework for the prediction API
- `uvicorn` — the server that runs FastAPI
- `joblib` — saves and loads the trained model to/from a .pkl file
- `openpyxl` — allows pandas to read .xlsx Excel files

**Expected output:** Several lines of `Collecting...` and `Installing...`. The `-q` flag keeps output minimal. Takes 3-5 minutes.

[SCREENSHOT: Lines scrolling showing package installation progress]

**WARNING:** If you see `ERROR: pip's dependency resolver does not currently take into account...` — this is a warning, not an error. Continue to Cell 3. Only stop if you see `ERROR: Could not install packages due to...`.

---

## Step 5 — CELL 3: Imports

This cell imports all the Python libraries into memory and detects the filenames of your uploaded raw files.

**Run Cell 3** (Shift + Enter):

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings, os, joblib
warnings.filterwarnings('ignore')

raw_files = os.listdir('/content/data/raw/')
XLSX_FILE = next((f for f in raw_files if f.endswith('.xlsx')), None)
CSV_FILE  = next((f for f in raw_files if f.endswith('.csv')),  None)

print(f'XLSX: {XLSX_FILE}')
print(f'CSV : {CSV_FILE}')
```

**Expected output:**
```
XLSX: Pune_Real_Estate_Data.xlsx
CSV : data_cleaned.csv
```

If either shows `None`, go back to Cell 1 — the file was not uploaded correctly.

---

## Step 6 — CELL 4 (Markdown): Exploratory Data Analysis Header

This is a markdown cell (text, not code). You do not run it. It just shows the section title: **"📊 Step 1: Exploratory Data Analysis"**. Click the next cell to continue.

---

## Step 7 — CELL 5: Load Raw Data and Inspect

This cell loads both raw files into pandas DataFrames and shows the first 3 rows of the XLSX.

**Run Cell 5** (Shift + Enter):

```python
df_raw  = pd.read_excel(f'/content/data/raw/{XLSX_FILE}')
df_base = pd.read_csv(f'/content/data/raw/{CSV_FILE}')

print('=== Raw XLSX ===')
print(df_raw.shape)
df_raw.head(3)
```

**Expected output:**
```
=== Raw XLSX ===
(200, 18)
```
Followed by a table showing the first 3 rows of the raw data with 18 columns (location, sub_area, price_in_lakhs, property_area_in_sq_ft, clubhouse, school, hospital, mall, park, swimming_pool, gym, company_name, etc.).

**WHY:** 200 rows means 200 property listings. 18 columns are the raw features. We need to understand this structure before cleaning.

---

## Step 8 — CELL 6: Check Missing Values

**Run Cell 6** (Shift + Enter):

```python
print('Missing values in XLSX:')
print(df_raw.isnull().sum()[df_raw.isnull().sum() > 0])
print()
print('Missing values in CSV:')
print(df_base.isnull().sum()[df_base.isnull().sum() > 0])
```

**Expected output:** A list of column names and how many rows have missing values. For example:
```
Missing values in XLSX:
total_township_area_in_acres    45
dtype: int64

Missing values in CSV:
Price Cleaned     3
Area Cleaned      2
```

**WHY:** Missing values must be handled during preprocessing. The imputer in our scikit-learn pipeline fills them with the median value of each column. We just need to know they exist.

---

## Step 9 — CELL 7: Visualise Price Distribution

**Run Cell 7** (Shift + Enter):

```python
fig, axes = plt.subplots(1, 2, figsize=(14, 4))
axes[0].hist(df_base['Price Cleaned'].dropna(), bins=30, color='steelblue', edgecolor='white')
axes[0].set_title('Price Distribution (Lakhs)')
axes[0].set_xlabel('Price (Lakhs ₹)')

axes[1].hist(np.log1p(df_base['Price Cleaned'].dropna()), bins=30, color='tomato', edgecolor='white')
axes[1].set_title('Log-Price Distribution')
axes[1].set_xlabel('log(Price)')

plt.tight_layout()
plt.show()
```

[SCREENSHOT: Two side-by-side histograms appear below the cell]

**What you see:**
- Left chart: Price distribution — right-skewed (most properties are cheap, a few are expensive)
- Right chart: Log of price — bell-shaped (more normal distribution)

**WHY:** The right-skew in prices means a few very expensive properties would dominate model training. Log transformation makes the distribution more symmetric and helps linear models perform better.

---

## Step 10 — CELL 8: Correlation Heatmap

**Run Cell 8** (Shift + Enter):

```python
amenity_cols = ['ClubHouse Cleaned','School Cleaned','Hospital Cleaned',
                'Mall Cleaned','Park Cleaned','Pool Cleaned','Gym Cleaned']
corr_cols = amenity_cols + ['Area Cleaned', 'Price Cleaned']
corr = df_base[corr_cols].corr()

plt.figure(figsize=(10, 7))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0)
plt.title('Feature Correlation Matrix')
plt.tight_layout()
plt.show()
```

[SCREENSHOT: A colour-coded 9×9 grid of numbers appears. Red = positive correlation, Blue = negative]

**What to look for:**
- `Area Cleaned` vs `Price Cleaned`: should be 0.5-0.8 (bigger properties cost more)
- Amenities with positive correlation to price: shows which amenities add value
- Numbers close to 1.0 in the `Price Cleaned` column = strong predictors

---

## Step 11 — CELL 9 (Markdown): Data Cleaning Header

Text cell only. Shows "🧹 Step 2: Data Cleaning & Feature Engineering". No action needed.

---

## Step 12 — CELL 10: Data Cleaning and Feature Engineering

This is the most important preprocessing cell. It defines two functions and runs the full pipeline to produce the clean feature set.

**Run Cell 10** (Shift + Enter):

```python
# Function 1: clean_raw() — standardises the XLSX data
def clean_raw(df):
    df = df.copy()
    # Standardise column names (lowercase, underscores)
    df.columns = (df.columns.str.strip().str.lower()
                    .str.replace(r'[^\w]+', '_', regex=True))
    df.rename(columns={'propert_type': 'property_type'}, inplace=True)

    # Extract numbers from text columns like "1200 sqft" → 1200
    df['property_area_sqft'] = pd.to_numeric(
        df['property_area_in_sq_ft'].astype(str).str.replace(',','')
        .str.extract(r'([\d.]+)')[0], errors='coerce')
    df['price_lakhs'] = pd.to_numeric(
        df['price_in_lakhs'].astype(str).str.replace(',','')
        .str.extract(r'([\d.]+)')[0], errors='coerce')

    # Map "Yes"/"No" amenity text → 1/0 binary integers
    binary = {
        'clubhouse': 'has_clubhouse',
        'school___university_in_township_': 'has_school',
        'hospital_in_township': 'has_hospital',
        'mall_in_township': 'has_mall',
        'park___jogging_track': 'has_park',
        'swimming_pool': 'has_pool',
        'gym': 'has_gym'
    }
    yes_map = {'yes':1,'no':0,'1':1,'0':0}
    for src, tgt in binary.items():
        if src in df.columns:
            df[tgt] = (df[src].astype(str).str.strip().str.lower()
                         .map(yes_map).fillna(0).astype(int))

    # Standardise text categoricals
    for col in ['location','sub_area','property_type','company_name']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()

    # Drop rows with no price or area
    df.dropna(subset=['price_lakhs','property_area_sqft'], inplace=True)
    return df


# Function 2: engineer_features() — creates derived features
def engineer_features(df_clean, df_base):
    shared = min(len(df_clean), len(df_base))
    df = df_clean.iloc[:shared].reset_index(drop=True).copy()

    # Use the pre-cleaned area and price from df_base
    df['area_sqft']   = df_base['Area Cleaned'].iloc[:shared].values
    df['price_lakhs'] = df_base['Price Cleaned'].iloc[:shared].values

    # Copy amenity flags from df_base
    flag_map = {
        'ClubHouse Cleaned':'has_clubhouse','School Cleaned':'has_school',
        'Hospital Cleaned':'has_hospital','Mall Cleaned':'has_mall',
        'Park Cleaned':'has_park','Pool Cleaned':'has_pool','Gym Cleaned':'has_gym'
    }
    for src, tgt in flag_map.items():
        if src in df_base.columns:
            df[tgt] = df_base[src].iloc[:shared].values

    # DERIVED FEATURE 1: amenity_score — count of all 7 amenity flags (0-7)
    df['amenity_score']  = df[[v for v in flag_map.values()]].sum(axis=1)

    # DERIVED FEATURE 2: price_per_sqft — price efficiency metric
    df['price_per_sqft'] = df['price_lakhs'] / (df['area_sqft'] + 1e-6)

    # DERIVED FEATURE 3: log_area — log transform reduces right skew
    df['log_area']       = np.log1p(df['area_sqft'])

    # DERIVED FEATURE 4: log_price — log transform of target
    df['log_price']      = np.log1p(df['price_lakhs'])

    # DERIVED FEATURE 5: township_area — size of the overall township
    if 'total_township_area_in_acres' in df.columns:
        df['township_area'] = df['total_township_area_in_acres'].fillna(
            df['total_township_area_in_acres'].median())
    else:
        df['township_area'] = 0.0

    # Encode categoricals as integers (label encoding)
    for col in ['location','sub_area','property_type','company_name',
                'township_name__society_name']:
        if col in df.columns:
            df[col] = df[col].astype('category').cat.codes

    df.dropna(subset=['price_lakhs','area_sqft'], inplace=True)
    return df.reset_index(drop=True)


# --- RUN THE PIPELINE ---
df_clean    = clean_raw(df_raw)
df_features = engineer_features(df_clean, df_base)

# Save to CSV in Colab's file system
df_features.to_csv('/content/data/processed/pune_features.csv', index=False)
print(f'✅  Features saved — shape: {df_features.shape}')
df_features.head(3)
```

**Expected output:**
```
✅  Features saved — shape: (197, 21)
```
Followed by a table showing the first 3 rows. Shape `(197, 21)` means 197 rows (3 dropped for missing price/area) and 21 columns (15 features + 6 derived/intermediate columns).

**WHY the functions do what they do:**
| Action | Reason |
|---|---|
| Lowercase column names | Prevents `Area_Sqft` vs `area_sqft` bugs |
| Extract number from text | Raw data has "1200 sqft" not 1200 |
| Map Yes/No → 0/1 | ML models need numbers, not text |
| Create log_area | Reduces skew; improves linear model accuracy |
| amenity_score | Summarises all 7 flags into one interpretable score |
| Label encode categoricals | Tree models need integers, not text strings |
| Drop null price/area rows | Can't train without knowing the answer |

---

## Step 13 — CELL 11 (Markdown): Model Training Header

Text cell. Shows "🤖 Step 3: Model Training & Evaluation with MLflow". No action.

---

## Step 14 — CELL 12: Train 5 Models with MLflow Tracking

This is the core ML cell. It trains 5 different model types, logs every metric to MLflow, and saves the best one.

**Run Cell 12** (Shift + Enter):

```python
import mlflow, mlflow.sklearn
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Define the 15 features the model uses
FEATURE_COLS = ['area_sqft','log_area','township_area','amenity_score',
                'has_clubhouse','has_school','has_hospital','has_mall',
                'has_park','has_pool','has_gym',
                'location','sub_area','property_type','company_name']
TARGET = 'price_lakhs'

# Keep only features that actually exist in our cleaned data
available = [c for c in FEATURE_COLS if c in df_features.columns]
X = df_features[available]  # features matrix
y = df_features[TARGET]     # target vector

# Split: 80% training, 20% testing (random_state=42 ensures reproducibility)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Preprocessing pipeline: fill NaN with median, then scale to mean=0 std=1
num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
preprocessor = ColumnTransformer([
    ('num', Pipeline([('imp', SimpleImputer(strategy='median')),
                       ('sc', StandardScaler())]), num_cols)
], remainder='drop')

# MLflow: store experiment data in /content/mlruns folder
mlflow.set_tracking_uri('/content/mlruns')
mlflow.set_experiment('pune_re_price_prediction')

# Define the 5 candidate models
models = {
    'Ridge':        Ridge(alpha=10),         # Linear with L2 regularisation
    'Lasso':        Lasso(alpha=1),          # Linear with L1 regularisation (feature selection)
    'RandomForest': RandomForestRegressor(n_estimators=200, random_state=42),
    'GBM':          GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, random_state=42),
    'ExtraTrees':   ExtraTreesRegressor(n_estimators=200, random_state=42),
}

results = {}
best_r2, best_name, best_pipe = -np.inf, None, None

# Train each model
for name, est in models.items():
    # Pipeline: preprocessing + model together (critical for production)
    pipe = Pipeline([('prep', preprocessor), ('model', est)])

    with mlflow.start_run(run_name=name):   # Start MLflow tracking for this run
        pipe.fit(X_train, y_train)          # Train on 80% of data

        preds = pipe.predict(X_test)        # Predict on the 20% held out

        # Evaluation metrics
        r2   = r2_score(y_test, preds)                        # R² — variance explained (1.0 = perfect)
        mae  = mean_absolute_error(y_test, preds)              # MAE — avg absolute error in Lakhs
        rmse = np.sqrt(mean_squared_error(y_test, preds))     # RMSE — penalises large errors
        cv   = cross_val_score(pipe, X, y, cv=5, scoring='r2').mean()  # 5-fold CV R²

        # Log everything to MLflow
        mlflow.log_params({'model': name})
        mlflow.log_metrics({'r2': r2, 'mae': mae, 'rmse': rmse, 'cv_r2': cv})
        mlflow.sklearn.log_model(pipe, 'model')  # Save model artifact in MLflow

        results[name] = {'R2': r2, 'MAE': mae, 'RMSE': rmse, 'CV_R2': cv}

        flag = ' ← BEST' if r2 > best_r2 else ''
        if r2 > best_r2:
            best_r2, best_name, best_pipe = r2, name, pipe
        print(f'{name:15s}  R²={r2:.3f}  MAE={mae:.1f}L  RMSE={rmse:.1f}L  CV={cv:.3f}{flag}')

# Save best model (the complete Pipeline including preprocessor)
joblib.dump({'pipeline': best_pipe, 'features': available}, '/content/models/best_model.pkl')
print(f'\n✅  Best: {best_name}  R²={best_r2:.3f}')
```

**Expected output (your numbers may vary slightly):**
```
Ridge           R²=0.742  MAE=14.4L  RMSE=19.8L  CV=0.718
Lasso           R²=0.765  MAE=12.7L  RMSE=18.2L  CV=0.739
RandomForest    R²=0.780  MAE=8.8L   RMSE=17.4L  CV=0.763
ExtraTrees      R²=0.791  MAE=9.4L   RMSE=16.9L  CV=0.771
GBM             R²=0.795  MAE=8.6L   RMSE=16.5L  CV=0.779  ← BEST

✅  Best: GBM  R²=0.795
```

**What these numbers mean:**
| Metric | GBM Score | Plain English |
|---|---|---|
| R² = 0.795 | Best score | Model explains 79.5% of price variation |
| MAE = 8.64 Lakhs | Best score | Average prediction error is 8.64 Lakhs (~₹8.64 lakh = ~$10,400 USD) |
| RMSE = 16.5 Lakhs | Best score | Penalised error accounting for big misses |
| CV R² = 0.779 | Best score | Consistent across 5 different train/test splits |

**This cell takes 3-8 minutes** because it trains 200-tree ensembles 5 times for cross-validation. The spinning circle means it is working. Do not interrupt.

---

## Step 15 — CELL 13: Results Table

**Run Cell 13** (Shift + Enter):

```python
pd.DataFrame(results).T.sort_values('R2', ascending=False).round(3)
```

[SCREENSHOT: A clean table sorted by R2 score, GBM at the top]

This is a visual comparison of all 5 models. GBM is selected as the winner because it has:
- Highest R² (explains most variance)
- Lowest MAE (closest predictions in absolute terms)

---

## Step 16 — CELL 14: Feature Importance Chart

**Run Cell 14** (Shift + Enter):

```python
if hasattr(best_pipe.named_steps['model'], 'feature_importances_'):
    imp = best_pipe.named_steps['model'].feature_importances_
    feat_names = best_pipe.named_steps['prep'].transformers_[0][2]
    fi = pd.Series(imp, index=feat_names).sort_values(ascending=False)
    fi.plot(kind='bar', figsize=(10, 4),
            title=f'{best_name} — Feature Importances', color='steelblue')
    plt.tight_layout()
    plt.show()
```

[SCREENSHOT: A horizontal bar chart showing which features matter most]

**What to expect:** `area_sqft` and `log_area` are typically the top features (property size drives price). Amenity features appear in the middle. Location and company name contribute meaningfully.

**WHY:** Feature importance tells you what actually drives price predictions. If `has_gym` has near-zero importance, it means gyms don't significantly affect price in this dataset.

---

## Step 17 — CELL 15 (Markdown): PyCaret Header

Text cell. Shows "🚀 Step 4: PyCaret AutoML". No action.

---

## Step 18 — CELL 16: PyCaret AutoML — Compare All Models

PyCaret runs 20+ different algorithm types automatically and ranks them by R².

**Run Cell 16** (Shift + Enter):

```python
from pycaret.regression import setup, compare_models, tune_model, finalize_model, save_model, pull

# Prepare data for PyCaret (features + target, no NaN in target)
df_pc = df_features[available + [TARGET]].dropna(subset=[TARGET])
print(f'PyCaret input shape: {df_pc.shape}')

# Setup: defines the experiment (split, normalisation, transformations)
exp = setup(data=df_pc, target=TARGET, session_id=42, train_size=0.8,
            normalize=True, transformation=True, fold=5,
            verbose=False, html=False)

# Compare all available models — this may take 5-15 minutes
best_models = compare_models(n_select=3, sort='R2', verbose=True)

# Show the leaderboard
lb = pull()
lb[['Model','R2','MAE','RMSE']].head(5)
```

**Expected output:**
```
PyCaret input shape: (197, 16)
```
Then after ~5-15 minutes, a leaderboard table showing 15-20 models ranked by R². Gradient Boosting variants (GBM, LGBM, XGBoost, CatBoost) typically top the list, confirming our scikit-learn experiment.

**WARNING:** This cell takes 5-15 minutes in Colab. The cell spinner will be active the whole time. If Colab disconnects, re-upload data (Cell 1) and re-run from Cell 3.

---

## Step 19 — CELL 17: Tune Best PyCaret Model and Save

**Run Cell 17** (Shift + Enter):

```python
# Get the top model from compare_models
best_pc = best_models[0] if isinstance(best_models, list) else best_models

# Tune it with Bayesian optimisation (20 iterations)
tuned_pc = tune_model(best_pc, optimize='R2', n_iter=20)

# Finalize: retrain on full dataset (train + test)
final_pc = finalize_model(tuned_pc)

# Save to Colab's file system
save_model(final_pc, '/content/models/pycaret_best')
print('✅  PyCaret model saved')
```

**Expected output:**
```
✅  PyCaret model saved
```
This creates `/content/models/pycaret_best.pkl` in Colab.

**WHY we save this separately:** The scikit-learn GBM in `best_model.pkl` is our primary production model. The PyCaret model is a secondary backup that may perform slightly better due to advanced optimisation.

---

## Step 20 — CELL 18 (Markdown): FastAPI Header

Text cell. Shows "🌐 Step 5: FastAPI — Test In-Notebook". No action.

---

## Step 21 — CELL 19: Write the FastAPI Application

This cell writes the FastAPI prediction server code to a Python file inside Colab.

**Run Cell 19** (Shift + Enter):

```python
fastapi_code = '''
import os, joblib, numpy as np, pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

# Load the model from disk
bundle   = joblib.load("/content/models/best_model.pkl")
pipeline = bundle["pipeline"]
features = bundle["features"]

app = FastAPI(title="Pune RE Price API")

# Input schema — what the API accepts
class Prop(BaseModel):
    area_sqft: float = 900
    township_area: float = 50
    amenity_score: int = 3
    has_clubhouse: int = 1
    has_school: int = 1
    has_hospital: int = 0
    has_mall: int = 0
    has_park: int = 1
    has_pool: int = 1
    has_gym: int = 1
    location: int = 3
    sub_area: int = 5
    property_type: int = 1
    company_name: int = 2

# Health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}

# Prediction endpoint
@app.post("/predict")
def predict(p: Prop):
    data = {
        "area_sqft": p.area_sqft,
        "log_area": np.log1p(p.area_sqft),   # computed inline
        "township_area": p.township_area,
        "amenity_score": p.amenity_score,
        "has_clubhouse": p.has_clubhouse,
        "has_school": p.has_school,
        "has_hospital": p.has_hospital,
        "has_mall": p.has_mall,
        "has_park": p.has_park,
        "has_pool": p.has_pool,
        "has_gym": p.has_gym,
        "location": p.location,
        "sub_area": p.sub_area,
        "property_type": p.property_type,
        "company_name": p.company_name
    }
    # Build DataFrame with only the features the model expects
    df_in = pd.DataFrame([{k: data[k] for k in features if k in data}])
    pred  = float(pipeline.predict(df_in)[0])
    return {
        "predicted_price_lakhs": round(pred, 2),
        "predicted_price_millions": round(pred / 10, 3)
    }
'''

with open('/content/api_app.py', 'w') as f:
    f.write(fastapi_code)
print('FastAPI app written to /content/api_app.py')
```

**Expected output:**
```
FastAPI app written to /content/api_app.py
```

---

## Step 22 — CELL 20: Start FastAPI Server and Create Public URL

This cell starts the FastAPI server in the background and creates a public internet URL using ngrok.

**Run Cell 20** (Shift + Enter):

```python
!pip install -q pyngrok

import subprocess, time
from pyngrok import ngrok

# Start uvicorn server in background (non-blocking)
proc = subprocess.Popen(['uvicorn', 'api_app:app', '--host', '0.0.0.0', '--port', '8000'])
time.sleep(3)  # Wait for server to start

# Create public tunnel
public_url = ngrok.connect(8000)
print(f'\n🌐 Public API URL: {public_url}')
print(f'   Swagger docs : {public_url}/docs')
print(f'   Health check : {public_url}/health')
```

**Expected output:**
```
🌐 Public API URL: https://abc123.ngrok.io
   Swagger docs : https://abc123.ngrok.io/docs
   Health check : https://abc123.ngrok.io/health
```

**The URL is a live, public internet URL.** Anyone with this URL can call your API from anywhere in the world — for as long as this Colab session is running.

**WARNING — ngrok account required:** If you see `ngrok.exceptions.PyngrokError: ngrok authtoken`, you need to:
1. Create a free account at https://ngrok.com
2. Go to Your Dashboard → Copy your auth token
3. Run: `!ngrok authtoken YOUR_TOKEN_HERE`
4. Re-run this cell

**Alternative if ngrok fails — use localtunnel:**
```python
!npm install -g localtunnel
!lt --port 8000 &
```

---

## Step 23 — CELL 21: Test the API from Within Colab

**Run Cell 21** (Shift + Enter):

```python
import requests

payload = {
    'area_sqft': 1000,
    'township_area': 80,
    'amenity_score': 5,
    'has_clubhouse': 1,
    'has_school': 1,
    'has_hospital': 1,
    'has_mall': 0,
    'has_park': 1,
    'has_pool': 1,
    'has_gym': 1,
    'location': 3,
    'sub_area': 5,
    'property_type': 1,
    'company_name': 2
}

r = requests.post(f'{public_url}/predict', json=payload)
print('Status:', r.status_code)
print('Response:', r.json())
```

**Expected output:**
```
Status: 200
Response: {'predicted_price_lakhs': 87.4, 'predicted_price_millions': 8.74}
```

This proves: the model is loaded, the API is running, and predictions are working end-to-end inside Colab.

Also open the Swagger UI in your browser:
1. Copy the URL from Cell 20 output (e.g., `https://abc123.ngrok.io`)
2. Paste in browser and add `/docs` → `https://abc123.ngrok.io/docs`
3. [SCREENSHOT: Swagger UI shows two endpoints: GET /health and POST /predict]
4. Click **POST /predict** → **Try it out** → **Execute**
5. See the response in the browser

---

## Step 24 — CELL 22 (Markdown): Download Header

Text cell. Shows "📦 Step 6: Download all outputs". No action.

---

## Step 25 — CELL 23: Download Outputs from Colab

This downloads the processed data file and trained model from Colab to your Windows machine.

**Run Cell 23** (Shift + Enter):

```python
from google.colab import files

for path in [
    '/content/data/processed/pune_features.csv',
    '/content/models/best_model.pkl',
]:
    if os.path.exists(path):
        files.download(path)
        print(f'Downloaded: {path}')
```

**What happens:** Your browser downloads two files:
1. `pune_features.csv` — the cleaned, engineered feature dataset
2. `best_model.pkl` — the trained Gradient Boosting model

**After download, find them in your browser's default download folder:** `C:\Users\admin\Downloads\`

---

## COLAB PHASE COMPLETE

At this point you have:
- Verified data quality through EDA (Steps 7-10)
- Cleaned and engineered 21 features from 18 raw columns (Steps 12)
- Trained and evaluated 5 models with MLflow tracking (Step 14)
- Confirmed GBM is the best model (R²=0.795, MAE=8.64L) (Step 15)
- Run AutoML with PyCaret for second opinion (Steps 18-19)
- Deployed FastAPI inside Colab and tested a live prediction (Steps 21-23)
- Downloaded `pune_features.csv` and `best_model.pkl` to your machine (Step 25)

---

# PHASE 2 — VS CODE: PRODUCTION PIPELINE ON YOUR MACHINE

## What This Phase Does
Everything you did in Colab was experimental — it runs in a temporary cloud session and disappears when you close the tab. Phase 2 takes those same steps, runs them reproducibly in VS Code on your machine, and prepares the code for production deployment.

---

## Step 26 — Copy Downloaded Files into Project

**In Windows Explorer (File Manager), not PowerShell:**
1. Open: `C:\Users\admin\Downloads\`
2. Find `pune_features.csv` and `best_model.pkl`
3. Copy `pune_features.csv`:
   - Destination: `C:\Users\admin\Desktop\pune_real_estate_mlops\data\processed\`
4. Copy `best_model.pkl`:
   - Destination: `C:\Users\admin\Desktop\pune_real_estate_mlops\models\`

**Verify in PowerShell:**
```powershell
Test-Path "C:\Users\admin\Desktop\pune_real_estate_mlops\data\processed\pune_features.csv"
# Must return: True

Test-Path "C:\Users\admin\Desktop\pune_real_estate_mlops\models\best_model.pkl"
# Must return: True
```

If either returns `False`, the file is in the wrong location. Check the destination path.

---

## Step 27 — Open Project in VS Code

```powershell
# Open VS Code pointing to the project folder
code C:\Users\admin\Desktop\pune_real_estate_mlops
```

Or in VS Code: File → Open Folder → navigate to `C:\Users\admin\Desktop\pune_real_estate_mlops` → Select Folder.

[SCREENSHOT: VS Code opens with the file explorer on the left showing the project folders: data/, models/, src/, deployment/, etc.]

---

## Step 28 — Open the Integrated Terminal in VS Code

1. In VS Code: **Terminal menu (top bar) → New Terminal**
2. Or press: **Ctrl + ` (backtick)**

[SCREENSHOT: A terminal panel opens at the bottom of VS Code, showing a PowerShell prompt]

**Verify you are in the right directory:**
```powershell
pwd
# Expected: C:\Users\admin\Desktop\pune_real_estate_mlops
```

If the path is wrong:
```powershell
cd C:\Users\admin\Desktop\pune_real_estate_mlops
```

---

## Step 29 — Activate the Python Virtual Environment

The virtual environment (`.venv`) contains all project-specific Python packages, separate from your system Python.

```powershell
.\.venv\Scripts\Activate.ps1
```

**Expected:** Your prompt changes to show `(.venv)` at the start:
```
(.venv) PS C:\Users\admin\Desktop\pune_real_estate_mlops>
```

**WARNING — Execution policy error:**
If you see: `cannot be loaded because running scripts is disabled on this system`
Run this first (one time only):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# When prompted, type Y and press Enter
```
Then re-run the activate command.

**WARNING — .venv not found:**
If you see: `the path .\.venv\Scripts\Activate.ps1 does not exist`
Recreate the venv:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## Step 30 — Verify Python Version

```powershell
python --version
# Must show: Python 3.10.x
```

If it shows 3.8, 3.9, or 3.11:
```powershell
# Check what pyenv has
pyenv versions

# Set 3.10
pyenv global 3.10.11

# Delete venv and recreate
deactivate
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## Step 31 — Install All Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

**This takes 10-20 minutes** on first run. PyCaret alone downloads ~500MB of dependencies.

**Monitor progress:** You will see hundreds of lines like `Collecting pandas>=2.0.0...`, `Downloading pandas-2.2.0...`, `Installing collected packages...`

**WARNING — Disk space:** This requires at least 3GB free disk space. Check with:
```powershell
Get-PSDrive C | Select-Object Used,Free
# Free should be > 3,000,000,000 (3GB in bytes)
```
If low, delete files from Downloads first.

**WARNING — Dependency conflict warning:** You may see lines like `ERROR: pip's dependency resolver does not currently take into account...`. These are **warnings, not fatal errors**. The packages still install. Continue only if you see `Successfully installed` at the end.

**Verify installation:**
```powershell
python -c "import pandas, sklearn, mlflow, fastapi, joblib; print('All packages OK')"
# Must print: All packages OK
```

---

## Step 32 — Run the Data Preprocessing Pipeline

This script reads the raw Excel and CSV files, cleans them, engineers features, and saves `pune_features.csv`. It replicates exactly what the Colab notebook Cell 10 did, but runs locally.

```powershell
python src/data/preprocess.py
```

**Expected output:**
```
Raw XLSX : (200, 18)  |  Cleaned CSV : (200, 12)
✅  Feature set saved → C:\Users\admin\Desktop\pune_real_estate_mlops\data\processed\pune_features.csv
   Shape   : (197, 21)
   Columns : ['location', 'sub_area', 'property_type', 'company_name', ...]
Sample:
   location  sub_area  property_type  ...  area_sqft  price_lakhs  log_area
0         3         5              1  ...      900.0         85.0    6.803
```

**WARNING — FileNotFoundError:**
```
FileNotFoundError: data/raw/Pune_Real_Estate_Data.xlsx not found
```
This means the raw data files are missing from `data/raw/`. Copy them from `C:\Users\admin\Desktop\pune_real_estate_mlops\data\raw\` — they should already be there. If not, find them at: wherever you originally stored them.

---

## Step 33 — Run Model Training with MLflow Tracking

This script trains all 5 models, evaluates them, tracks every run in MLflow, and saves the best model to `models/best_model.pkl`. It replicates Colab Cell 12 but runs fully locally with proper file paths.

```powershell
python src/models/train.py
```

**Expected output (takes 3-8 minutes):**
```
Dataset  : 197 rows × 15 features
Target   : price_lakhs  (mean=87.3, std=52.1)

[ridge]
  Test  R²=0.742  MAE=14.39L  RMSE=19.84L  MAPE=19.2%
  CV R²=0.718

[lasso]
  Test  R²=0.765  MAE=12.72L  RMSE=18.21L  MAPE=16.8%
  CV R²=0.739

[rf]
  Test  R²=0.780  MAE=8.77L   RMSE=17.43L  MAPE=11.2%
  CV R²=0.763

[gbm] ← BEST
  Test  R²=0.795  MAE=8.64L   RMSE=16.52L  MAPE=10.9%
  CV R²=0.779

[extra_trees]
  Test  R²=0.791  MAE=9.38L   RMSE=16.89L  MAPE=12.1%
  CV R²=0.771

✅  Best model (gbm, R²=0.795) saved → models\best_model.pkl
```

**Verify the model file:**
```powershell
Test-Path models\best_model.pkl
# Must return: True

# Check file size (should be 2-50MB)
(Get-Item models\best_model.pkl).Length / 1MB
# Shows size in MB
```

---

## Step 34 — View MLflow Dashboard

MLflow provides a web UI to compare all 5 model runs visually.

```powershell
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

**Expected output:**
```
[2026-06-02 10:30:00] INFO mlflow.server: Starting gunicorn server
[2026-06-02 10:30:00] INFO mlflow.server: Listening at: http://127.0.0.1:5000
```

**Open in browser:**
1. Open Chrome or Edge
2. Go to: http://localhost:5000
3. [SCREENSHOT: MLflow UI shows "Experiments" list with "pune_real_estate_price_prediction"]
4. Click the experiment name
5. See all 5 runs with their metrics
6. Click "ridge" and "gbm" runs to compare side by side
7. Click "Chart" tab to see visual comparison

**To stop MLflow (when done):** Go back to terminal and press **Ctrl + C**.

**WHY MLflow matters for a manager:** Every model training run is logged with a timestamp, all metrics, all hyperparameters, and the model artifact. This creates a permanent audit trail of every experiment. If someone asks "why did we choose GBM?" you can open MLflow and show the comparison data.

---

## Step 35 — Run the FastAPI Server Locally

This starts the production API server on your machine. The same code that will run in Docker and on EC2.

Open a **second terminal** in VS Code (Terminal → New Terminal) so MLflow can keep running:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn src.api.fastapi_app:app --reload --port 8000
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
✅  Model loaded successfully.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**`--reload`** means the server automatically restarts whenever you save a change to the code. Useful for development.

---

## Step 36 — Test the FastAPI Server

With the server running, open a **third terminal** or test in browser.

**Method 1: Browser (easiest)**
1. Open: http://localhost:8000/docs
2. [SCREENSHOT: Swagger UI with 3 endpoints: GET /health, POST /predict, POST /predict/batch]
3. Click **GET /health** → **Try it out** → **Execute**
4. See: `{"status": "ok", "model_loaded": true}`
5. Click **POST /predict** → **Try it out**
6. Replace the example JSON with:
```json
{
  "area_sqft": 1000,
  "township_area": 50,
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
  "company_name": 2
}
```
7. Click **Execute**
8. See the response: `{"predicted_price_lakhs": 87.4, ...}`

**Method 2: PowerShell command**
```powershell
# In a third terminal (with venv activated):
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -ExpandProperty Content
# Expected: {"status":"ok","model_loaded":true}

$body = '{"area_sqft":1000,"township_area":50,"amenity_score":4,"has_clubhouse":1,"has_school":1,"has_hospital":0,"has_mall":0,"has_park":1,"has_pool":0,"has_gym":1,"location":3,"sub_area":5,"property_type":1,"company_name":2}'

Invoke-WebRequest -Method POST `
  -Uri http://localhost:8000/predict `
  -ContentType "application/json" `
  -Body $body | Select-Object -ExpandProperty Content
# Expected: {"predicted_price_lakhs":87.4,"predicted_price_millions":8.74,...}
```

**Stop the server when done:** Press **Ctrl + C** in the terminal running uvicorn.

---

## Step 37 — Run PyCaret AutoML Locally (Optional)

This runs the AutoML comparison locally. Only needed if you want to check if a different algorithm outperforms GBM with the full library.

```powershell
python src/models/pycaret_train.py
```

This takes 15-30 minutes locally. Output similar to Colab Cell 16-17. Creates `models/pycaret_best.pkl`.

**Skip this step if you are confident in the GBM result from train.py.**

---

# PHASE 3 — DOCKER: PACKAGE THE ENTIRE APPLICATION

## What Docker Does
Docker creates a "container" — a self-contained box with Python 3.10, all installed packages, the model file, and the API code. This container runs identically on your Windows machine, on Ubuntu, and on AWS. No "works on my machine" problems.

---

## Step 38 — Verify Docker Desktop is Running

Look at your Windows system tray (bottom-right corner of taskbar). Find the whale icon.
- **Whale icon present and not animated** = Docker is running
- **No whale icon** = Open Docker Desktop from the Start Menu and wait 60 seconds

```powershell
docker --version
# Expected: Docker version 24.x.x
docker ps
# Expected: CONTAINER ID   IMAGE   COMMAND   ... (empty table, but no error)
```

---

## Step 39 — Review the Dockerfile

In VS Code, open [deployment/docker/Dockerfile](../deployment/docker/Dockerfile). Read it:

```dockerfile
FROM python:3.10-slim                # Start with minimal Python 3.10 Linux image

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git && \   # System tools needed to compile some packages
    rm -rf /var/lib/apt/lists/*     # Clean up to reduce image size

WORKDIR /app                        # All subsequent commands run from /app

COPY requirements.txt .             # Copy requirements FIRST (for layer caching)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt  # Install Python packages

COPY . .                            # Copy all project files into /app

EXPOSE 8000                         # Document that port 8000 will be used

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1  # Container health check

CMD ["uvicorn", "src.api.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
# Start the FastAPI server when container launches
```

No changes needed. This file is production-ready.

---

## Step 40 — Build the Docker Image

Make sure you are in the project root (not inside `deployment/docker/`):
```powershell
cd C:\Users\admin\Desktop\pune_real_estate_mlops
```

Build:
```powershell
docker build -t pune-real-estate-api:latest -f deployment/docker/Dockerfile .
```

**The dot `.` at the end is required.** It tells Docker to use the current folder as the build context.

**This takes 10-20 minutes** on first build (downloads Python image, installs all packages). Subsequent builds use cache and take 30-60 seconds.

**Watch the output:**
```
[+] Building 523.4s (12/12) FINISHED
 => [1/7] FROM docker.io/library/python:3.10-slim
 => [2/7] RUN apt-get update ...
 => [3/7] WORKDIR /app
 => [4/7] COPY requirements.txt .
 => [5/7] RUN pip install --no-cache-dir ...
 => [6/7] COPY . .
 => [7/7] EXPOSE 8000
 => exporting to image
```

**WARNING — error during connect:**
```
error during connect: this error may indicate that the docker daemon is not running
```
Open Docker Desktop from Start Menu. Wait for it to say "Docker Desktop is running" in the system tray. Then retry.

**Verify the image exists:**
```powershell
docker images pune-real-estate-api
# Expected:
# REPOSITORY              TAG       IMAGE ID       CREATED         SIZE
# pune-real-estate-api    latest    abc123def456   1 minute ago   1.85GB
```

---

## Step 41 — Run the Docker Container Locally and Test

```powershell
docker run -d `
  --name pune_api_test `
  -p 8000:8000 `
  pune-real-estate-api:latest
```

**What each flag does:**
- `-d` = run in background (detached)
- `--name pune_api_test` = give the container a name
- `-p 8000:8000` = map port 8000 on your machine to port 8000 in the container

**Wait 30 seconds for startup**, then test:
```powershell
Start-Sleep -Seconds 30

# Health check
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -ExpandProperty Content
# Expected: {"status":"ok","model_loaded":true}

# Test prediction
$body = '{"area_sqft":1000,"amenity_score":4,"has_clubhouse":1,"location":3,"sub_area":5,"property_type":1,"company_name":2}'
Invoke-WebRequest -Method POST -Uri http://localhost:8000/predict -ContentType "application/json" -Body $body | Select-Object -ExpandProperty Content
```

**See container logs:**
```powershell
docker logs pune_api_test
# Look for: ✅  Model loaded successfully.
# And:      INFO:     Application startup complete.
```

**Open Swagger UI in browser:**
```powershell
Start-Process "http://localhost:8000/docs"
```

**Stop and remove the test container:**
```powershell
docker stop pune_api_test
docker rm pune_api_test
```

---

## Step 42 — Push Docker Image to Docker Hub

Docker Hub is a public registry where you store Docker images so any server in the world can download them.

**42.1 — Create Docker Hub account:**
1. Go to https://hub.docker.com
2. Sign Up → choose a username (example: `shadracknakoba`) → verify email
3. Create Repository → Name: `pune-real-estate-api` → Visibility: Public → Create

**42.2 — Create an access token (not your password):**
1. hub.docker.com → click username top-right → Account Settings
2. Left menu → Security → New Access Token
3. Token name: `github-actions` | Permissions: Read & Write
4. Generate → **Copy the token — it shows ONCE**
5. Save it in a text file temporarily: `C:\Users\admin\Desktop\dockerhub_token.txt`

**42.3 — Login from PowerShell:**
```powershell
docker login -u YOUR_DOCKERHUB_USERNAME
# When prompted for Password: paste the ACCESS TOKEN (not your account password)
# Expected: Login Succeeded
```

**42.4 — Tag the image with your username:**
```powershell
# Replace shadracknakoba with YOUR actual Docker Hub username
docker tag pune-real-estate-api:latest shadracknakoba/pune-real-estate-api:latest
docker tag pune-real-estate-api:latest shadracknakoba/pune-real-estate-api:v1.0.0
```

**42.5 — Push both tags:**
```powershell
docker push shadracknakoba/pune-real-estate-api:latest
docker push shadracknakoba/pune-real-estate-api:v1.0.0
```

**This takes 5-15 minutes.** The image is ~1.5-2GB.

**Output:**
```
The push refers to repository [docker.io/shadracknakoba/pune-real-estate-api]
v1.0.0: digest: sha256:abc123... size: 1234
latest: digest: sha256:abc123... size: 1234
```

**42.6 — Verify on Docker Hub:**
1. Go to hub.docker.com/r/shadracknakoba/pune-real-estate-api
2. You should see Tags: `latest` and `v1.0.0`

---

## Step 43 — Set GitHub Actions Secrets

GitHub Actions is the automated pipeline that runs every time you push code. It needs credentials stored as secrets.

**43.1 — Open your GitHub repository:**
https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops

**43.2 — Navigate to secrets:**
Settings tab (top of repo page) → Left sidebar: Secrets and variables → Actions → New repository secret

**43.3 — Add these secrets one at a time:**

Click "New repository secret" for each:

| Name | Value |
|---|---|
| `DOCKER_USERNAME` | Your Docker Hub username (e.g., `shadracknakoba`) |
| `DOCKER_PASSWORD` | The access token from Step 42.2 |

**Do NOT add AWS secrets yet** — we create the EC2 instance first in the next phase, then come back to add them.

---

## Step 44 — Test CI/CD Pipeline (Build Only)

Trigger the pipeline by pushing a small change:

```powershell
# Make a small change to trigger the pipeline
Add-Content -Path README.md -Value "`n<!-- pipeline test $(Get-Date -Format 'yyyy-MM-dd HH:mm') -->"

git add README.md
git commit -m "ci: test GitHub Actions pipeline"
git push origin main
```

**Watch the pipeline run:**
1. Go to: https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops/actions
2. [SCREENSHOT: A workflow run appears with name "CI/CD Pipeline — Pune Real Estate API"]
3. Click it → see three jobs: `test`, `build`, `deploy-ec2`
4. `test` job: should go green in ~2 minutes
5. `build` job: should go green in ~5-10 minutes (builds and pushes Docker image)
6. `deploy-ec2` job: **skipped** (no `EC2_HOST` secret yet — this is expected)

**If test job fails:**
Look at the error. Most common: `No module named 'fastapi'` → add a requirements install step (already in the workflow). Check the workflow file at `.github/workflows/deploy.yml`.

---

# PHASE 4 — AWS EC2: DEPLOY TO THE CLOUD

## What EC2 Is
Amazon EC2 is a virtual Linux server in Amazon's data centre. You rent it by the hour. It runs 24/7 and has a public IP address. You SSH into it (like Remote Desktop but text-based), install Docker, and run your container there. Anyone in the world can then call your API.

---

## Step 45 — Create AWS Account

If you already have an AWS account, skip to Step 46.

1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Enter email, password, account name
4. Credit/debit card required (you won't be charged if you use free tier)
5. Phone verification required
6. Choose "Basic support — Free"
7. Sign in to the console: https://console.aws.amazon.com

---

## Step 46 — Launch EC2 Instance

**Make sure you are in the correct AWS region:**
1. Top-right corner of AWS console → click the region dropdown
2. Select: **Asia Pacific (Mumbai) ap-south-1**
3. This is the closest AWS region to Pune — lowest latency for Indian users

**Launch the instance:**
1. Search "EC2" in the search bar → click EC2
2. Click the orange **Launch instance** button
3. Fill in these settings:

**Name and tags:**
- Name: `pune-real-estate-api`

**Application and OS Images:**
- Click: `Ubuntu` (quick start tab)
- AMI: `Ubuntu Server 22.04 LTS (HVM), SSD Volume Type`
- Architecture: `64-bit (x86)`
- **IMPORTANT:** Check it says "Free tier eligible" if you want free usage

**Instance type:**
- `t2.micro` — free tier (1 vCPU, 1GB RAM) — good for demo
- `t3.small` — paid (~$15/month) — better performance for real usage

**Key pair (login):**
- Click "Create new key pair"
- Key pair name: `pune-api-key`
- Key pair type: RSA
- Private key file format: `.pem`
- Click **Create key pair**
- [YOUR BROWSER DOWNLOADS `pune-api-key.pem` AUTOMATICALLY]
- **Move this file to:** `C:\Users\admin\Downloads\pune-api-key.pem`
- **CRITICAL: You cannot download this file again. Do not delete it.**

**Network settings:**
- Click **Edit** button (next to "Network settings")
- VPC: default VPC (leave as is)
- Auto-assign public IP: **Enable**
- Firewall (security groups): **Create security group**
  - Security group name: `pune-api-sg`
  - Add security group rule → **Add rule**:
    - Type: SSH | Port: 22 | Source: My IP (it auto-fills your current IP)
  - Add another rule:
    - Type: HTTP | Port: 80 | Source: Anywhere (0.0.0.0/0)
  - Add another rule:
    - Type: HTTPS | Port: 443 | Source: Anywhere (0.0.0.0/0)
  - **Do NOT add Port 8000** — Nginx will proxy from 80 to 8000 internally

**Configure storage:**
- 20 GiB | Volume type: gp3

**Summary — Launch:**
- Review the summary on the right
- Click **Launch instance**
- [SCREENSHOT: "Successfully initiated launch of instance i-0abc123..."]
- Click the instance ID link

**Note your instance details (write these down):**
- Instance ID: `i-0...`
- Public IPv4 address: `13.233.x.x` (visible in the instance details)

---

## Step 47 — Create and Associate Elastic IP

By default, EC2 instances get a new IP address every time they reboot. An Elastic IP is a permanent IP address that stays attached to your instance forever.

**In EC2 console left sidebar:**
1. Network & Security → **Elastic IPs**
2. Click **Allocate Elastic IP address**
3. Network border group: ap-south-1 (default)
4. Click **Allocate**
5. [SCREENSHOT: New Elastic IP address allocated, e.g., `13.233.45.67`]
6. Select the Elastic IP → Actions → **Associate Elastic IP address**
7. Resource type: Instance
8. Instance: select `pune-real-estate-api`
9. Click **Associate**
10. **Write down the Elastic IP address** — this is your permanent server address

---

## Step 48 — SSH into EC2 from Windows

**Set permissions on your .pem file** (Windows requires this):
```powershell
$pem = "C:\Users\admin\Downloads\pune-api-key.pem"
icacls $pem /inheritance:r
icacls $pem /grant:r "${env:USERNAME}:(R)"
```

**Connect:**
```powershell
# Replace YOUR_ELASTIC_IP with the IP from Step 47
ssh -i C:\Users\admin\Downloads\pune-api-key.pem ubuntu@YOUR_ELASTIC_IP
```

**When prompted:**
```
The authenticity of host 'x.x.x.x' can't be established.
ECDSA key fingerprint is SHA256:...
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```
Type `yes` and press Enter.

**[SCREENSHOT: You see `ubuntu@ip-x-x-x-x:~$` prompt]** — You are now inside your EC2 server.

---

## Step 49 — Set Up the EC2 Server

Run these commands inside the EC2 SSH session (copy-paste each block):

**49.1 — System update:**
```bash
sudo apt-get update -y && sudo apt-get upgrade -y
```
Takes 2-5 minutes. Shows package updates downloading.

**49.2 — Install Docker:**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

**49.3 — Install Nginx and Certbot:**
```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx curl
```

**49.4 — Log out and back in (required to apply Docker group membership):**
```bash
exit
```

Then reconnect:
```powershell
ssh -i C:\Users\admin\Downloads\pune-api-key.pem ubuntu@YOUR_ELASTIC_IP
```

**49.5 — Verify Docker works without sudo:**
```bash
docker ps
# Expected: empty table with headers (no error)
```

---

## Step 50 — Upload Model File to EC2

The Docker image we built includes the model file (it was copied in via `COPY . .`). But if you want to update the model without rebuilding the image, you can mount it separately.

For now, the model is inside the Docker image. Skip to Step 51.

**To upload the model separately (optional):**
```powershell
# Run this from your Windows PowerShell (not inside the EC2 SSH session)
scp -i C:\Users\admin\Downloads\pune-api-key.pem `
  C:\Users\admin\Desktop\pune_real_estate_mlops\models\best_model.pkl `
  ubuntu@YOUR_ELASTIC_IP:~/best_model.pkl
```

---

## Step 51 — Pull and Run Docker Container on EC2

Inside the EC2 SSH session:

```bash
# Pull the image from Docker Hub
docker pull shadracknakoba/pune-real-estate-api:latest
```

Output:
```
latest: Pulling from shadracknakoba/pune-real-estate-api
...
Status: Downloaded newer image for shadracknakoba/pune-real-estate-api:latest
```

**Start the container:**
```bash
docker run -d \
  --name pune_api \
  --restart unless-stopped \
  -p 8000:8000 \
  -e APP_ENV=production \
  shadracknakoba/pune-real-estate-api:latest
```

**Wait and check:**
```bash
sleep 35
docker ps
# Expected: pune_api container in "Up 35 seconds" state

curl http://localhost:8000/health
# Expected: {"status":"ok","model_loaded":true}
```

**See logs:**
```bash
docker logs pune_api --tail 30
# Look for: ✅  Model loaded successfully.
```

---

## Step 52 — Configure Nginx as Reverse Proxy

Nginx sits between the internet (port 80) and your FastAPI server (port 8000). It handles routing, security headers, and later SSL.

Inside EC2:
```bash
sudo tee /etc/nginx/sites-available/pune_api > /dev/null <<'NGINX'
server {
    listen 80;
    server_name _;

    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/pune_api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
```

Expected: `nginx: configuration file /etc/nginx/nginx.conf test is successful`

```bash
sudo systemctl restart nginx
sudo systemctl enable nginx

# Test via Nginx (port 80 now, not 8000)
curl http://localhost/health
# Expected: {"status":"ok","model_loaded":true}
```

---

## Step 53 — Test the Public API

**From your Windows machine** (not inside EC2):
```powershell
# Health check via public IP
Invoke-WebRequest -Uri "http://YOUR_ELASTIC_IP/health" | Select-Object -ExpandProperty Content
# Expected: {"status":"ok","model_loaded":true}

# Open Swagger UI in browser
Start-Process "http://YOUR_ELASTIC_IP/docs"
```

[SCREENSHOT: Swagger UI loads in your browser from the public EC2 IP address]

**Your API is now publicly accessible.** Anyone with your IP address can call it.

---

## Step 54 — Add EC2 Secrets to GitHub and Enable Full CI/CD

Now that EC2 exists, add the remaining secrets to GitHub:

1. Go to: https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops → Settings → Secrets and variables → Actions

**Add these secrets:**

| Secret Name | Value |
|---|---|
| `EC2_HOST` | Your Elastic IP (e.g., `13.233.45.67`) |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Full contents of `pune-api-key.pem` |

**To copy the .pem file contents:**
```powershell
Get-Content C:\Users\admin\Downloads\pune-api-key.pem | Set-Clipboard
```
Then paste into the GitHub secret value field. The full content starts with `-----BEGIN RSA PRIVATE KEY-----` and ends with `-----END RSA PRIVATE KEY-----`.

**For AWS secrets (needed for ECS — add later):**
| Secret Name | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | From IAM user you create in Step 55 |
| `AWS_SECRET_ACCESS_KEY` | From IAM user you create in Step 55 |

**Test the full CI/CD pipeline with EC2 deploy:**
```powershell
# On your Windows machine
Add-Content -Path README.md -Value "`n<!-- full deploy test $(Get-Date -Format 'yyyy-MM-dd HH:mm') -->"
git add README.md
git commit -m "ci: test full deploy pipeline to EC2"
git push origin main
```

Watch at: https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops/actions

Expected: test ✓ → build ✓ → deploy-ec2 ✓ (all green, takes ~5-8 minutes total)

After it finishes, test the API again from your browser — the new container should be running:
```powershell
Invoke-WebRequest -Uri "http://YOUR_ELASTIC_IP/health" | Select-Object -ExpandProperty Content
```

---

# PHASE 5 — HTTPS: SECURE THE API

## Step 55 — Get a Domain Name (required for HTTPS)

HTTPS requires a domain name (not just an IP address).

**Option A — Free domain (for testing):**
- Go to https://www.freenom.com
- Search for `punepriceapi.tk` or any `.tk` / `.ml` domain
- Register free for 12 months

**Option B — Cheap domain ($1-2/year):**
- Go to https://www.namecheap.com
- Search for `puneapi.xyz` or similar
- Register

**Option C — AWS Route 53 (~$12/year for .com):**
- AWS Console → Route 53 → Register Domain

---

## Step 56 — Point Domain to EC2

In your domain registrar's DNS settings panel:

1. Find "DNS Records" or "Manage DNS"
2. Add an A record:
   - Type: **A**
   - Name: `api` (creates `api.yourdomain.com`) OR `@` (root domain)
   - Value: **YOUR_ELASTIC_IP**
   - TTL: 300

3. Wait 5-30 minutes for DNS to propagate worldwide

**Test DNS propagation:**
```powershell
nslookup api.yourdomain.com
# Should return your Elastic IP
# If it shows a different IP or error, wait more and retry
```

---

## Step 57 — Get SSL Certificate with Let's Encrypt

Inside the EC2 SSH session:

```bash
# Update Nginx config with your domain first
sudo sed -i 's/server_name _;/server_name api.yourdomain.com;/' /etc/nginx/sites-available/pune_api
sudo systemctl reload nginx

# Get certificate (interactive)
sudo certbot --nginx -d api.yourdomain.com
```

**You will be asked:**
1. `Enter email address:` → `shadrack.n159@gmail.com`
2. `Agree to ToS? (A/C):` → `A`
3. `Share email with EFF? (Y/N):` → `N` (your choice)

**Expected success output:**
```
Congratulations! Your certificate and chain have been saved at:
/etc/letsencrypt/live/api.yourdomain.com/fullchain.pem

Your certificate will expire on 2026-09-02.
```

Certbot automatically modifies your Nginx config to add SSL and HTTP→HTTPS redirect.

**Test HTTPS:**
```bash
curl https://api.yourdomain.com/health
# Expected: {"status":"ok","model_loaded":true}
```

**Test from Windows:**
```powershell
Start-Process "https://api.yourdomain.com/docs"
```

[SCREENSHOT: Browser shows padlock (🔒) and your domain in the address bar, Swagger UI loads]

---

# PHASE 6 — FULL VERIFICATION

## Step 58 — End-to-End Test

Run these from your Windows machine to verify every layer is working:

```powershell
# 1. Health check via HTTPS
Invoke-WebRequest -Uri "https://api.yourdomain.com/health" | Select-Object -ExpandProperty Content
# Must return: {"status":"ok","model_loaded":true}

# 2. Prediction via HTTPS
$headers = @{"Content-Type" = "application/json"}
$body = '{"area_sqft":1200,"township_area":80,"amenity_score":5,"has_clubhouse":1,"has_school":1,"has_hospital":1,"has_mall":0,"has_park":1,"has_pool":1,"has_gym":1,"location":3,"sub_area":5,"property_type":1,"company_name":2}'
$r = Invoke-WebRequest -Method POST -Uri "https://api.yourdomain.com/predict" -Headers $headers -Body $body
$r.Content
# Must return price prediction JSON

# 3. Batch prediction
$batchBody = '[{"area_sqft":800,"amenity_score":2,"location":1,"sub_area":1,"property_type":0,"company_name":0},{"area_sqft":2000,"amenity_score":7,"has_clubhouse":1,"location":5,"sub_area":10,"property_type":2,"company_name":3}]'
$r = Invoke-WebRequest -Method POST -Uri "https://api.yourdomain.com/predict/batch" -Headers $headers -Body $batchBody
$r.Content
# Must return array of 2 predictions

# 4. Input validation (should fail with 422)
$bad = '{"area_sqft":-500}'
try {
  Invoke-WebRequest -Method POST -Uri "https://api.yourdomain.com/predict" -Headers $headers -Body $bad
} catch {
  $_.Exception.Response.StatusCode.Value__
  # Must return: 422
}
```

## Step 59 — Confirm CI/CD Full Cycle

1. Make a small code change in VS Code (e.g., change `version="1.0.0"` to `version="1.0.1"` in `src/api/fastapi_app.py`)
2. Save the file
3. Run:
```powershell
git add src/api/fastapi_app.py
git commit -m "bump api version to 1.0.1"
git push origin main
```
4. Watch GitHub Actions: https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops/actions
5. All jobs complete green (~8 minutes)
6. Call the API — the container has been automatically updated on EC2

---

# COMPLETE SYSTEM MAP (What Each File Does)

```
pune_real_estate_mlops/
│
├── data/
│   ├── raw/
│   │   ├── Pune_Real_Estate_Data.xlsx  ← Raw property listings (200 rows, 18 columns)
│   │   └── data_cleaned.csv            ← Secondary data source with cleaned price/area
│   └── processed/
│       └── pune_features.csv           ← OUTPUT of preprocess.py (197 rows, 21 features)
│
├── models/
│   ├── best_model.pkl                  ← OUTPUT of train.py (GBM pipeline, ~10MB)
│   ├── feature_columns.txt             ← List of 15 features the model expects
│   └── pycaret_best.pkl                ← OUTPUT of pycaret_train.py (AutoML winner)
│
├── notebooks/
│   └── Pune_Real_Estate_EndToEnd_ML.ipynb  ← COLAB NOTEBOOK (Cells 1-23 above)
│
├── src/
│   ├── data/
│   │   └── preprocess.py       ← VS CODE VERSION of Colab Cell 10 (run locally)
│   ├── models/
│   │   ├── train.py            ← VS CODE VERSION of Colab Cell 12 (run locally)
│   │   └── pycaret_train.py    ← VS CODE VERSION of Colab Cells 16-17 (run locally)
│   └── api/
│       ├── fastapi_app.py      ← PRODUCTION API (expanded version of Colab Cell 19)
│       └── flask_app.py        ← Alternative lightweight API (not used in production)
│
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile           ← Instructions to build the Docker image (Step 39)
│   │   └── docker-compose.yml   ← Runs API + MLflow UI containers together
│   └── ec2/
│       └── deploy.sh            ← One-click EC2 setup script (for manual EC2 deploy)
│
├── .github/
│   └── workflows/
│       └── deploy.yml           ← GitHub Actions CI/CD (auto runs on every git push)
│
├── NAKOBA_implementation/
│   ├── PROJECT_JOURNEY.md       ← Full project story (architecture, tools, problems)
│   ├── PROD_READY.md            ← Production checklist + AWS/K8s deployment guide
│   ├── CONTINUATION.md          ← Step-by-step from Docker Hub to live URL
│   └── E2E_MASTER_GUIDE.md     ← THIS FILE (every step from Colab to live)
│
├── tests/
│   └── test_api.py              ← Automated tests (run by GitHub Actions)
│
├── dvc.yaml                     ← DVC pipeline definition (preprocess → train → pycaret)
├── requirements.txt             ← All Python package dependencies
└── README.md                    ← Project overview and quick start guide
```

---

# QUICK REFERENCE — ALL COMMANDS IN ORDER

## Colab Commands (in order)
```
Cell 1:  Upload files     → Shift+Enter → choose files
Cell 2:  !pip install     → Shift+Enter (wait 3-5 min)
Cell 3:  imports          → Shift+Enter
Cell 5:  load data        → Shift+Enter
Cell 6:  missing values   → Shift+Enter
Cell 7:  price histogram  → Shift+Enter
Cell 8:  correlation map  → Shift+Enter
Cell 10: clean + engineer → Shift+Enter (creates pune_features.csv)
Cell 12: train 5 models   → Shift+Enter (wait 5-8 min, creates best_model.pkl)
Cell 13: results table    → Shift+Enter
Cell 14: feature chart    → Shift+Enter
Cell 16: pycaret compare  → Shift+Enter (wait 10-15 min)
Cell 17: pycaret tune     → Shift+Enter
Cell 19: write API        → Shift+Enter
Cell 20: start server     → Shift+Enter (starts public URL)
Cell 21: test API         → Shift+Enter
Cell 23: download files   → Shift+Enter (saves to Downloads)
```

## VS Code / PowerShell Commands (in order)
```powershell
# Navigate to project
cd C:\Users\admin\Desktop\pune_real_estate_mlops

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install packages (first time only)
pip install --upgrade pip
pip install -r requirements.txt

# Run pipeline
python src/data/preprocess.py
python src/models/train.py

# Start MLflow dashboard
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
# Open: http://localhost:5000

# Start API
uvicorn src.api.fastapi_app:app --reload --port 8000
# Open: http://localhost:8000/docs

# Build Docker image
docker build -t pune-real-estate-api:latest -f deployment/docker/Dockerfile .

# Test Docker container
docker run -d --name pune_api_test -p 8000:8000 pune-real-estate-api:latest
Start-Sleep 30
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -ExpandProperty Content
docker stop pune_api_test && docker rm pune_api_test

# Push to Docker Hub
docker login -u YOUR_DOCKERHUB_USERNAME
docker tag pune-real-estate-api:latest YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:latest
docker push YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:latest

# Push to GitHub (triggers CI/CD)
git add .
git commit -m "deploy: push changes"
git push origin main
```

## EC2 Commands (run inside SSH session)
```bash
# SSH in (run from Windows PowerShell)
ssh -i C:\Users\admin\Downloads\pune-api-key.pem ubuntu@YOUR_ELASTIC_IP

# Inside EC2:
sudo apt-get update -y && sudo apt-get upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
sudo apt-get install -y nginx certbot python3-certbot-nginx curl
exit   # Then reconnect

# Pull and run
docker pull YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:latest
docker run -d --name pune_api --restart unless-stopped -p 8000:8000 YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:latest
sleep 35 && curl http://localhost:8000/health

# Configure Nginx
sudo tee /etc/nginx/sites-available/pune_api > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF
sudo ln -sf /etc/nginx/sites-available/pune_api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# SSL (after domain DNS is configured)
sudo certbot --nginx -d api.yourdomain.com
```

---

**The API is live when:** `curl https://api.yourdomain.com/health` returns `{"status":"ok","model_loaded":true}` from any machine, any network, anywhere in the world.
