"""
PulseGuard Webhook Server
Receives JSON triage payloads from the PulseGuard web interface and dispatches automated Twilio SMS alerts.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from send_emergency_alert import send_emergency_sms

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the web frontend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AlertServer")


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "PulseGuard Alert Webhook Server",
        "version": "1.0.0"
    })


@app.route("/api/alert", methods=["POST"])
def receive_emergency_alert():
    """
    Receives JSON payload from frontend Gemini triage and dispatches Twilio SMS.
    """
    try:
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        logger.info(f"Received emergency alert payload: {payload}")
        
        # Dispatch SMS via Twilio integration module
        result = send_emergency_sms(payload)
        
        return jsonify({
            "message": "Alert processed successfully",
            "dispatch_result": result
        }), 200

    except Exception as e:
        logger.error(f"Error processing emergency alert: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("PulseGuard Emergency Webhook Server Running on http://localhost:5000")
    print("Listening for POST requests on /api/alert")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
