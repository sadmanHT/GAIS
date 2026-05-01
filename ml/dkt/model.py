import torch
import torch.nn as nn

class DKT(nn.Module):
    def __init__(self, n_questions, embed_size=128, hidden_size=128, num_layers=2):
        super(DKT, self).__init__()
        self.n_questions = n_questions
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # Embeddings for each interaction: (question_id, correctness)
        # Pad is 0, incorrect responses are 1 to n_questions, correct ones are n_questions+1 to 2*n_questions
        self.embedding = nn.Embedding(2 * n_questions + 1, embed_size, padding_idx=0)
        
        # LSTM with 2 layers
        self.lstm = nn.LSTM(embed_size, hidden_size, num_layers, batch_first=True)
        
        # Linear output projecting to n_questions + 1 (1-based question IDs, 0 is pad)
        self.fc = nn.Linear(hidden_size, n_questions + 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, q_seq, a_seq):
        """
        q_seq: Encoded question ids (batch_size, seq_len)
        a_seq: Answer correctness, 0 or 1. Padding is usually represented as -1. (batch_size, seq_len)
        """
        # Create interaction encoding: question_id + n_questions * correctness
        # Ensure a_seq is clamped so padding (-1) doesn't cause out-of-bounds before masking
        interaction = q_seq + self.n_questions * a_seq.clamp(min=0).long()
        
        # Apply padding mask: set interaction to 0 where sequence is padded
        interaction = interaction.masked_fill(q_seq == 0, 0)
        
        # Pass through embedding
        embeds = self.embedding(interaction)
        
        # Pass through LSTM
        out, _ = self.lstm(embeds)
        
        # Project and apply sigmoid to get mastery probabilities
        logits = self.fc(out)
        preds = self.sigmoid(logits)
        
        return preds

    def predict_next(self, q_seq, a_seq, target_q):
        """
        Returns the mastery probability for a specific concept given interaction history.
        """
        self.eval()
        with torch.no_grad():
            # If not a tensor, convert to tensor and add batch dimension
            if not isinstance(q_seq, torch.Tensor):
                q_seq = torch.tensor(q_seq).unsqueeze(0)
                a_seq = torch.tensor(a_seq).unsqueeze(0)
                
            preds = self(q_seq, a_seq)
            
            # Predict the mastery for the target question based on output of the last interaction
            # preds is (batch, seq_len, n_questions+1)
            last_step_preds = preds[0, -1, :]
            
            return last_step_preds[target_q].item()
