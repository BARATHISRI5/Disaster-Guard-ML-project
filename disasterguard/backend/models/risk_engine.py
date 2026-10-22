"""
DisasterGuard - Risk Engine

Combines CNN spatial flood detection + LSTM time-series forecast into a
unified risk score. Generates GeoJSON risk heatmaps and damage assessments.

Risk Formula: final_risk = 0.4 * CNN_score + 0.6 * LSTM_score
Risk Levels: <0.3 safe (green), 0.3-0.65 moderate (amber), >0.65 critical (red)
"""

import numpy as np
from datetime import datetime, timedelta

# All 38 Tamil Nadu districts with approximate centroids [lat, lon]
TN_DISTRICTS = {
    "Ariyalur": [11.14, 79.08], "Chengalpattu": [12.69, 79.98],
    "Chennai": [13.08, 80.27], "Coimbatore": [11.01, 76.97],
    "Cuddalore": [11.75, 79.77], "Dharmapuri": [12.13, 78.16],
    "Dindigul": [10.37, 77.97], "Erode": [11.34, 77.72],
    "Kallakurichi": [11.74, 78.96], "Kancheepuram": [12.83, 79.71],
    "Kanyakumari": [8.08, 77.57], "Karur": [10.96, 78.08],
    "Krishnagiri": [12.52, 78.21], "Madurai": [9.92, 78.12],
    "Mayiladuthurai": [11.10, 79.65], "Nagapattinam": [10.77, 79.84],
    "Namakkal": [11.22, 78.17], "Nilgiris": [11.41, 76.73],
    "Perambalur": [11.23, 78.88], "Pudukkottai": [10.38, 78.82],
    "Ramanathapuram": [9.37, 78.83], "Ranipet": [12.93, 79.33],
    "Salem": [11.66, 78.15], "Sivaganga": [10.00, 78.50],
    "Tenkasi": [8.96, 77.31], "Thanjavur": [10.79, 79.14],
    "Theni": [10.01, 77.48], "Thoothukudi": [8.76, 78.13],
    "Tiruchirappalli": [10.80, 78.69], "Tirunelveli": [8.73, 77.70],
    "Tirupathur": [12.50, 78.57], "Tiruppur": [11.11, 77.35],
    "Tiruvallur": [13.14, 79.91], "Tiruvannamalai": [12.23, 79.07],
    "Tiruvarur": [10.77, 79.64], "Vellore": [12.92, 79.13],
    "Viluppuram": [11.94, 79.49], "Virudhunagar": [9.59, 77.96],
}

# Pre-set risk levels for demo scenario (simulating active flood event)
DEMO_RISK_PRESETS = {
    "Thoothukudi": 0.82, "Nagapattinam": 0.71, "Cuddalore": 0.68,
    "Tirunelveli": 0.55, "Chennai": 0.48, "Ramanathapuram": 0.62,
    "Tiruvarur": 0.58, "Thanjavur": 0.42, "Mayiladuthurai": 0.52,
    "Viluppuram": 0.45, "Chengalpattu": 0.38, "Kancheepuram": 0.35,
    "Tiruvallur": 0.33, "Kanyakumari": 0.28, "Madurai": 0.22,
    "Sivaganga": 0.30, "Pudukkottai": 0.35, "Dindigul": 0.20,
    "Theni": 0.18, "Virudhunagar": 0.25, "Tenkasi": 0.22,
    "Ariyalur": 0.30, "Perambalur": 0.25, "Karur": 0.18,
    "Tiruchirappalli": 0.22, "Namakkal": 0.15, "Salem": 0.12,
    "Erode": 0.10, "Coimbatore": 0.08, "Tiruppur": 0.10,
    "Nilgiris": 0.15, "Dharmapuri": 0.12, "Krishnagiri": 0.10,
    "Vellore": 0.15, "Ranipet": 0.18, "Tirupathur": 0.12,
    "Tiruvannamalai": 0.20, "Kallakurichi": 0.28,
}


