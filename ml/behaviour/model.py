from pathlib import Path

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
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


class BehaviourModel:
    def __init__(
        self,
        engagement_model_path=ENGAGEMENT_MODEL_PATH,
        confusion_model_path=CONFUSION_MODEL_PATH,
    ):
        if not Path(engagement_model_path).exists():
            raise FileNotFoundError(
                f"Missing engagement model: {engagement_model_path}. Run train.py first."
            )
        if not Path(confusion_model_path).exists():
            raise FileNotFoundError(
                f"Missing confusion model: {confusion_model_path}. Run train.py first."
            )

        self.engagement_model = joblib.load(engagement_model_path)
        self.confusion_model = joblib.load(confusion_model_path)

    def score(
        self,
        response_time_ms,
        retry_count,
        incorrect_streak,
        skip_rate,
        session_duration_minutes,
        time_of_day_hour,
        recent_accuracy,
    ):
        features = pd.DataFrame(
            [
                {
                    "response_time_ms": response_time_ms,
                    "retry_count": retry_count,
                    "incorrect_streak": incorrect_streak,
                    "skip_rate": skip_rate,
                    "session_duration_minutes": session_duration_minutes,
                    "time_of_day_hour": time_of_day_hour,
                    "recent_accuracy": recent_accuracy,
                }
            ],
            columns=FEATURE_COLUMNS,
        )

        engagement_score = float(self.engagement_model.predict(features)[0])
        confusion_score = float(self.confusion_model.predict(features)[0])

        engagement_score = min(max(engagement_score, 0.0), 1.0)
        confusion_score = min(max(confusion_score, 0.0), 1.0)

        return {
            "engagement_score": round(engagement_score, 3),
            "confusion_score": round(confusion_score, 3),
        }
