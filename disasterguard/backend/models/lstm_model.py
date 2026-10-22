"""
DisasterGuard — LSTM Time-Series Forecaster (PyTorch)

Forecasts disaster risk from 14-day sequential environmental data.
Features: rainfall, soil_moisture, wind_speed, river_level, ndwi, temperature
Output: flood probability for 24h, 48h, and 72h windows.
"""

import os
import numpy as np

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# ---------- Dataset ----------

class FloodTimeSeriesDataset:
    """Custom dataset for time-series flood prediction."""
    def __init__(self, sequences, labels):
        if TORCH_AVAILABLE:
            self.sequences = torch.FloatTensor(sequences)
            self.labels = torch.FloatTensor(labels)
        else:
            self.sequences = sequences
            self.labels = labels

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]


# ---------- Model ----------

if TORCH_AVAILABLE:
    class FloodLSTM(nn.Module):
        """
        LSTM model for flood risk forecasting.
        Input: (batch, 14, 6) — 14 days × 6 features
        Output: (batch, 3) — 24h, 48h, 72h flood probabilities
        """
        def __init__(self, input_size=6, hidden1=128, hidden2=64, output_size=3):
            super().__init__()
            self.lstm1 = nn.LSTM(input_size, hidden1, batch_first=True)
            self.dropout1 = nn.Dropout(0.3)
            self.lstm2 = nn.LSTM(hidden1, hidden2, batch_first=True)
            self.dropout2 = nn.Dropout(0.3)
            self.fc1 = nn.Linear(hidden2, 32)
            self.relu = nn.ReLU()
            self.fc2 = nn.Linear(32, output_size)
            self.sigmoid = nn.Sigmoid()

        def forward(self, x):
            out, _ = self.lstm1(x)
            out = self.dropout1(out)
            out, _ = self.lstm2(out)
            out = self.dropout2(out[:, -1, :])  # Take last timestep
            out = self.relu(self.fc1(out))
            return self.sigmoid(self.fc2(out))


# ---------- Training ----------

def build_lstm_model(input_size=6, hidden1=128, hidden2=64):
    """Build and return the LSTM model."""
    if not TORCH_AVAILABLE:
        print("⚠️  PyTorch not installed. Using mock model.")
        return None
    model = FloodLSTM(input_size, hidden1, hidden2)
    print(f"🧠 LSTM Model: {sum(p.numel() for p in model.parameters())} parameters")
    return model


def generate_training_data(num_samples=1000, seq_len=14, num_features=6):
    """Generate synthetic training data for LSTM. Features per timestep:
    [rainfall_mm, soil_moisture_pct, wind_speed_kmh, river_level_m, ndwi, temperature_c]
    """
    sequences, labels = [], []
    for _ in range(num_samples):
        is_flood = np.random.random() > 0.5
        seq = np.zeros((seq_len, num_features))
        if is_flood:
            # Simulating pre-flood conditions: rising rainfall, soil moisture, river levels
            base_rain = np.random.uniform(20, 50)
            for t in range(seq_len):
                seq[t, 0] = base_rain + t * np.random.uniform(5, 15) + np.random.normal(0, 5)  # rainfall
                seq[t, 1] = min(100, 40 + t * 3 + np.random.normal(0, 3))  # soil moisture
                seq[t, 2] = np.random.uniform(20, 60) + t * 2  # wind speed
                seq[t, 3] = 2.0 + t * 0.3 + np.random.normal(0, 0.2)  # river level
                seq[t, 4] = min(0.8, -0.1 + t * 0.05 + np.random.normal(0, 0.02))  # ndwi
                seq[t, 5] = np.random.uniform(25, 35)  # temperature
            # Higher flood probability for later windows
            labels.append([0.65 + np.random.uniform(0, 0.3),
                          0.7 + np.random.uniform(0, 0.25),
                          0.75 + np.random.uniform(0, 0.2)])
        else:
            for t in range(seq_len):
                seq[t, 0] = np.random.uniform(0, 20)  # low rainfall
                seq[t, 1] = np.random.uniform(20, 50)  # normal soil moisture
                seq[t, 2] = np.random.uniform(5, 25)   # calm winds
                seq[t, 3] = np.random.uniform(0.5, 2.0)  # normal river
                seq[t, 4] = np.random.uniform(-0.3, 0.1)  # low ndwi
                seq[t, 5] = np.random.uniform(25, 38)  # temperature
            labels.append([np.random.uniform(0, 0.25),
                          np.random.uniform(0, 0.2),
                          np.random.uniform(0, 0.15)])
        sequences.append(seq)
    return np.array(sequences, dtype=np.float32), np.array(labels, dtype=np.float32)


def train_lstm(model, train_data, val_data, epochs=50, lr=1e-3,
               save_path="models/flood_lstm_model.pt"):
    """Train the LSTM model."""
    if not TORCH_AVAILABLE or model is None:
        print("⚠️  PyTorch not available. Skipping training.")
        return None

    train_loader = DataLoader(train_data, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=32)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

    best_val_loss = float("inf")
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for X, y in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(X), y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for X, y in val_loader:
                val_loss += criterion(model(X), y).item()

        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), save_path)

        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch+1}/{epochs} — Train: {train_loss:.4f}, Val: {val_loss:.4f}")

    print(f"✅ LSTM model saved to {save_path}")
    return {"best_val_loss": best_val_loss}


def load_lstm_model(model_path="models/flood_lstm_model.pt", input_size=6):
    """Load a trained LSTM model from disk."""
    if not TORCH_AVAILABLE:
        return None
    model = FloodLSTM(input_size)
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.eval()
        return model
    print(f"⚠️  Model file not found: {model_path}")
    return None


def predict_flood_timeseries(model, sequence):
    """
    Predict flood probability for 24h, 48h, 72h windows.
    Input: (14, 6) numpy array of daily readings
    Output: dict with 24h, 48h, 72h probabilities
    """
    if model is None:
        return mock_lstm_prediction()
    if not TORCH_AVAILABLE:
        return mock_lstm_prediction()
    model.eval()
    with torch.no_grad():
        x = torch.FloatTensor(sequence).unsqueeze(0)
        pred = model(x).numpy()[0]
    return {"24h": float(pred[0]), "48h": float(pred[1]), "72h": float(pred[2])}


def mock_lstm_prediction(district=None):
    """Generate realistic mock LSTM predictions for demo."""
    presets = {
        "Thoothukudi": {"24h": 0.72, "48h": 0.76, "72h": 0.78},
        "Chennai": {"24h": 0.35, "48h": 0.42, "72h": 0.48},
        "Nagapattinam": {"24h": 0.58, "48h": 0.63, "72h": 0.67},
        "Tirunelveli": {"24h": 0.45, "48h": 0.50, "72h": 0.55},
        "Cuddalore": {"24h": 0.62, "48h": 0.67, "72h": 0.71},
    }
    if district and district in presets:
        base = presets[district]
        noise = np.random.uniform(-0.03, 0.03)
        return {k: float(np.clip(v + noise, 0, 1)) for k, v in base.items()}
    base = np.random.uniform(0.1, 0.7)
    return {"24h": float(np.clip(base, 0, 1)),
            "48h": float(np.clip(base + 0.05, 0, 1)),
            "72h": float(np.clip(base + 0.1, 0, 1))}
