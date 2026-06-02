"""
STEP 1: Data Cleaning & Feature Engineering
Pune Real Estate Price Prediction
"""

import pandas as pd
import numpy as np
import warnings
import os
warnings.filterwarnings("ignore")

_BASE    = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
RAW_XLSX = os.path.join(_BASE, "data/raw/Pune_Real_Estate_Data.xlsx")
RAW_CSV  = os.path.join(_BASE, "data/raw/data_cleaned.csv")
OUT_PATH = os.path.join(_BASE, "data/processed/pune_features.csv")


def load_raw_data():
    df_raw  = pd.read_excel(RAW_XLSX)
    df_base = pd.read_csv(RAW_CSV)
    print(f"Raw XLSX : {df_raw.shape}  |  Cleaned CSV : {df_base.shape}")
    return df_raw, df_base


def clean_raw(df):
    df = df.copy()
    df.columns = (df.columns.str.strip().str.lower()
                   .str.replace(r"[^\w]+", "_", regex=True))
    df.rename(columns={"propert_type": "property_type",
                        "township_name_society_name": "township_name"}, inplace=True)

    area_col  = next((c for c in df.columns if "property_area" in c), None)
    price_col = next((c for c in df.columns if "price_in_lakhs" in c), None)

    df["property_area_sqft"] = pd.to_numeric(
        df[area_col].astype(str).str.replace(",","").str.extract(r"([\d.]+)")[0],
        errors="coerce") if area_col else np.nan

    df["price_lakhs"] = pd.to_numeric(
        df[price_col].astype(str).str.replace(",","").str.extract(r"([\d.]+)")[0],
        errors="coerce") if price_col else np.nan

    amenity_map = {
        "clubhouse":                     "has_clubhouse",
        "school_university_in_township": "has_school",
        "hospital_in_township":          "has_hospital",
        "mall_in_township":              "has_mall",
        "park_jogging_track":            "has_park",
        "swimming_pool":                 "has_pool",
        "gym":                           "has_gym",
    }
    yes_map = {"yes":1,"no":0,"1":1,"0":0}
    for src, tgt in amenity_map.items():
        if src in df.columns:
            df[tgt] = (df[src].astype(str).str.strip().str.lower()
                         .map(yes_map).fillna(0).astype(int))

    for col in ["location","sub_area","property_type","company_name","township_name"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()

    df.dropna(subset=["price_lakhs","property_area_sqft"], inplace=True)
    keep = (["location","sub_area","property_type","company_name","township_name",
             "total_township_area_in_acres","property_area_sqft","price_lakhs"]
            + list(amenity_map.values()))
    return df[[c for c in keep if c in df.columns]]


def merge_datasets(df_clean, df_base):
    shared = min(len(df_clean), len(df_base))
    df = df_clean.reset_index(drop=True).iloc[:shared].copy()
    df["area_sqft"]   = df_base["Area Cleaned"].iloc[:shared].values
    df["price_lakhs"] = df_base["Price Cleaned"].iloc[:shared].values
    flag_map = {"ClubHouse Cleaned":"has_clubhouse","School Cleaned":"has_school",
                "Hospital Cleaned":"has_hospital","Mall Cleaned":"has_mall",
                "Park Cleaned":"has_park","Pool Cleaned":"has_pool","Gym Cleaned":"has_gym"}
    for src, tgt in flag_map.items():
        if src in df_base.columns:
            df[tgt] = df_base[src].iloc[:shared].values
    df.dropna(subset=["price_lakhs","area_sqft"], inplace=True)
    return df


def engineer_features(df):
    df = df.copy()
    df["price_per_sqft"] = df["price_lakhs"] / (df["area_sqft"] + 1e-6)
    amenity_cols = ["has_clubhouse","has_school","has_hospital",
                    "has_mall","has_park","has_pool","has_gym"]
    df["amenity_score"] = df[[c for c in amenity_cols if c in df.columns]].sum(axis=1)
    df["log_area"]  = np.log1p(df["area_sqft"])
    df["log_price"] = np.log1p(df["price_lakhs"])
    if "total_township_area_in_acres" in df.columns:
        df["township_area"] = df["total_township_area_in_acres"].fillna(
            df["total_township_area_in_acres"].median())
    else:
        df["township_area"] = 0.0
    for col in ["location","sub_area","property_type","company_name","township_name"]:
        if col in df.columns:
            df[col] = df[col].astype("category").cat.codes
    return df.reset_index(drop=True)


def run_pipeline():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df_raw, df_base = load_raw_data()
    df_clean        = clean_raw(df_raw)
    df_merged       = merge_datasets(df_clean, df_base)
    df_features     = engineer_features(df_merged)
    df_features.to_csv(OUT_PATH, index=False)
    print(f"\n✅  Feature set saved → {OUT_PATH}")
    print(f"   Shape   : {df_features.shape}")
    print(f"   Columns : {df_features.columns.tolist()}")
    return df_features


if __name__ == "__main__":
    df = run_pipeline()
    print("\nSample:")
    print(df.head())
