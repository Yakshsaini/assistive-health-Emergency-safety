"""
PulseGuard - Automated Emergency SMS Alert Dispatcher
Connects Gemini Multimodal AI JSON output to Twilio SMS API
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PulseGuardAlert")

# Twilio Credentials from Environment
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "AC_YOUR_TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "YOUR_TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+15005550006")
EMERGENCY_CONTACT_PHONE = os.getenv("EMERGENCY_CONTACT_PHONE", "+1234567890")
CAMPUS_SECURITY_PHONE = os.getenv("CAMPUS_SECURITY_PHONE", "+1987654321")


def format_emergency_sms(gemini_payload: Dict[str, Any]) -> str:
    """
    Formats the structured Gemini JSON output into an actionable, high-priority SMS.
    """
    severity = gemini_payload.get("severity", "CRITICAL").upper()
    category = gemini_payload.get("category", "MEDICAL").upper()
    summary = gemini_payload.get("summary", "Immediate medical assistance required.")
    hazard = gemini_payload.get("hazard") or gemini_payload.get("hazard_or_condition_identified") or "Hazard Detected"
    warning = gemini_payload.get("critical_warning", "")
    
    # Extract geolocation coordinates if present
    geo = gemini_payload.get("geolocation") or {}
    maps_link = geo.get("maps_link")
    if not maps_link and "lat" in geo and "lng" in geo:
        maps_link = f"https://www.google.com/maps?q={geo['lat']},{geo['lng']}"
    
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Build SMS content
    sms_lines = [
        f"🚨 [PULSEGUARD EMERGENCY ALERT - {severity}]",
        f"Category: {category} | Hazard: {hazard}",
        f"Details: {summary}",
    ]

    if warning:
        sms_lines.append(f"⚠️ Warning: {warning}")

    if maps_link:
        sms_lines.append(f"📍 Live Map: {maps_link}")
    else:
        sms_lines.append("📍 Location: Campus Main Area (GPS unavailable)")

    sms_lines.append(f"⏱️ Logged: {timestamp} (Automated Gemini Triage)")

    return "\n".join(sms_lines)


def send_emergency_sms(
    gemini_payload: Dict[str, Any],
    recipient_phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parses Gemini JSON payload and dispatches an emergency SMS via Twilio.
    """
    # 1. Evaluate alert trigger condition
    alert_trigger = gemini_payload.get("alert_trigger", False)
    severity = str(gemini_payload.get("severity", "")).upper()

    # If trigger is not explicitly true and severity is not high/critical, ignore
    if not alert_trigger and severity not in ["CRITICAL", "HIGH"]:
        logger.info(f"Skipping SMS alert. Alert trigger: {alert_trigger}, Severity: {severity}")
        return {
            "status": "skipped",
            "message": f"Alert condition not met (Severity: {severity})"
        }

    # 2. Format the SMS body
    sms_body = format_emergency_sms(gemini_payload)
    target_phone = recipient_phone or EMERGENCY_CONTACT_PHONE

    logger.info(f"Preparing to send emergency SMS to {target_phone}...")
    logger.info(f"SMS Content:\n{sms_body}\n")

    # 3. Check for Twilio library & valid credentials
    try:
        from twilio.rest import Client
        
        # Check if dummy credentials are in place
        if "YOUR_TWILIO" in TWILIO_ACCOUNT_SID or not TWILIO_ACCOUNT_SID.startswith("AC"):
            logger.warning("[SIMULATION MODE] Valid Twilio credentials not set. Simulated SMS transmission successful.")
            return {
                "status": "simulated",
                "recipient": target_phone,
                "sms_body": sms_body,
                "timestamp": datetime.now().isoformat()
            }

        # Initialize Twilio Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=sms_body,
            from_=TWILIO_PHONE_NUMBER,
            to=target_phone
        )

        logger.info(f"Emergency SMS sent successfully! Twilio SID: {message.sid}")
        return {
            "status": "sent",
            "message_sid": message.sid,
            "recipient": target_phone,
            "timestamp": datetime.now().isoformat()
        }

    except ImportError:
        logger.warning("[SIMULATION MODE] twilio package not installed. Simulating successful SMS dispatch.")
        return {
            "status": "simulated",
            "recipient": target_phone,
            "sms_body": sms_body,
            "note": "Install twilio via `pip install twilio` to enable live cellular dispatch.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to send SMS via Twilio: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Failed to send SMS via Twilio: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Example execution for direct testing
if __name__ == "__main__":
    print("=" * 60)
    print("PulseGuard - Gemini JSON to Twilio SMS Test")
    print("=" * 60)

    # Sample Gemini Multimodal JSON output
    sample_gemini_output = {
        "alert_trigger": True,
        "severity": "CRITICAL",
        "category": "CHEMICAL",
        "hazard": "Sulfuric Acid Eye Splash",
        "summary": "CRITICAL: Chemical splash in right eye. Eye wash flushing initiated.",
        "critical_warning": "DO NOT rub eye. DO NOT use neutralizing agents.",
        "geolocation": {
            "lat": "37.7749",
            "lng": "-122.4194",
            "maps_link": "https://www.google.com/maps?q=37.7749,-122.4194"
        }
    }

    result = send_emergency_sms(sample_gemini_output)
    print("Dispatch Result:", json.dumps(result, indent=2))