def compute_risk_score(cnn_score, lstm_scores, crowd_override=None):
    """
    Combine CNN spatial + LSTM time-series scores.
    final_risk = 0.4 * CNN + 0.6 * LSTM
    Optional crowd_override applies with 0.2 weight.
    """
    lstm_avg = np.mean([lstm_scores.get("24h", 0), lstm_scores.get("48h", 0),
                        lstm_scores.get("72h", 0)])
    risk = 0.4 * cnn_score + 0.6 * lstm_avg
    if crowd_override is not None:
        risk = 0.8 * risk + 0.2 * crowd_override
    return float(np.clip(risk, 0, 1))


def classify_risk(score):
    """Classify risk score into level and color."""
    if score >= 0.65:
        return {"level": "critical", "color": "#ef4444", "label": "Critical"}
    elif score >= 0.3:
        return {"level": "moderate", "color": "#f59e0b", "label": "Moderate"}
    return {"level": "safe", "color": "#00d4ff", "label": "Safe"}


def generate_risk_heatmap(use_mock=True):
    """
    Generate a GeoJSON FeatureCollection with risk levels for all TN districts.
    """
    features = []
    for district, coords in TN_DISTRICTS.items():
        if use_mock:
            risk = DEMO_RISK_PRESETS.get(district, np.random.uniform(0.05, 0.3))
            risk += np.random.uniform(-0.02, 0.02)
            risk = float(np.clip(risk, 0, 1))
        else:
            risk = float(np.random.uniform(0, 1))

        classification = classify_risk(risk)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [coords[1], coords[0]]},
            "properties": {
                "district": district,
                "risk_score": round(risk, 3),
                "risk_level": classification["level"],
                "color": classification["color"],
                "label": classification["label"],
                "last_updated": datetime.utcnow().isoformat() + "Z",
            }
        })

    return {"type": "FeatureCollection", "features": features}


def get_district_prediction(district, use_mock=True):
    """Get detailed prediction for a specific district."""
    if use_mock:
        from models.lstm_model import mock_lstm_prediction
        from models.cnn_model import mock_cnn_prediction
        lstm_pred = mock_lstm_prediction(district)
        cnn_score = mock_cnn_prediction(district)
    else:
        lstm_pred = {"24h": 0.5, "48h": 0.5, "72h": 0.5}
        cnn_score = 0.5

    risk = compute_risk_score(cnn_score, lstm_pred)
    classification = classify_risk(risk)

    return {
        "district": district,
        "coordinates": TN_DISTRICTS.get(district, [0, 0]),
        "cnn_score": round(cnn_score, 3),
        "lstm_prediction": {k: round(v, 3) for k, v in lstm_pred.items()},
        "combined_risk": round(risk, 3),
        "risk_level": classification["level"],
        "color": classification["color"],
        "label": classification["label"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "recommended_action": _get_recommended_action(risk),
    }


def get_damage_assessment(district, date=None, use_mock=True):
    """Compare pre/post disaster imagery for damage assessment."""
    if use_mock:
        np.random.seed(hash(district) % 2**32)
        pre_ndwi = float(np.random.uniform(-0.1, 0.15))
        post_ndwi = float(np.random.uniform(0.2, 0.65))
        water_expansion = float(np.clip(
            (post_ndwi - pre_ndwi) / max(abs(pre_ndwi), 0.01), 0, 10))
        return {
            "district": district,
            "date": date or datetime.utcnow().strftime("%Y-%m-%d"),
            "pre_event": {
                "ndwi_mean": round(pre_ndwi, 3),
                "water_coverage_pct": round(float(np.random.uniform(5, 15)), 1),
            },
            "post_event": {
                "ndwi_mean": round(post_ndwi, 3),
                "water_coverage_pct": round(float(np.random.uniform(25, 60)), 1),
            },
            "water_expansion_factor": round(water_expansion, 2),
            "estimated_affected_area_sqkm": round(
                float(np.random.uniform(50, 500)), 1),
            "severity": "high" if post_ndwi > 0.4 else "moderate",
        }
    return {
        "district": district,
        "message": "Live damage assessment requires GEE connection",
    }


def generate_time_series_data(district, days=7, use_mock=True):
    """Generate 7-day environmental time series data for charts."""
    if not use_mock:
        return {"district": district,
                "message": "Live data requires API connection"}

    np.random.seed(hash(district) % 2**32)
    is_high_risk = DEMO_RISK_PRESETS.get(district, 0) > 0.5
    data = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(
            days=days - 1 - i)).strftime("%Y-%m-%d")
        if is_high_risk:
            rainfall = 20 + i * 15 + np.random.uniform(-5, 10)
            soil_moisture = min(95, 45 + i * 6 + np.random.uniform(-3, 3))
            river_level = 2.5 + i * 0.4 + np.random.uniform(-0.1, 0.2)
            wind_speed = 25 + i * 5 + np.random.uniform(-3, 5)
            ndwi = -0.05 + i * 0.08 + np.random.uniform(-0.02, 0.02)
        else:
            rainfall = np.random.uniform(0, 15)
            soil_moisture = np.random.uniform(25, 45)
            river_level = np.random.uniform(0.8, 2.0)
            wind_speed = np.random.uniform(5, 20)
            ndwi = np.random.uniform(-0.2, 0.1)
        data.append({
            "date": date,
            "rainfall_mm": round(float(rainfall), 1),
            "soil_moisture_pct": round(float(soil_moisture), 1),
            "wind_speed_kmh": round(float(wind_speed), 1),
            "river_level_m": round(float(river_level), 2),
            "ndwi": round(float(ndwi), 3),
            "temperature_c": round(float(np.random.uniform(26, 34)), 1),
        })
    return {"district": district, "days": days, "data": data}


