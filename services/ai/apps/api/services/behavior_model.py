"""
behavior_model.py
=================
Deep Learning model cho phân tích hành vi người dùng trong hệ thống E-Commerce.

Architecture:
  1. EventEncoder  – Encode chuỗi hành vi (search, click, cart, purchase) thành vector
  2. AttentionLayer – Self-attention để tập trung vào hành vi quan trọng nhất
  3. BehaviorLSTM  – LSTM xử lý chuỗi thời gian hành vi
  4. IntentClassifier – Phân loại ý định mua hàng (Browsing / Interested / High-Intent / Ready-to-Buy)

Training pipeline:
  - generate_synthetic_data(): Tạo dữ liệu huấn luyện tổng hợp
  - train():                   Vòng lặp huấn luyện full epoch
  - save_weights() / load_weights(): Lưu / Tải trọng số mô hình
"""

import os
import json
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Mã hoá hành vi thành ID
EVENT_VOCAB = {
    "<PAD>": 0,
    "search": 1,
    "view": 2,
    "click": 3,
    "add_to_cart": 4,
    "remove_from_cart": 5,
    "purchase": 6,
    "wishlist": 7,
    "review": 8,
}

# Nhãn ý định mua hàng (output classes)
INTENT_LABELS = {
    0: "Browsing",        # Chỉ lướt, chưa có ý định rõ
    1: "Interested",      # Quan tâm sản phẩm
    2: "High-Intent",     # Có ý định mua cao
    3: "Ready-to-Buy",    # Sẵn sàng mua ngay
}

# Trọng số hành vi dùng để tính interest score (α · clicks + β · cart + γ · purchase)
BEHAVIOR_WEIGHTS = {
    "search": 0.1,
    "view": 0.2,
    "click": 0.3,
    "add_to_cart": 0.5,
    "remove_from_cart": -0.2,
    "purchase": 1.0,
    "wishlist": 0.4,
    "review": 0.3,
}

VOCAB_SIZE   = len(EVENT_VOCAB)
EMBED_DIM    = 32
HIDDEN_DIM   = 64
NUM_LAYERS   = 2
NUM_CLASSES  = len(INTENT_LABELS)
MAX_SEQ_LEN  = 20
DROPOUT      = 0.3

WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "behavior_weights.pth")


# ---------------------------------------------------------------------------
# Attention Layer
# ---------------------------------------------------------------------------
class SelfAttention(nn.Module):
    """
    Scaled dot-product self-attention trên output của LSTM.
    Trả về context vector là tổng có trọng số của tất cả hidden states.
    """

    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attn = nn.Linear(hidden_dim, 1)

    def forward(self, lstm_out: torch.Tensor) -> torch.Tensor:
        # lstm_out: (batch, seq_len, hidden_dim)
        scores = self.attn(lstm_out).squeeze(-1)          # (batch, seq_len)
        weights = torch.softmax(scores, dim=-1).unsqueeze(-1)  # (batch, seq_len, 1)
        context = (lstm_out * weights).sum(dim=1)          # (batch, hidden_dim)
        return context


