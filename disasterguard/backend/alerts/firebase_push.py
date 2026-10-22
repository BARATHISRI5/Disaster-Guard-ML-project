"""
DisasterGuard — Firebase Cloud Messaging Push Notifications

Sends push notifications via FCM and stores alert history in Firestore.
Gracefully falls back when Firebase is not configured.
"""

import os
from datetime import datetime

FIREBASE_INITIALIZED = False
db = None


def initialize_firebase(credentials_path=None):
    """Initialize Firebase Admin SDK."""
    global FIREBASE_INITIALIZED, db
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        cred_path = credentials_path or os.getenv("FIREBASE_CREDENTIALS_PATH")
        if not cred_path or not os.path.exists(cred_path):
            print("⚠️  Firebase credentials not found. Push notifications disabled.")
            return False
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        FIREBASE_INITIALIZED = True
        print("✅ Firebase initialized successfully")
        return True
    except Exception as e:
        print(f"⚠️  Firebase init failed: {e}")
        return False


def send_push_notification(title, body, topic="disaster_alerts", data=None):
    """Send push notification via FCM to a topic."""
    if not FIREBASE_INITIALIZED:
        print(f"📱 [MOCK PUSH] {title}: {body}")
        return {"success": True, "mock": True, "title": title, "body": body}
    try:
        from firebase_admin import messaging
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            topic=topic,
            data=data or {},
        )
        response = messaging.send(message)
        print(f"✅ Push notification sent: {response}")
        return {"success": True, "message_id": response}
    except Exception as e:
        print(f"❌ Push notification failed: {e}")
        return {"success": False, "error": str(e)}


def store_alert_history(alert_data):
    """Store alert in Firestore for history tracking."""
    alert_record = {**alert_data, "created_at": datetime.utcnow().isoformat() + "Z"}
    if not FIREBASE_INITIALIZED or db is None:
        print(f"📝 [MOCK STORE] Alert stored: {alert_data.get('district', 'N/A')}")
        return {"success": True, "mock": True, "id": f"mock_{datetime.utcnow().timestamp()}"}
    try:
        doc_ref = db.collection("alerts").add(alert_record)
        return {"success": True, "id": doc_ref[1].id}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_alert_history(limit=20):
    """Fetch recent alerts from Firestore."""
    if not FIREBASE_INITIALIZED or db is None:
        return _mock_alert_history()
    try:
        docs = db.collection("alerts").order_by("created_at", direction="DESCENDING").limit(limit).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        print(f"❌ Failed to fetch alerts: {e}")
        return _mock_alert_history()


def _mock_alert_history():
    """Generate mock alert history for demo."""
    import numpy as np
    districts = ["Thoothukudi", "Nagapattinam", "Chennai", "Cuddalore", "Tirunelveli"]
    alerts = []
    for i, d in enumerate(districts):
        risk = round(0.65 + np.random.uniform(0, 0.3), 2)
        alerts.append({
            "id": f"mock_alert_{i}",
            "district": d, "risk_score": risk,
            "risk_level": "critical" if risk > 0.65 else "moderate",
            "message": f"🚨 DISASTERGUARD ALERT | {d} | Flood Risk: {int(risk*100)}%",
            "created_at": (datetime.utcnow()).isoformat() + "Z",
            "type": "flood", "status": "active",
        })
    return alerts
