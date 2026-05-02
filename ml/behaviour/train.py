from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "behaviour_data.csv"
ENGAGEMENT_MODEL_PATH = BASE_DIR / "engagement_model.pkl"
CONFUSION_MODEL_PATH = BASE_DIR / "confusion_model.pkl"

FEATURE_COLUMNS = [
    "response_time_ms",
    "retry_count",
    "incorrect_streak",
    "skip_rate",
    "session_duration_minutes",
    "time_of_day_hour",
    "recent_accuracy",
]


def train_regressor(X_train, y_train):
    model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def print_metrics(name, y_true, y_pred):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    print(f"{name} RMSE: {rmse:.4f}")
    print(f"{name} R2:   {r2:.4f}")


def train_models():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {DATA_PATH}. Run generate_data.py before training."
        )

    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLUMNS]

    X_train, X_test, engagement_train, engagement_test, confusion_train, confusion_test = train_test_split(
        X,
        df["engagement_score"],
        df["confusion_score"],
        test_size=0.2,
        random_state=42,
    )

    engagement_model = train_regressor(X_train, engagement_train)
    confusion_model = train_regressor(X_train, confusion_train)

    engagement_pred = engagement_model.predict(X_test)
    confusion_pred = confusion_model.predict(X_test)

    print_metrics("Engagement", engagement_test, engagement_pred)
    print_metrics("Confusion", confusion_test, confusion_pred)

    joblib.dump(engagement_model, ENGAGEMENT_MODEL_PATH)
    joblib.dump(confusion_model, CONFUSION_MODEL_PATH)
    print(f"Saved engagement model to {ENGAGEMENT_MODEL_PATH}")
    print(f"Saved confusion model to {CONFUSION_MODEL_PATH}")

    return engagement_model, confusion_model


if __name__ == "__main__":
    train_models()