def get_evacuation_routes(district):
    """Get evacuation routes and shelter locations for a district."""
    shelters = {
        "Thoothukudi": [
            {"name": "Govt. Higher Secondary School, Thoothukudi",
             "lat": 8.7642, "lon": 78.1348, "capacity": 500},
            {"name": "Town Hall Shelter",
             "lat": 8.7830, "lon": 78.1200, "capacity": 300},
            {"name": "Community Center Zone 3",
             "lat": 8.7500, "lon": 78.1500, "capacity": 200},
        ],
        "Chennai": [
            {"name": "Nehru Indoor Stadium",
             "lat": 13.0614, "lon": 80.2810, "capacity": 2000},
            {"name": "YMCA Nandanam",
             "lat": 13.0300, "lon": 80.2400, "capacity": 500},
            {"name": "Govt. School T.Nagar",
             "lat": 13.0400, "lon": 80.2300, "capacity": 400},
        ],
        "Nagapattinam": [
            {"name": "District Collectorate Shelter",
             "lat": 10.7672, "lon": 79.8449, "capacity": 600},
            {"name": "Velankanni Church Hall",
             "lat": 10.6833, "lon": 79.8500, "capacity": 800},
        ],
    }
    routes = {
        "Thoothukudi": [
            {"from": "Coastal Zone 3", "to": "Town Hall Shelter",
             "route": "NH 45B -> NH 38", "distance_km": 4.2},
            {"from": "Harbor Area", "to": "Govt. School",
             "route": "Beach Rd -> Main Rd", "distance_km": 3.1},
        ],
        "Chennai": [
            {"from": "Adyar", "to": "Nehru Stadium",
             "route": "Sardar Patel Rd", "distance_km": 2.5},
            {"from": "Velachery", "to": "YMCA",
             "route": "Velachery Main Rd -> GP Rd", "distance_km": 5.0},
        ],
    }
    default_coords = TN_DISTRICTS.get(district, [10, 78])
    return {
        "district": district,
        "shelters": shelters.get(district, [
            {"name": f"{district} Emergency Shelter",
             "lat": default_coords[0], "lon": default_coords[1],
             "capacity": 300}
        ]),
        "routes": routes.get(district, []),
        "emergency_contacts": {
            "ndrf": "011-24363260",
            "state_disaster": "1070",
            "ambulance": "108",
        },
    }


def _get_recommended_action(risk_score):
    """Get recommended action based on risk score."""
    if risk_score >= 0.8:
        return ("IMMEDIATE EVACUATION - Move to nearest shelter. "
                "Contact NDRF: 011-24363260")
    elif risk_score >= 0.65:
        return ("HIGH ALERT - Prepare for evacuation. "
                "Stock emergency supplies. Stay tuned for updates.")
    elif risk_score >= 0.45:
        return ("CAUTION - Monitor weather updates. "
                "Avoid low-lying areas. Keep emergency kit ready.")
    elif risk_score >= 0.3:
        return ("WATCH - Stay informed. "
                "Check local weather forecasts regularly.")
    return "NORMAL - No immediate threat. Standard precautions apply."
