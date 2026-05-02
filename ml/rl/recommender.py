from pathlib import Path

import torch

from agent import QNetwork


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "dqn_best.pt"

STATE_KEYS = [
    "knowledge_score",
    "engagement_score",
    "confusion_score",
    "retention_score",
    "recent_accuracy",
    "questions_answered_normalized",
    "session_time_normalized",
    "incorrect_streak_normalized",
]

TOPICS = ["Algebra", "Probability", "Geometry"]
DIFFICULTIES = ["easy", "medium", "hard"]


class RLRecommender:
    def __init__(self, model_path=MODEL_PATH):
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Missing DQN weights: {model_path}. Run train.py first.")

        self.network = QNetwork(input_dim=8, output_dim=9)
        self.network.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
        self.network.eval()

    def recommend(self, state_dict):
        missing = [key for key in STATE_KEYS if key not in state_dict]
        if missing:
            raise KeyError(f"Missing state keys: {missing}")

        state = torch.tensor(
            [float(state_dict[key]) for key in STATE_KEYS],
            dtype=torch.float32,
        ).unsqueeze(0)

        with torch.no_grad():
            q_values = self.network(state).squeeze(0)

        action_id = int(torch.argmax(q_values).item())
        return {
            "action_id": action_id,
            "topic": TOPICS[action_id // 3],
            "difficulty": DIFFICULTIES[action_id % 3],
            "q_values": [round(float(value), 4) for value in q_values.tolist()],
        }
