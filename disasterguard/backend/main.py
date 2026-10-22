"""
DisasterGuard — FastAPI Backend Application

REST API for disaster prediction, risk mapping, alerts, and crowd reporting.
Supports mock data mode (USE_MOCK_DATA=True) for offline hackathon demos.
"""

import os
import sys
# Fix Windows console encoding for Unicode/emoji characters
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "True").lower() in ("true", "1", "yes")

# ---------- App Setup ----------

app = FastAPI(
    title="DisasterGuard API",
    description="AI Disaster Prediction & Response Platform for Tamil Nadu",
    version="1.0.0",
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- In-memory stores ----------
crowd_reports_store: list = []
alert_history_store: list = []

# ---------- Pydantic Models ----------

class CrowdReport(BaseModel):
    latitude: float
    longitude: float
    disaster_type: str = "flood"
    severity: int = 3  # 1-5
    description: str = ""
    photo_url: Optional[str] = None
    reporter_name: Optional[str] = "Anonymous"

class AlertRequest(BaseModel):
    district: str
    risk_score: Optional[float] = None
    message: Optional[str] = None
    recipients: Optional[List[str]] = None

# ---------- Startup ----------

@app.on_event("startup")
async def startup():
    print("=" * 60)
    print("🛡️  DisasterGuard API Starting...")
    print(f"   Mock Data Mode: {'ON' if USE_MOCK_DATA else 'OFF'}")
    print(f"   CORS Origins: {cors_origins}")
    print("=" * 60)

    if not USE_MOCK_DATA:
        try:
            from alerts.twilio_sms import initialize_twilio
            from alerts.firebase_push import initialize_firebase
            initialize_twilio()
            initialize_firebase()
        except Exception as e:
            print(f"⚠️  Alert services init failed: {e}")

    # Seed some demo alert history
    _seed_demo_alerts()

# ---------- API Endpoints ----------

@app.get("/")
async def root():
    return {
        "name": "DisasterGuard API",
        "version": "1.0.0",
        "status": "operational",
        "mock_mode": USE_MOCK_DATA,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/risk-map")
async def get_risk_map(
    lat: Optional[float] = Query(None, description="Center latitude"),
    lon: Optional[float] = Query(None, description="Center longitude"),
    radius: Optional[float] = Query(None, description="Radius in km"),
):
    """Returns GeoJSON risk heatmap for Tamil Nadu districts."""
    from models.risk_engine import generate_risk_heatmap
    heatmap = generate_risk_heatmap(use_mock=USE_MOCK_DATA)

    # Filter by radius if lat/lon provided
    if lat is not None and lon is not None and radius is not None:
        filtered_features = []
        for f in heatmap["features"]:
            flon, flat = f["geometry"]["coordinates"]
            dist = _haversine(lat, lon, flat, flon)
            if dist <= radius:
                filtered_features.append(f)
        heatmap["features"] = filtered_features

    return heatmap


@app.get("/api/prediction")
async def get_prediction(
    district: str = Query(..., description="District name"),
):
    """Returns 24/48/72h flood probability for a district."""
    from models.risk_engine import get_district_prediction, TN_DISTRICTS
    if district not in TN_DISTRICTS:
        # Try case-insensitive match
        match = next((d for d in TN_DISTRICTS if d.lower() == district.lower()), None)
        if match:
            district = match
        else:
            raise HTTPException(status_code=404, detail=f"District '{district}' not found")
    return get_district_prediction(district, use_mock=USE_MOCK_DATA)


@app.post("/api/alert")
async def trigger_alert(req: AlertRequest):
    """Triggers SMS + push notification for a district."""
    from models.risk_engine import get_district_prediction, TN_DISTRICTS

    if req.district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District '{req.district}' not found")

    prediction = get_district_prediction(req.district, use_mock=USE_MOCK_DATA)
    risk_score = req.risk_score or prediction["combined_risk"]
    risk_pct = int(risk_score * 100)

    # Send SMS
    from alerts.twilio_sms import send_sms_alert
    sms_result = send_sms_alert(req.district, risk_score, recipients=req.recipients)

    # Send push notification
    from alerts.firebase_push import send_push_notification, store_alert_history
    push_result = send_push_notification(
        title=f"🚨 {req.district} — Flood Alert",
        body=f"Flood Risk: {risk_pct}% | {prediction.get('recommended_action', '')}",
        data={"district": req.district, "risk_score": str(risk_score)},
    )

    # Store alert
    alert_record = {
        "district": req.district, "risk_score": risk_score,
        "risk_level": prediction["risk_level"],
        "message": sms_result.get("message", ""),
        "type": "flood", "status": "active",
        "sms_sent": sms_result.get("success", False),
        "push_sent": push_result.get("success", False),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    store_alert_history(alert_record)
    alert_history_store.insert(0, alert_record)

    return {
        "success": True,
        "alert": alert_record,
        "sms": sms_result,
        "push": push_result,
    }


@app.get("/api/damage-assessment")
async def get_damage_assessment(
    district: str = Query(..., description="District name"),
    date: Optional[str] = Query(None, description="Date YYYY-MM-DD"),
):
    """Compare pre/post satellite imagery for damage assessment."""
    from models.risk_engine import get_damage_assessment, TN_DISTRICTS
    if district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District '{district}' not found")
    return get_damage_assessment(district, date, use_mock=USE_MOCK_DATA)


@app.get("/api/districts")
async def list_districts():
    """List all Tamil Nadu districts with current risk levels."""
    from models.risk_engine import TN_DISTRICTS, DEMO_RISK_PRESETS, classify_risk
    districts = []
    for name, coords in TN_DISTRICTS.items():
        risk = DEMO_RISK_PRESETS.get(name, round(np.random.uniform(0.05, 0.25), 3))
        classification = classify_risk(risk)
        districts.append({
            "name": name, "lat": coords[0], "lon": coords[1],
            "risk_score": round(risk, 3), **classification,
        })
    districts.sort(key=lambda d: d["risk_score"], reverse=True)
    return {"districts": districts, "count": len(districts)}


@app.get("/api/time-series")
async def get_time_series(
    district: str = Query("Thoothukudi", description="District name"),
    days: int = Query(7, description="Number of days", ge=1, le=30),
):
    """Get environmental time-series data for prediction charts."""
    from models.risk_engine import generate_time_series_data, TN_DISTRICTS
    if district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District '{district}' not found")
    return generate_time_series_data(district, days, use_mock=USE_MOCK_DATA)


@app.post("/api/crowd-report")
async def submit_crowd_report(report: CrowdReport):
    """Submit a crowd-sourced disaster report."""
    record = {
        "id": f"cr_{len(crowd_reports_store)+1}_{int(datetime.utcnow().timestamp())}",
        **report.dict(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "verified": False,
    }
    crowd_reports_store.insert(0, record)
    return {"success": True, "report": record}


@app.get("/api/crowd-reports")
async def get_crowd_reports(limit: int = Query(50, ge=1, le=200)):
    """Fetch recent crowd-sourced reports."""
    if not crowd_reports_store:
        return {"reports": _mock_crowd_reports(), "count": 5}
    return {"reports": crowd_reports_store[:limit], "count": len(crowd_reports_store[:limit])}


@app.get("/api/evacuation-routes")
async def get_evacuation_routes(
    district: str = Query("Thoothukudi", description="District name"),
):
    """Get evacuation routes and shelter locations for a district."""
    from models.risk_engine import get_evacuation_routes, TN_DISTRICTS
    if district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District '{district}' not found")
    return get_evacuation_routes(district)


@app.get("/api/alerts/history")
async def get_alerts_history(limit: int = Query(20, ge=1, le=100)):
    """Get alert history."""
    if alert_history_store:
        return {"alerts": alert_history_store[:limit]}
    from alerts.firebase_push import get_alert_history
    return {"alerts": get_alert_history(limit)}


# ---------- Helpers ----------

def _haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km."""
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def _seed_demo_alerts():
    """Seed alert history for demo."""
    demo_alerts = [
        {"district": "Thoothukudi", "risk_score": 0.82, "risk_level": "critical",
         "message": "🚨 DISASTERGUARD ALERT | Thoothukudi | Flood Risk: 82% | 48h window",
         "type": "flood", "status": "active", "created_at": datetime.utcnow().isoformat() + "Z"},
        {"district": "Nagapattinam", "risk_score": 0.71, "risk_level": "critical",
         "message": "🚨 DISASTERGUARD ALERT | Nagapattinam | Flood Risk: 71% | 72h window",
         "type": "flood", "status": "active", "created_at": datetime.utcnow().isoformat() + "Z"},
        {"district": "Cuddalore", "risk_score": 0.68, "risk_level": "critical",
         "message": "🚨 DISASTERGUARD ALERT | Cuddalore | Flood Risk: 68% | 72h window",
         "type": "flood", "status": "monitoring", "created_at": datetime.utcnow().isoformat() + "Z"},
    ]
    alert_history_store.extend(demo_alerts)


def _mock_crowd_reports():
    """Generate mock crowd reports for demo."""
    return [
        {"id": "cr_mock_1", "latitude": 8.76, "longitude": 78.13, "disaster_type": "flood",
         "severity": 4, "description": "Water level rising near Thoothukudi harbor area",
         "reporter_name": "Local Authority", "timestamp": datetime.utcnow().isoformat() + "Z", "verified": True},
        {"id": "cr_mock_2", "latitude": 10.77, "longitude": 79.84, "disaster_type": "flood",
         "severity": 3, "description": "Waterlogging reported in Nagapattinam low-lying areas",
         "reporter_name": "Resident", "timestamp": datetime.utcnow().isoformat() + "Z", "verified": False},
        {"id": "cr_mock_3", "latitude": 13.08, "longitude": 80.27, "disaster_type": "flood",
         "severity": 2, "description": "Minor waterlogging in Chennai T.Nagar underpass",
         "reporter_name": "Anonymous", "timestamp": datetime.utcnow().isoformat() + "Z", "verified": False},
        {"id": "cr_mock_4", "latitude": 11.75, "longitude": 79.77, "disaster_type": "flood",
         "severity": 4, "description": "River overflow near Cuddalore agricultural lands",
         "reporter_name": "Farmer Assoc.", "timestamp": datetime.utcnow().isoformat() + "Z", "verified": True},
        {"id": "cr_mock_5", "latitude": 8.73, "longitude": 77.70, "disaster_type": "landslide",
         "severity": 3, "description": "Minor landslide on Tirunelveli-Courtallam road",
         "reporter_name": "PWD Officer", "timestamp": datetime.utcnow().isoformat() + "Z", "verified": True},
    ]


# ---------- Init Modules ----------
# Create __init__.py files for package imports
for pkg in ["models", "data", "alerts"]:
    init_path = os.path.join(os.path.dirname(__file__), pkg, "__init__.py")
    os.makedirs(os.path.dirname(init_path), exist_ok=True)
    if not os.path.exists(init_path):
        open(init_path, "w").close()
