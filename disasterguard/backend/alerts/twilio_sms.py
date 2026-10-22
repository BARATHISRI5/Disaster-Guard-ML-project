"""
DisasterGuard — Twilio SMS Alert System

Sends formatted disaster alert SMS to registered authorities.
Gracefully falls back when Twilio is not configured.
"""

import os
from datetime import datetime

TWILIO_INITIALIZED = False
twilio_client = None
twilio_from = None


def initialize_twilio():
    """Initialize Twilio client from environment variables."""
    global TWILIO_INITIALIZED, twilio_client, twilio_from
    try:
        from twilio.rest import Client
        sid = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_from = os.getenv("TWILIO_PHONE_NUMBER")
        if not all([sid, token, twilio_from]):
            print("⚠️  Twilio credentials not configured. SMS alerts disabled.")
            return False
        twilio_client = Client(sid, token)
        TWILIO_INITIALIZED = True
        print("✅ Twilio initialized successfully")
        return True
    except ImportError:
        print("⚠️  Twilio library not installed.")
        return False
    except Exception as e:
        print(f"⚠️  Twilio init failed: {e}")
        return False


def format_alert_message(district, risk_pct, window="48h", route_url=None):
    """Format the disaster alert SMS message."""
    route = route_url or f"https://disasterguard.app/evacuate/{district.lower()}"
    return (
        f"🚨 DISASTERGUARD ALERT | {district} | Flood Risk: {risk_pct}% | "
        f"{window} window | Evacuate: {route} | NDRF helpline: 011-24363260"
    )


def send_sms_alert(district, risk_score, recipients=None, window="48h"):
    """
    Send SMS alert to registered recipients.
    Triggers when risk_score > 0.65.
    """
    risk_pct = int(risk_score * 100)
    message_body = format_alert_message(district, risk_pct, window)

    if recipients is None:
        recipients = os.getenv("ALERT_RECIPIENTS", "").split(",")
        recipients = [r.strip() for r in recipients if r.strip()]

    if not TWILIO_INITIALIZED or not twilio_client:
        print(f"📲 [MOCK SMS] To: {recipients or ['no recipients']}")
        print(f"   Message: {message_body}")
        return {
            "success": True, "mock": True,
            "message": message_body,
            "recipients": recipients,
            "district": district,
            "risk_pct": risk_pct,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    results = []
    for phone in recipients:
        try:
            msg = twilio_client.messages.create(
                body=message_body, from_=twilio_from, to=phone
            )
            results.append({"phone": phone, "sid": msg.sid, "status": msg.status})
            print(f"✅ SMS sent to {phone}: {msg.sid}")
        except Exception as e:
            results.append({"phone": phone, "error": str(e)})
            print(f"❌ SMS failed to {phone}: {e}")

    return {
        "success": all("error" not in r for r in results),
        "message": message_body,
        "results": results,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def check_and_alert(district, risk_score, threshold=0.65):
    """Check if risk exceeds threshold and trigger alert."""
    if risk_score >= threshold:
        window = "24h" if risk_score >= 0.8 else "48h" if risk_score >= 0.7 else "72h"
        return send_sms_alert(district, risk_score, window=window)
    return {"triggered": False, "risk_score": risk_score, "threshold": threshold}
