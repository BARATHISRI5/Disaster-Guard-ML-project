# 🛡️ DisasterGuard — AI Disaster Prediction & Response Platform

> Predict natural disasters 24–72 hours in advance using satellite remote sensing + deep learning.  
> **Hackathon:** NOOB HACKFEST @ SRM IST Trichy × NoobTron

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-FF6F00?logo=tensorflow)
![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?logo=pytorch)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)

---

## 🚀 Quick Start (Demo Mode)

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### 1. Backend Setup

```bash
cd disasterguard/backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

# Run in mock data mode (no API keys needed)
set USE_MOCK_DATA=True       # Windows
# export USE_MOCK_DATA=True  # Linux/Mac

uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd disasterguard/frontend
npm install
npm run dev
```

### 3. Open Dashboard
Navigate to `http://localhost:5173` — you'll see the Tamil Nadu risk map immediately.

---

## 🔑 API Keys (Optional — for production use)

Copy `.env.example` to `.env` and fill in:

| Service | Key | Where to get it |
|---------|-----|-----------------|
| Google Earth Engine | `GEE_SERVICE_ACCOUNT_KEY` | [signup.earthengine.google.com](https://signup.earthengine.google.com) |
| Twilio | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE` | [twilio.com/console](https://www.twilio.com/console) |
| Firebase | `FIREBASE_CREDENTIALS_PATH` | [console.firebase.google.com](https://console.firebase.google.com) |

> **Note:** All features work in demo mode (`USE_MOCK_DATA=True`) without any API keys.

---

## 📁 Project Structure

```
disasterguard/
├── backend/
│   ├── main.py                  # FastAPI application
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/
│   │   ├── cnn_model.py         # CNN flood classifier (TensorFlow)
│   │   ├── lstm_model.py        # LSTM time-series forecaster (PyTorch)
│   │   └── risk_engine.py       # Combined risk scoring
│   ├── data/
│   │   ├── fetch_sentinel.py    # Google Earth Engine data fetching
│   │   └── preprocess.py        # Cloud masking, NDWI, patching
│   └── alerts/
│       ├── firebase_push.py     # FCM push notifications
│       └── twilio_sms.py        # SMS alerts via Twilio
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main dashboard layout
│   │   ├── components/          # UI components
│   │   └── api/                 # API client + React Query hooks
│   └── public/
│       └── tn_districts.geojson # Tamil Nadu district boundaries
└── notebooks/
    ├── 01_data_exploration.ipynb
    ├── 02_cnn_training.ipynb
    └── 03_lstm_training.ipynb
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/risk-map?lat=&lon=&radius=` | GeoJSON risk heatmap |
| `GET` | `/api/prediction?district=` | 24/48/72h flood probability |
| `POST` | `/api/alert` | Trigger SMS + push notification |
| `GET` | `/api/damage-assessment?date=&district=` | Pre/post imagery comparison |
| `GET` | `/api/districts` | All TN districts with risk levels |
| `GET` | `/api/time-series?district=` | 7-day environmental data |
| `POST` | `/api/crowd-report` | Submit crowd-sourced report |
| `GET` | `/api/crowd-reports` | Fetch recent crowd reports |
| `GET` | `/api/evacuation-routes?district=` | Evacuation routes + shelters |

---

## 🎯 Demo Scenario

1. **Open dashboard** → Tamil Nadu map with all 38 districts
2. **Select Thoothukudi** → See rising 7-day rainfall chart
3. **LSTM predicts 78%** flood risk in 72 hours
4. **CNN detects** water body expansion in Sentinel-1 SAR
5. **Map lights up red** over Thoothukudi with pulsing animation
6. **Auto-trigger SMS**: *"DISASTERGUARD: Thoothukudi — Flood Risk 78% in 72h"*
7. **Toggle evacuation** overlay → routes and shelters appear
8. **Damage assessment** → side-by-side pre/post flood comparison

---

## 🧠 Model Architecture

### CNN (Spatial Flood Detection)
```
Input(256×256×3) → Conv2D(32) → MaxPool → Conv2D(64) → MaxPool →
Conv2D(128) → MaxPool → Conv2D(128) → MaxPool → Flatten →
Dropout(0.3) → Dense(256) → Dense(1, sigmoid)
```

### LSTM (Time-Series Forecasting)
```
Input(14 days × 6 features) → LSTM(128) → LSTM(64) →
Dense(32) → Dense(3, sigmoid) → [24h, 48h, 72h probabilities]
```

### Risk Score Fusion
```
final_risk = 0.4 × CNN_score + 0.6 × LSTM_score
```

---

## 📜 License

MIT License — Built for NOOB HACKFEST @ SRM IST Trichy × NoobTron
