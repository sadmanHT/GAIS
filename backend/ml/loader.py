import importlib.util
import sys
from collections import namedtuple
from functools import lru_cache
from pathlib import Path

import torch


LoadedModels = namedtuple(
    "LoadedModels",
    ["sakt_model", "behaviour_model", "forgetting_model", "rl_recommender"],
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
ROOT_ML_DIR = ROOT_DIR / "ml"


def _load_module(module_name, path, extra_sys_path=None):
    if extra_sys_path:
        sys.path.insert(0, str(extra_sys_path))
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create import spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if extra_sys_path and sys.path and sys.path[0] == str(extra_sys_path):
            sys.path.pop(0)


class SAKTModel:
    def __init__(self, model_path=None):
        model_path = Path(model_path or BACKEND_DIR / "ml" / "sakt_best.pt")
        if not model_path.exists():
            fallback = ROOT_ML_DIR / "sakt_best.pt"
            if fallback.exists():
                model_path = fallback
            else:
                raise FileNotFoundError(
                    f"Missing SAKT weights. Looked for {model_path} and {fallback}."
                )

        sakt_module = _load_module("root_sakt_model", ROOT_ML_DIR / "dkt" / "model.py")
        state_dict = torch.load(model_path, map_location="cpu", weights_only=True)
        n_questions = state_dict["pred_layer.weight"].shape[0] - 1

        self.model = sakt_module.SAKT(n_questions=n_questions).to("cpu")
        self.model.load_state_dict(state_dict)
        self.model.eval()
        self.n_questions = n_questions
        self.model_path = model_path

    def predict_next(self, q_seq, a_seq, target_q):
        target_q = int(target_q)
        if target_q <= 0 or target_q > self.n_questions:
            return 0.5
        if not q_seq:
            return 0.5
        with torch.no_grad():
            q_tensor = torch.tensor([q_seq[-200:]], dtype=torch.long)
            a_tensor = torch.tensor([a_seq[-200:]], dtype=torch.float32)
            return float(self.model.predict_next(q_tensor, a_tensor, target_q))


@lru_cache(maxsize=1)
def get_models():
    try:
        sakt_model = SAKTModel()

        behaviour_module = _load_module(
            "root_behaviour_model",
            ROOT_ML_DIR / "behaviour" / "model.py",
        )
        forgetting_module = _load_module(
            "root_forgetting_model",
            ROOT_ML_DIR / "forgetting" / "model.py",
        )
        rl_module = _load_module(
            "root_rl_recommender",
            ROOT_ML_DIR / "rl" / "recommender.py",
            extra_sys_path=ROOT_ML_DIR / "rl",
        )

        behaviour_model = behaviour_module.BehaviourModel()
        forgetting_model = forgetting_module.ForgettingModel()
        rl_recommender = rl_module.RLRecommender()
    except FileNotFoundError as exc:
        raise RuntimeError(f"ML model startup failed: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"ML model startup failed: {type(exc).__name__}: {exc}") from exc

    return LoadedModels(
        sakt_model=sakt_model,
        behaviour_model=behaviour_model,
        forgetting_model=forgetting_model,
        rl_recommender=rl_recommender,
    )
