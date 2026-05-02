from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_PATH = Path(__file__).with_name("behaviour_data.csv")
N_RECORDS = 50_000
RANDOM_SEED = 42


def min_max_scale(values, min_value, max_value):
    return (values - min_value) / (max_value - min_value)


def generate_behaviour_data(n_records=N_RECORDS, output_path=OUTPUT_PATH):
    rng = np.random.default_rng(RANDOM_SEED)

    response_time_ms = rng.normal(loc=25_000, scale=12_000, size=n_records)
    response_time_ms = np.clip(response_time_ms, 3_000, 120_000)

    retry_count = rng.choice([0, 1, 2, 3], size=n_records, p=[0.68, 0.2, 0.09, 0.03])
    incorrect_streak_weights = np.array(
        [0.32, 0.22, 0.15, 0.1, 0.075, 0.055, 0.035, 0.025, 0.015]
    )
    incorrect_streak = rng.choice(
        np.arange(9),
        size=n_records,
        p=incorrect_streak_weights / incorrect_streak_weights.sum(),
    )
    skip_rate = rng.beta(a=1.4, b=5.5, size=n_records) * 0.4
    session_duration_minutes = rng.uniform(10, 90, size=n_records)
    time_of_day_hour = rng.integers(0, 24, size=n_records)
    questions_answered = rng.integers(1, 101, size=n_records)
    recent_accuracy = rng.beta(a=4.0, b=2.2, size=n_records)

    response_fast = 1.0 - min_max_scale(response_time_ms, 3_000, 120_000)
    session_norm = min_max_scale(session_duration_minutes, 10, 90)
    skip_low = 1.0 - min_max_scale(skip_rate, 0.0, 0.4)

    engagement_noise = rng.normal(0, 0.06, size=n_records)
    engagement_score = (
        0.42 * session_norm
        + 0.28 * response_fast
        + 0.22 * skip_low
        + 0.08 * recent_accuracy
        + engagement_noise
    )
    engagement_score = np.clip(engagement_score, 0.0, 1.0)

    response_slow = min_max_scale(response_time_ms, 3_000, 120_000)
    retry_norm = retry_count / 3.0
    incorrect_norm = incorrect_streak / 8.0

    confusion_noise = rng.normal(0, 0.07, size=n_records)
    confusion_score = (
        0.45 * incorrect_norm
        + 0.28 * response_slow
        + 0.2 * retry_norm
        + 0.07 * (1.0 - recent_accuracy)
        + confusion_noise
    )
    confusion_score = np.clip(confusion_score, 0.0, 1.0)

    df = pd.DataFrame(
        {
            "response_time_ms": response_time_ms.round(0).astype(int),
            "retry_count": retry_count,
            "incorrect_streak": incorrect_streak,
            "skip_rate": skip_rate.round(4),
            "session_duration_minutes": session_duration_minutes.round(2),
            "time_of_day_hour": time_of_day_hour,
            "questions_answered": questions_answered,
            "recent_accuracy": recent_accuracy.round(4),
            "engagement_score": engagement_score.round(4),
            "confusion_score": confusion_score.round(4),
        }
    )

    df.to_csv(output_path, index=False)
    print(f"Saved {len(df):,} synthetic behaviour records to {output_path}")
    return df


if __name__ == "__main__":
    generate_behaviour_data()
