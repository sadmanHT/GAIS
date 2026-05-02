import os

import torch
import torch.nn as nn
import math
from sklearn.metrics import roc_auc_score
from torch.amp import GradScaler, autocast
from torch.utils.data import DataLoader, TensorDataset

from model import SAKT


def train_sakt():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    amp_device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    batch_size = 512
    n_epochs = 30
    lr = 1e-3
    weight_decay = 1e-2
    patience = 8
    warmup_epochs = 2
    lr_plateau_patience = 3
    lr_plateau_factor = 0.5
    data_dir = "../../data/processed"

    print("Loading data...")
    train_data = torch.load(os.path.join(data_dir, "train.pt"), map_location="cpu", weights_only=True)
    val_data = torch.load(os.path.join(data_dir, "val.pt"), map_location="cpu", weights_only=True)

    n_questions = max(train_data["q"].max().item(), val_data["q"].max().item())
    print(f"Num questions encoded: {n_questions}")

    train_dataset = TensorDataset(train_data["q"], train_data["a"])
    val_dataset = TensorDataset(val_data["q"], val_data["a"])

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        pin_memory=torch.cuda.is_available(),
    )

    model = SAKT(n_questions=n_questions).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    criterion = nn.BCELoss(reduction="none")
    scaler = GradScaler(amp_device, enabled=torch.cuda.is_available())

    best_val_auc = 0.0
    epochs_no_improve = 0
    epochs_no_improve_lr = 0
    plateau_scale = 1.0

    for epoch in range(n_epochs):
        if epoch < warmup_epochs:
            schedule_scale = (epoch + 1) / warmup_epochs
        else:
            progress = (epoch - warmup_epochs) / max(n_epochs - warmup_epochs, 1)
            schedule_scale = 0.5 * (1.0 + math.cos(math.pi * progress))

        current_lr = lr * schedule_scale * plateau_scale
        for group in optimizer.param_groups:
            group["lr"] = current_lr

        model.train()
        total_loss = 0.0
        valid_batches = 0

        for q_batch, a_batch in train_loader:
            q_batch = q_batch.to(device, non_blocking=True)
            a_batch = a_batch.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)

            with autocast(amp_device, enabled=torch.cuda.is_available()):
                q_target = q_batch[:, 1:].long()
                a_target = a_batch[:, 1:]
                mask = (a_target != -1) & (q_target > 0)
                if not mask.any():
                    continue

                target_preds = model(q_batch, a_batch, target_q=q_target)
                valid_preds = target_preds[mask]
                valid_targets = a_target[mask]
                smoothed_targets = valid_targets * 0.90 + 0.05
                loss = criterion(valid_preds, smoothed_targets).mean()

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()

            total_loss += loss.item() * q_batch.size(0)
            valid_batches += q_batch.size(0)

        train_loss = total_loss / max(valid_batches, 1)

        model.eval()
        val_preds_all = []
        val_targets_all = []

        with torch.no_grad():
            for q_batch, a_batch in val_loader:
                q_batch = q_batch.to(device, non_blocking=True)
                a_batch = a_batch.to(device, non_blocking=True)

                q_target = q_batch[:, 1:].long()
                a_target = a_batch[:, 1:]
                mask = (a_target != -1) & (q_target > 0)
                if not mask.any():
                    continue

                target_preds = model(q_batch, a_batch, target_q=q_target)
                valid_preds = target_preds[mask]
                valid_targets = a_target[mask]

                val_preds_all.extend(valid_preds.detach().cpu().numpy())
                val_targets_all.extend(valid_targets.detach().cpu().numpy())

        if len(set(val_targets_all)) < 2:
            print("Validation split has fewer than two target classes; skipping AUC for this epoch.")
            continue

        val_auc = roc_auc_score(val_targets_all, val_preds_all)
        print(
            f"Epoch {epoch + 1:02d}/{n_epochs} | "
            f"LR: {current_lr:.2e} | Loss: {train_loss:.4f} | Val AUC-ROC: {val_auc:.4f}"
        )

        if val_auc > best_val_auc:
            best_val_auc = val_auc
            torch.save(model.state_dict(), "sakt_best.pt")
            epochs_no_improve = 0
            epochs_no_improve_lr = 0
            print(f"  --> Saved new best model with Val AUC: {best_val_auc:.4f}")
        else:
            epochs_no_improve += 1
            epochs_no_improve_lr += 1
            print(f"  --> No improvement. Patience counter: {epochs_no_improve}/{patience}")
            if epochs_no_improve_lr >= lr_plateau_patience:
                plateau_scale *= lr_plateau_factor
                epochs_no_improve_lr = 0
                print(f"  --> Reducing LR by {lr_plateau_factor}; next epoch LR scale is {plateau_scale:.4f}")
            if epochs_no_improve >= patience:
                print("Early stopping triggered. Training stopped.")
                break


if __name__ == "__main__":
    train_sakt()
