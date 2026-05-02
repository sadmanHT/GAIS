from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "forgetting_data.csv"
MODEL_PATH = BASE_DIR / "forgetting_model.pkl"

FEATURE_COLUMNS = [
    "hours_since_last_review",
    "review_count",
    "average_correctness",
]


def exponential_baseline(features, stability_scale):
    hours, review_count, average_correctness = features
    stability = stability_scale * review_count * average_correctness
    stability = np.maximum(stability, 1e-6)
    return average_correctness * np.exp(-hours / stability)


def train_model():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {DATA_PATH}. Run generate_data.py before training."
        )

    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLUMNS]
    y = df["retention_score"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    model = XGBRegressor(
        n_estimators=350,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    print(f"XGBoost RMSE: {rmse:.4f}")
    print(f"XGBoost R2:   {r2:.4f}")

    train_features = (
        X_train["hours_since_last_review"].to_numpy(),
        X_train["review_count"].to_numpy(),
        X_train["average_correctness"].to_numpy(),
    )
    params, _ = curve_fit(
        exponential_baseline,
        train_features,
        y_train.to_numpy(),
        p0=[24.0],
        bounds=([1.0], [240.0]),
        maxfev=10_000,
    )
    test_features = (
        X_test["hours_since_last_review"].to_numpy(),
        X_test["review_count"].to_numpy(),
        X_test["average_correctness"].to_numpy(),
    )
    baseline_preds = exponential_baseline(test_features, params[0])
    baseline_r2 = r2_score(y_test, baseline_preds)
    print(f"Exponential baseline stability scale: {params[0]:.4f}")
    print(f"Exponential baseline R2: {baseline_r2:.4f}")

    joblib.dump(model, MODEL_PATH)
    print(f"Saved forgetting model to {MODEL_PATH}")
    return model


if __name__ == "__main__":
    train_model()
