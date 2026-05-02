import os
import pandas as pd
import torch
from torch.nn.utils.rnn import pad_sequence
from sklearn.model_selection import train_test_split

def process_data(input_csv="train.csv", output_dir="../../data/processed", max_seq_len=200, max_rows=5000000):
    print(f"Loading data from {input_csv} (max {max_rows} rows)...")
    # Load dataset
    df = pd.read_csv(input_csv, nrows=max_rows)
    
    # Riiid dataset specific: filter out lectures (content_type_id == 1)
    if 'content_type_id' in df.columns:
        df = df[df.content_type_id == 0]
        
    df = df[['user_id', 'content_id', 'answered_correctly']]
    df.columns = ['user_id', 'question_id', 'answered_correctly']
    
    print("Encoding question IDs...")
    # Encode question_ids as integers
    q_unique = df['question_id'].unique()
    q_mapping = {q: i + 1 for i, q in enumerate(q_unique)} # 0 reserved for padding
    df['question_id'] = df['question_id'].map(q_mapping)
    
    print("Grouping into sequences...")
    # Group by user_id
    grouped = df.groupby('user_id').agg({
        'question_id': list,
        'answered_correctly': list
    })
    
    # Convert lists to tensors
    sequences_q = [torch.tensor(q, dtype=torch.long) for q in grouped['question_id']]
    sequences_a = [torch.tensor(a, dtype=torch.float32) for a in grouped['answered_correctly']]
    
    print(f"Padding sequences to length {max_seq_len}...")
    # Truncate sequences that are too long
    sequences_q = [q[-max_seq_len:] for q in sequences_q]
    sequences_a = [a[-max_seq_len:] for a in sequences_a]
    
    # Pad sequences
    padded_q = pad_sequence(sequences_q, batch_first=True, padding_value=0)
    padded_a = pad_sequence(sequences_a, batch_first=True, padding_value=-1) # -1 for padding in answers
    
    # If padding didn't reach max_seq_len for all, add explicit padding
    if padded_q.size(1) < max_seq_len:
        pad_size = max_seq_len - padded_q.size(1)
        padded_q = torch.cat([padded_q, torch.zeros(padded_q.size(0), pad_size, dtype=torch.long)], dim=1)
        padded_a = torch.cat([padded_a, torch.full((padded_a.size(0), pad_size), -1, dtype=torch.float32)], dim=1)
    
    print("Splitting dataset...")
    # Split 80 / 10 / 10
    total_users = padded_q.size(0)
    indices = list(range(total_users))
    
    train_idx, temp_idx = train_test_split(indices, test_size=0.2, random_state=42)
    val_idx, test_idx = train_test_split(temp_idx, test_size=0.5, random_state=42)
    
    print("Saving tensors...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save splits
    torch.save({
        'q': padded_q[train_idx],
        'a': padded_a[train_idx]
    }, os.path.join(output_dir, "train.pt"))
    
    torch.save({
        'q': padded_q[val_idx],
        'a': padded_a[val_idx]
    }, os.path.join(output_dir, "val.pt"))
    
    torch.save({
        'q': padded_q[test_idx],
        'a': padded_a[test_idx]
    }, os.path.join(output_dir, "test.pt"))
    
    print(f"Preprocessing complete. Saved {len(train_idx)} train, {len(val_idx)} val, {len(test_idx)} test sequences.")
    print(f"Unique questions encoded: {len(q_unique)}")

if __name__ == "__main__":
    # Update path below if the csv is located elsewhere
    process_data(input_csv="../../data/raw/train.csv")