# ---------------------------------------------------------------------------
# Core Deep Learning Model
# ---------------------------------------------------------------------------
class BehaviorLSTMWithAttention(nn.Module):
    """
    LSTM + Self-Attention model để phân tích chuỗi hành vi người dùng.

    Input:  LongTensor (batch, seq_len) – chuỗi event IDs
    Output: FloatTensor (batch, num_classes) – logits cho từng intent class
    """

    def __init__(
        self,
        vocab_size: int = VOCAB_SIZE,
        embed_dim: int = EMBED_DIM,
        hidden_dim: int = HIDDEN_DIM,
        num_layers: int = NUM_LAYERS,
        num_classes: int = NUM_CLASSES,
        dropout: float = DROPOUT,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.attention = SelfAttention(hidden_dim)
        self.dropout   = nn.Dropout(dropout)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        embedded  = self.dropout(self.embedding(x))          # (B, T, E)
        lstm_out, _ = self.lstm(embedded)                    # (B, T, H)
        context   = self.attention(lstm_out)                 # (B, H)
        logits    = self.classifier(context)                 # (B, C)
        return logits


# ---------------------------------------------------------------------------
# Synthetic Dataset for demo / cold-start training
# ---------------------------------------------------------------------------
class BehaviorDataset(Dataset):
    """Tập dữ liệu tổng hợp cho mục đích demo / cold-start."""

    def __init__(self, sequences, labels, max_len: int = MAX_SEQ_LEN):
        self.sequences = sequences
        self.labels    = labels
        self.max_len   = max_len

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        seq = self.sequences[idx][:self.max_len]
        # Padding
        padded = seq + [0] * (self.max_len - len(seq))
        return (
            torch.tensor(padded, dtype=torch.long),
            torch.tensor(self.labels[idx], dtype=torch.long),
        )


def generate_synthetic_data(n_samples: int = 1000):
    """
    Tạo dữ liệu tổng hợp:
    - Nhãn 0 (Browsing):     nhiều search/view, ít click
    - Nhãn 1 (Interested):   search → view → click
    - Nhãn 2 (High-Intent):  click → add_to_cart lặp lại
    - Nhãn 3 (Ready-to-Buy): add_to_cart → purchase
    """
    rng = np.random.default_rng(42)
    sequences, labels = [], []
    templates = {
        0: [1, 2, 1, 2, 1],           # search, view, ...
        1: [1, 2, 3, 2, 3],           # search, view, click
        2: [3, 4, 3, 4, 3],           # click, cart, ...
        3: [4, 4, 6, 4, 6],           # cart, purchase
    }
    for label, base_seq in templates.items():
        for _ in range(n_samples // 4):
            noise_len = rng.integers(1, MAX_SEQ_LEN - len(base_seq) + 1)
            noise     = rng.choice(list(EVENT_VOCAB.values()), size=noise_len).tolist()
            seq       = base_seq + noise
            sequences.append(seq)
            labels.append(label)
    return sequences, labels


# ---------------------------------------------------------------------------
# High-level wrapper – used by views.py
# ---------------------------------------------------------------------------
class UserBehaviorModel:
    """
    Production-ready wrapper trên BehaviorLSTMWithAttention.

    Cung cấp:
      - predict_intent(event_sequence) → intent label string
      - compute_interest_score(event_counts) → float score
      - train(epochs, lr) → training metrics dict
      - save_weights() / load_weights()
    """

    def __init__(self, auto_train: bool = False):
        self.model = BehaviorLSTMWithAttention()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        # Tải trọng số nếu đã tồn tại
        if os.path.exists(WEIGHTS_PATH):
            self.load_weights()
            logger.info("Loaded pre-trained behavior model weights.")
        elif auto_train:
            logger.info("No weights found – running cold-start training.")
            self.train()
        else:
            logger.info("No weights found – using random-initialized model (demo mode).")

        self.model.eval()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def encode_events(self, event_names: list) -> list:
        """Chuyển tên hành vi → list ID."""
        return [EVENT_VOCAB.get(e, 0) for e in event_names]

    def predict_intent(self, event_sequence: list) -> dict:
        """
        Nhận chuỗi event IDs hoặc event names, trả về dict kết quả.

        Args:
            event_sequence: list[int | str] – chuỗi hành vi người dùng

        Returns:
            {
              "intent": "High-Intent",
              "confidence": 0.82,
              "scores": { "Browsing": 0.03, ... },
              "interest_score": 0.67
            }
        """
        if not event_sequence:
            return {
                "intent": "Browsing",
                "confidence": 1.0,
                "scores": {v: 0.0 for v in INTENT_LABELS.values()},
                "interest_score": 0.0,
            }

        # Encode nếu là string
        if isinstance(event_sequence[0], str):
            ids = self.encode_events(event_sequence)
        else:
            ids = list(event_sequence)

        # Padding / truncation
        ids = ids[:MAX_SEQ_LEN]
        padded = ids + [0] * (MAX_SEQ_LEN - len(ids))

        x = torch.tensor([padded], dtype=torch.long).to(self.device)
        with torch.no_grad():
            logits = self.model(x)                         # (1, 4)
            probs  = torch.softmax(logits, dim=-1)[0]      # (4,)

        pred_idx    = probs.argmax().item()
        confidence  = probs[pred_idx].item()
        scores = {INTENT_LABELS[i]: round(probs[i].item(), 4) for i in range(NUM_CLASSES)}

        # Tính interest score dựa trên trọng số hành vi
        interest = self.compute_interest_score(
            {name: ids.count(eid) for name, eid in EVENT_VOCAB.items() if name != "<PAD>"}
        )

        return {
            "intent": INTENT_LABELS[pred_idx],
            "confidence": round(confidence, 4),
            "scores": scores,
            "interest_score": round(interest, 4),
        }

    # Alias kept for backward compatibility with old views.py
    def predict_next(self, event_sequence: list) -> str:
        result = self.predict_intent(event_sequence)
        return result["intent"]

    def compute_interest_score(self, event_counts: dict) -> float:
        """
        Tính điểm quan tâm theo công thức trọng số:
        score = Σ weight_i * count_i  (chuẩn hoá về [0, 1])
        """
        raw = sum(
            BEHAVIOR_WEIGHTS.get(event, 0.0) * count
            for event, count in event_counts.items()
        )
        # Clamp vào [0, 1]
        return min(max(raw / 5.0, 0.0), 1.0)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def train(
        self,
        epochs: int = 10,
        lr: float = 1e-3,
        batch_size: int = 32,
    ) -> dict:
        """
        Chạy vòng lặp huấn luyện trên dữ liệu tổng hợp.
        Trong production, thay thế bằng dữ liệu thực từ interaction-service.
        """
        self.model.train()
        sequences, labels = generate_synthetic_data(n_samples=1000)
        dataset    = BehaviorDataset(sequences, labels)
        loader     = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        optimizer  = optim.Adam(self.model.parameters(), lr=lr)
        criterion  = nn.CrossEntropyLoss()
        scheduler  = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

        history = {"loss": [], "accuracy": []}

        for epoch in range(epochs):
            epoch_loss, correct, total = 0.0, 0, 0
            for x_batch, y_batch in loader:
                x_batch = x_batch.to(self.device)
                y_batch = y_batch.to(self.device)

                optimizer.zero_grad()
                logits = self.model(x_batch)
                loss   = criterion(logits, y_batch)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()

                epoch_loss += loss.item() * x_batch.size(0)
                preds       = logits.argmax(dim=1)
                correct    += (preds == y_batch).sum().item()
                total      += x_batch.size(0)

            scheduler.step()
            avg_loss = epoch_loss / total
            accuracy = correct / total
            history["loss"].append(round(avg_loss, 4))
            history["accuracy"].append(round(accuracy, 4))
            logger.info(f"Epoch {epoch+1}/{epochs} – loss: {avg_loss:.4f}  acc: {accuracy:.4f}")

        self.model.eval()
        self.save_weights()
        return history

    def save_weights(self):
        torch.save(self.model.state_dict(), WEIGHTS_PATH)
        logger.info(f"Model weights saved to {WEIGHTS_PATH}")

    def load_weights(self):
        state = torch.load(WEIGHTS_PATH, map_location=self.device)
        self.model.load_state_dict(state)
        logger.info(f"Model weights loaded from {WEIGHTS_PATH}")
