from pathlib import Path

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "forgetting_model.pkl"

FEATURE_COLUMNS = [
    "hours_since_last_review",
    "review_count",
    "average_correctness",
]


class ForgettingModel:
    def __init__(self, model_path=MODEL_PATH):
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Missing forgetting model: {model_path}. Run train.py first.")
        self.model = joblib.load(model_path)

    def predict_retention(self, hours_since_last_review, review_count, average_correctness):
        features = pd.DataFrame(
            [
                {
                    "hours_since_last_review": hours_since_last_review,
                    "review_count": review_count,
                    "average_correctness": average_correctness,
                }
            ],
            columns=FEATURE_COLUMNS,
        )
        prediction = float(self.model.predict(features)[0])
        return min(max(prediction, 0.0), 1.0)

    def hours_until_threshold(self, review_count, average_correctness, threshold=0.85):
        low = 0.0
        high = 720.0

        if self.predict_retention(low, review_count, average_correctness) < threshold:
            return low
        if self.predict_retention(high, review_count, average_correctness) >= threshold:
            return high

        for _ in range(40):
            mid = (low + high) / 2.0
            retention = self.predict_retention(mid, review_count, average_correctness)
            if retention >= threshold:
                low = mid
            else:
                high = mid

        return round(high, 3)
