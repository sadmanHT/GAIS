from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_PATH = Path(__file__).with_name("forgetting_data.csv")
N_RECORDS = 30_000
RANDOM_SEED = 42


def generate_forgetting_data(n_records=N_RECORDS, output_path=OUTPUT_PATH):
    rng = np.random.default_rng(RANDOM_SEED)

    user_id = rng.integers(1, 1001, size=n_records)
    concept_id = rng.integers(1, 201, size=n_records)
    hours_since_last_review = rng.uniform(0.5, 720.0, size=n_records)
    review_count = rng.integers(1, 21, size=n_records)
    average_correctness = rng.uniform(0.3, 1.0, size=n_records)

    stability = 24.0 * review_count * average_correctness
    retention_score = average_correctness * np.exp(-hours_since_last_review / stability)
    retention_score += rng.normal(0.0, 0.025, size=n_records)
    retention_score = np.clip(retention_score, 0.0, 1.0)

    df = pd.DataFrame(
        {
            "user_id": user_id,
            "concept_id": concept_id,
            "hours_since_last_review": hours_since_last_review.round(3),
            "review_count": review_count,
            "average_correctness": average_correctness.round(4),
            "retention_score": retention_score.round(4),
        }
    )

    df.to_csv(output_path, index=False)
    print(f"Saved {len(df):,} forgetting records to {output_path}")
    return df


if __name__ == "__main__":
    generate_forgetting_data()
