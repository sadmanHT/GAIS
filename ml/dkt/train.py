import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torch.amp import autocast, GradScaler
from sklearn.metrics import roc_auc_score
from model import DKT

def train_dkt():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Hyperparameters
    batch_size = 256
    n_epochs = 20
    lr = 3e-4
    weight_decay = 1e-2
    patience = 3
    data_dir = "../../data/processed"

    print("Loading data...")
    train_data = torch.load(os.path.join(data_dir, "train.pt"), map_location="cpu", weights_only=True)
    val_data = torch.load(os.path.join(data_dir, "val.pt"), map_location="cpu", weights_only=True)

    # Determine num_questions dynamically from maximum ID in chunks
    n_questions = max(train_data['q'].max().item(), val_data['q'].max().item())
    
    print(f"Num questions encoded: {n_questions}")

    train_dataset = TensorDataset(train_data['q'], train_data['a'])
    val_dataset = TensorDataset(val_data['q'], val_data['a'])

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    model = DKT(n_questions=n_questions).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    
    # Use reduction='none' because we need to ignore padding (-1s) via a mask
    criterion = nn.BCELoss(reduction='none')
    scaler = GradScaler('cuda' if torch.cuda.is_available() else 'cpu')

    best_val_auc = 0.0
    epochs_no_improve = 0

    for epoch in range(n_epochs):
        model.train()
        total_loss = 0.0
        
        for q_batch, a_batch in train_loader:
            q_batch, a_batch = q_batch.to(device), a_batch.to(device)
            optimizer.zero_grad()
            
            with autocast('cuda' if torch.cuda.is_available() else 'cpu'):
                # Forward pass
                preds = model(q_batch, a_batch)
                
                # For t+1 prediction given data up to t
                # We align targets shifted left by 1.
                q_target = q_batch[:, 1:].clone().long()
                a_target = a_batch[:, 1:].clone()
                preds_subset = preds[:, :-1, :]
                
                # Check where targets are valid
                mask = (a_target != -1)
                
                # Gather the predicted prob for the specific target question IDs asked at t+1
                # Because q_target values represent column indices. Unpack output using gather.
                gathered_preds = torch.gather(preds_subset, 2, q_target.unsqueeze(2)).squeeze(2)
                
                # Apply BCE loss on valid targets
                loss_unreduced = criterion(gathered_preds[mask], a_target[mask])
                loss = loss_unreduced.mean()
                
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            total_loss += loss.item() * q_batch.size(0)
            
        train_loss = total_loss / len(train_dataset)

        # Evaluate on validation
        model.eval()
        val_preds_all = []
        val_targets_all = []
        
        with torch.no_grad():
            for q_batch, a_batch in val_loader:
                q_batch, a_batch = q_batch.to(device), a_batch.to(device)
                
                # Forward pass
                preds = model(q_batch, a_batch)
                
                # Align prediction
                q_target = q_batch[:, 1:].clone().long()
                a_target = a_batch[:, 1:].clone()
                preds_subset = preds[:, :-1, :]
                mask = (a_target != -1)
                
                gathered_preds = torch.gather(preds_subset, 2, q_target.unsqueeze(2)).squeeze(2)
                
                # Collect predictions and valid targets to compute ROC AUC
                val_preds_all.extend(gathered_preds[mask].cpu().numpy())
                val_targets_all.extend(a_target[mask].cpu().numpy())
                
        # Calculate Validation AUC-ROC
        val_auc = roc_auc_score(val_targets_all, val_preds_all)
        
        print(f"Epoch {epoch+1:02d}/{n_epochs} | Loss: {train_loss:.4f} | Val AUC-ROC: {val_auc:.4f}")
        
        # Early Stopping and Checkpoint saving
        if val_auc > best_val_auc:
            best_val_auc = val_auc
            torch.save(model.state_dict(), "dkt_best.pt")
            epochs_no_improve = 0
            print(f"  --> Saved new best model with Val AUC: {best_val_auc:.4f}")
        else:
            epochs_no_improve += 1
            print(f"  --> No improvement. Patience counter: {epochs_no_improve}/{patience}")
            if epochs_no_improve >= patience:
                print("Early stopping triggered. Training stopped.")
                break

if __name__ == "__main__":
    train_dkt()