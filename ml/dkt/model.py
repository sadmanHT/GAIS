import torch
import torch.nn as nn
import numpy as np

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=1000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        seq_len = x.size(1)
        return x + self.pe[:, :seq_len, :]

class SAKT(nn.Module):
    def __init__(self, n_questions, d_model=256, n_heads=8, dropout=0.2, max_seq_len=200):
        super().__init__()
        self.d_model = d_model
        
        # Interaction embedding: Question ID + correctness (offset by n_questions)
        self.interaction_emb = nn.Embedding(2 * n_questions + 1, d_model, padding_idx=0)
        
        # Question embedding (for queries)
        self.question_emb = nn.Embedding(n_questions + 1, d_model, padding_idx=0)
        
        self.pos_encoder = PositionalEncoding(d_model, max_len=max_seq_len)
        
        self.attention = nn.MultiheadAttention(embed_dim=d_model, num_heads=n_heads, dropout=dropout, batch_first=True)
        
        self.layer_norm1 = nn.LayerNorm(d_model)
        self.layer_norm2 = nn.LayerNorm(d_model)
        
        self.dropout = nn.Dropout(dropout)
        
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model)
        )
        
        self.pred_layer = nn.Linear(d_model, n_questions + 1)

    def forward(self, q, a):
        device = q.device
        
        interaction_tokens = q + self.question_emb.num_embeddings * a.clamp(min=0).long()
        interaction_tokens = interaction_tokens.masked_fill(q == 0, 0)
        
        interactions = self.interaction_emb(interaction_tokens)
        interactions = self.pos_encoder(interactions)
        
        questions = self.question_emb(q)
        
        seq_len = q.size(1)
        attn_mask = torch.triu(torch.ones(seq_len, seq_len, device=device) * float('-inf'), diagonal=1)
        
        attn_out, _ = self.attention(
            query=questions, 
            key=interactions, 
            value=interactions, 
            attn_mask=attn_mask,
            need_weights=False
        )
        
        out = self.layer_norm1(questions + self.dropout(attn_out))
        ffn_out = self.ffn(out)
        out = self.layer_norm2(out + self.dropout(ffn_out))
        
        logits = self.pred_layer(out) 
        preds = torch.sigmoid(logits)
        return preds

    def predict_next(self, q_seq, a_seq, target_q):
        self.eval()
        with torch.no_grad():
            if not isinstance(q_seq, torch.Tensor):
                q_seq = torch.tensor(q_seq).unsqueeze(0)
                a_seq = torch.tensor(a_seq).unsqueeze(0)
                
            preds = self(q_seq, a_seq)
            last_step_preds = preds[0, -1, :]
            
            return last_step_preds[target_q].item()

