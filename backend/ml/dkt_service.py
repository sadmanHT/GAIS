import math
import os

import torch
import torch.nn as nn


MAX_SEQ_LEN = 200
device = torch.device("cpu")


class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=MAX_SEQ_LEN):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, : x.size(1), :]


class SAKT(nn.Module):
    def __init__(self, n_questions, d_model=128, n_heads=4, dropout=0.3, max_seq_len=MAX_SEQ_LEN):
        super().__init__()
        self.n_questions = n_questions

        self.question_emb = nn.Embedding(n_questions + 1, d_model, padding_idx=0)
        self.interaction_emb = nn.Embedding(2 * n_questions + 1, d_model, padding_idx=0)
        self.pos_encoder = PositionalEncoding(d_model, max_len=max_seq_len)
        self.pos_dropout = nn.Dropout(dropout)

        self.attention = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=n_heads,
            dropout=dropout,
            batch_first=True,
        )
        self.layer_norm1 = nn.LayerNorm(d_model)
        self.layer_norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model),
        )
        self.pred_layer = nn.Linear(d_model, n_questions + 1)

    def _encode(self, q_seq, a_seq, target_q=None):
        if target_q is None:
            context_q = q_seq
            context_a = a_seq
            questions = self.question_emb(q_seq)
        else:
            context_q = q_seq[:, : target_q.size(1)]
            context_a = a_seq[:, : target_q.size(1)]
            questions = self.question_emb(target_q.clamp(min=0, max=self.n_questions))

        interaction = context_q + self.n_questions * context_a.clamp(min=0).long()
        interaction = interaction.masked_fill(context_q == 0, 0)
        interactions = self.pos_dropout(self.pos_encoder(self.interaction_emb(interaction)))

        seq_len = questions.size(1)
        attn_mask = torch.triu(
            torch.full((seq_len, seq_len), float("-inf"), device=q_seq.device),
            diagonal=1,
        )
        attn_out, _ = self.attention(
            query=questions,
            key=interactions,
            value=interactions,
            attn_mask=attn_mask,
            need_weights=False,
        )
        out = self.layer_norm1(questions + self.dropout(attn_out))
        ffn_out = self.ffn(out)
        return self.layer_norm2(out + self.dropout(ffn_out))

    def forward(self, q_seq, a_seq, target_q=None):
        encoded = self._encode(q_seq, a_seq, target_q=target_q)
        if target_q is not None:
            target_q = target_q.long().clamp(min=0, max=self.n_questions)
            target_weight = self.pred_layer.weight[target_q]
            target_bias = self.pred_layer.bias[target_q]
            logits = (encoded * target_weight).sum(dim=-1) + target_bias
            return torch.sigmoid(logits)
        return torch.sigmoid(self.pred_layer(encoded))

    def predict_next(self, q_seq, a_seq, target_q):
        self.eval()
        with torch.no_grad():
            if not isinstance(q_seq, torch.Tensor):
                q_seq = torch.tensor(q_seq, dtype=torch.long).unsqueeze(0)
            if not isinstance(a_seq, torch.Tensor):
                a_seq = torch.tensor(a_seq, dtype=torch.float32).unsqueeze(0)

            q_seq = q_seq[:, -MAX_SEQ_LEN:].to(device)
            a_seq = a_seq[:, -MAX_SEQ_LEN:].to(device)
            target_q = int(target_q)
            if target_q <= 0 or target_q > self.n_questions:
                return 0.5
            preds = self(q_seq, a_seq)
            return preds[0, -1, target_q].item()


def _candidate_model_paths():
    here = os.path.dirname(__file__)
    return [
        os.path.join(here, "sakt_best.pt"),
        os.path.abspath(os.path.join(here, "..", "..", "ml", "sakt_best.pt")),
    ]


def _load_state_dict():
    for path in _candidate_model_paths():
        if os.path.exists(path):
            return path, torch.load(path, map_location=device, weights_only=True)
    return None, None


model_path, state_dict = _load_state_dict()
if state_dict:
    N_QUESTIONS = state_dict["pred_layer.weight"].shape[0] - 1
else:
    N_QUESTIONS = 13500

sakt_model = SAKT(n_questions=N_QUESTIONS).to(device)


def load_weights():
    if state_dict:
        sakt_model.load_state_dict(state_dict)
        sakt_model.eval()
        print(f"Loaded SAKT model weights successfully from {model_path}.")
    else:
        print(f"Warning: SAKT weights not found in {_candidate_model_paths()}!")


load_weights()


def predict_mastery(q_seq_list, a_seq_list, target_q_ids):
    """
    Returns a dictionary of {question_id: mastery_probability}.
    Question IDs are expected to use the same encoded IDs as the SAKT training data.
    """
    valid_targets = [int(q) for q in target_q_ids if 0 < int(q) <= N_QUESTIONS]
    if not q_seq_list:
        return {q: 0.5 for q in target_q_ids}

    q_seq = [int(q) if 0 < int(q) <= N_QUESTIONS else 0 for q in q_seq_list][-MAX_SEQ_LEN:]
    a_seq = [float(a) for a in a_seq_list][-MAX_SEQ_LEN:]

    masteries = {}
    for target_q in target_q_ids:
        if int(target_q) not in valid_targets:
            masteries[target_q] = 0.5
            continue
        prob = sakt_model.predict_next(q_seq, a_seq, int(target_q))
        masteries[target_q] = round(prob, 4)

    return masteries
