import sys
from pathlib import Path

import numpy as np


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import gym
    from gym import spaces
except ImportError:
    gym = None

    class _Discrete:
        def __init__(self, n):
            self.n = n

        def sample(self):
            return int(np.random.randint(self.n))

    class _Box:
        def __init__(self, low, high, shape, dtype):
            self.low = low
            self.high = high
            self.shape = shape
            self.dtype = dtype

    class _Spaces:
        Discrete = _Discrete
        Box = _Box

    class _Env:
        pass

    spaces = _Spaces()

from behaviour.model import BehaviourModel
from forgetting.model import ForgettingModel


BaseEnv = gym.Env if gym is not None else _Env


class StudentEnv(BaseEnv):
    """
    Simulated student environment.

    State:
    [knowledge_score, engagement_score, confusion_score, retention_score,
     recent_accuracy, questions_answered_normalized, session_time_normalized,
     incorrect_streak_normalized]
    """

    metadata = {"render_modes": []}

    def __init__(self, seed=None):
        super().__init__()
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(8,), dtype=np.float32)
        self.action_space = spaces.Discrete(9)
        self.rng = np.random.default_rng(seed)
        self.behaviour_model = BehaviourModel()
        self.forgetting_model = ForgettingModel()
        self.max_questions = 20
        self.topics = ["Algebra", "Probability", "Geometry"]
        self.difficulties = ["easy", "medium", "hard"]
        self.state = None
        self.question_count = 0
        self.incorrect_streak = 0
        self.review_count = 1
        self.hours_since_last_review = 24.0

    def reset(self, seed=None, options=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)

        knowledge_score = self.rng.uniform(0.25, 0.75)
        engagement_score = self.rng.uniform(0.45, 0.85)
        confusion_score = self.rng.uniform(0.05, 0.35)
        retention_score = self.rng.uniform(0.45, 0.95)
        recent_accuracy = self.rng.uniform(0.4, 0.8)
        self.question_count = 0
        self.incorrect_streak = int(self.rng.integers(0, 3))
        self.review_count = int(self.rng.integers(1, 8))
        self.hours_since_last_review = float(self.rng.uniform(4.0, 240.0))
        session_time_normalized = 0.0

        self.state = np.array(
            [
                knowledge_score,
                engagement_score,
                confusion_score,
                retention_score,
                recent_accuracy,
                0.0,
                session_time_normalized,
                self.incorrect_streak / 8.0,
            ],
            dtype=np.float32,
        )
        return self.state.copy()

    def step(self, action):
        if self.state is None:
            self.reset()

        action = int(action)
        topic_id = action // 3
        difficulty_id = action % 3
        difficulty_penalty = [0.0, 0.12, 0.25][difficulty_id]

        knowledge, engagement, confusion, retention, recent_accuracy, _, session_time, _ = self.state
        near_forgetting_threshold = 0.72 <= retention <= 0.88

        response_time_ms = float(
            np.clip(
                18_000
                + 30_000 * confusion
                + 8_000 * difficulty_id
                - 8_000 * engagement
                + self.rng.normal(0, 4_000),
                3_000,
                120_000,
            )
        )
        retry_count = int(np.clip(round(confusion * 3 + difficulty_id * 0.4 + self.rng.normal(0, 0.4)), 0, 3))
        skip_rate = float(np.clip(0.05 + 0.25 * confusion - 0.12 * engagement + self.rng.normal(0, 0.025), 0.0, 0.4))
        session_duration = float(np.clip(10 + session_time * 80 + self.rng.normal(0, 4), 10, 90))

        behaviour = self.behaviour_model.score(
            response_time_ms=response_time_ms,
            retry_count=retry_count,
            incorrect_streak=self.incorrect_streak,
            skip_rate=skip_rate,
            session_duration_minutes=session_duration,
            time_of_day_hour=int(self.rng.integers(0, 24)),
            recent_accuracy=float(recent_accuracy),
        )
        engagement = 0.7 * engagement + 0.3 * behaviour["engagement_score"]
        confusion = 0.7 * confusion + 0.3 * behaviour["confusion_score"]

        correct_prob = (
            0.45 * knowledge
            + 0.25 * retention
            + 0.2 * recent_accuracy
            + 0.1 * engagement
            - 0.18 * confusion
            - difficulty_penalty
            + self.rng.normal(0, 0.04)
        )
        correct_prob = float(np.clip(correct_prob, 0.02, 0.98))
        is_correct = bool(self.rng.random() < correct_prob)

        if is_correct:
            self.incorrect_streak = 0
            knowledge += 0.035 + 0.015 * difficulty_id
        else:
            self.incorrect_streak += 1
            knowledge -= 0.015 + 0.005 * difficulty_id

        self.question_count += 1
        self.review_count += 1 if topic_id == 0 or near_forgetting_threshold else 0
        self.hours_since_last_review = max(0.5, self.hours_since_last_review + self.rng.uniform(0.5, 12.0))

        retention = self.forgetting_model.predict_retention(
            hours_since_last_review=self.hours_since_last_review,
            review_count=self.review_count,
            average_correctness=float(np.clip(recent_accuracy, 0.3, 1.0)),
        )
        if near_forgetting_threshold:
            retention = min(1.0, retention + 0.08)
            self.hours_since_last_review = 0.5

        recent_accuracy = 0.85 * recent_accuracy + 0.15 * float(is_correct)
        session_time = min(1.0, session_time + self.rng.uniform(0.035, 0.065))

        reward = 0.0
        reward += 0.3 if is_correct else 0.0
        reward += 0.2 if engagement >= 0.65 else 0.0
        reward -= 0.2 if confusion >= 0.55 else 0.0
        reward -= 0.1 if self.incorrect_streak > 3 else 0.0
        reward += 0.1 if near_forgetting_threshold else 0.0

        self.state = np.array(
            [
                np.clip(knowledge, 0.0, 1.0),
                np.clip(engagement, 0.0, 1.0),
                np.clip(confusion, 0.0, 1.0),
                np.clip(retention, 0.0, 1.0),
                np.clip(recent_accuracy, 0.0, 1.0),
                min(self.question_count / self.max_questions, 1.0),
                session_time,
                min(self.incorrect_streak / 8.0, 1.0),
            ],
            dtype=np.float32,
        )

        done = self.question_count >= self.max_questions
        info = {
            "topic": self.topics[topic_id],
            "difficulty": self.difficulties[difficulty_id],
            "correct": is_correct,
            "correct_prob": correct_prob,
            "near_forgetting_threshold": near_forgetting_threshold,
        }
        return self.state.copy(), float(reward), done, info
