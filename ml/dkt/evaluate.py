import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from sklearn.metrics import roc_auc_score
from torch.utils.data import DataLoader, TensorDataset

from model import SAKT


def evaluate():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Evaluating on device: {device}")

    data_dir = "../../data/processed"
    model_candidates = [
        "sakt_best.pt",
        "../sakt_best.pt",
        "../../ml/sakt_best.pt",
        "../../backend/ml/sakt_best.pt",
    ]
    model_path = next((path for path in model_candidates if os.path.exists(path)), None)
    if model_path is None:
        print(f"Failed to find SAKT weights in: {model_candidates}")
        return

    print("Loading test data...")
    test_data = torch.load(os.path.join(data_dir, "test.pt"), map_location="cpu", weights_only=True)
    state_dict = torch.load(model_path, map_location=device, weights_only=True)

    n_questions = state_dict["pred_layer.weight"].shape[0] - 1
    test_data["q"][test_data["q"] > n_questions] = 0

    model = SAKT(n_questions=n_questions).to(device)
    try:
        model.load_state_dict(state_dict)
        print(f"Successfully loaded {model_path}")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    model.eval()
    test_loader = DataLoader(TensorDataset(test_data["q"], test_data["a"]), batch_size=256, shuffle=False)

    all_preds = []
    all_targets = []
    first_10_correct, first_10_total = 0, 0
    last_10_correct, last_10_total = 0, 0

    with torch.no_grad():
        for q_batch, a_batch in test_loader:
            q_batch = q_batch.to(device)
            a_batch = a_batch.to(device)

            q_target = q_batch[:, 1:].long()
            a_target = a_batch[:, 1:]
            mask = (a_target != -1) & (q_target > 0)
            gathered_preds = model(q_batch, a_batch, target_q=q_target)

            valid_preds = gathered_preds[mask]
            valid_targets = a_target[mask]

            all_preds.extend(valid_preds.cpu().numpy())
            all_targets.extend(valid_targets.cpu().numpy())

            for i in range(q_target.size(0)):
                valid_idx = torch.where((a_target[i] != -1) & (q_target[i] > 0))[0]
                if len(valid_idx) >= 20:
                    f_idx = valid_idx[:10]
                    l_idx = valid_idx[-10:]

                    f_pred = gathered_preds[i, f_idx] > 0.5
                    f_tgt = a_target[i, f_idx] == 1.0
                    first_10_correct += (f_pred == f_tgt).sum().item()
                    first_10_total += 10

                    l_pred = gathered_preds[i, l_idx] > 0.5
                    l_tgt = a_target[i, l_idx] == 1.0
                    last_10_correct += (l_pred == l_tgt).sum().item()
                    last_10_total += 10

    auc = roc_auc_score(all_targets, all_preds)
    acc_first = (first_10_correct / first_10_total) if first_10_total > 0 else 0.0
    acc_last = (last_10_correct / last_10_total) if last_10_total > 0 else 0.0

    print(f"\n{'=' * 40}")
    print("SAKT MODEL EVALUATION SUMMARY")
    print(f"{'=' * 40}")
    print(f"Test AUC-ROC:        {auc:.4f} (Target: > 0.78)")
    print(f"Accuracy (First 10): {acc_first * 100:.2f}%")
    print(f"Accuracy (Last 10):  {acc_last * 100:.2f}%")
    print(f"Learning Gain:       {(acc_last - acc_first) * 100:+.2f}%")

    if auc > 0.78:
        print("\nSUCCESS: Target AUC-ROC reached!")
    else:
        print("\nWARNING: AUC-ROC is below the 0.78 target.")

    print(f"{'=' * 40}")

    try:
        plt.figure(figsize=(7, 5))
        bars = plt.bar(
            ["First 10\nQuestions", "Last 10\nQuestions"],
            [acc_first * 100, acc_last * 100],
            color=["#ff9999", "#66b3ff"],
        )

        plt.title("SAKT Model: Student Learning Curve (Accuracy Over Time)")
        plt.ylabel("Accuracy (%)")
        plt.ylim(0, 100)

        for bar in bars:
            yval = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                yval + 1,
                f"{yval:.1f}%",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.tight_layout()
        plt.savefig("accuracy_learning_curve.png", dpi=150)
        print("\nPlot saved successfully to accuracy_learning_curve.png")
    except Exception as e:
        print(f"Failed to generate plot (Install matplotlib): {e}")


if __name__ == "__main__":
    evaluate()
