"""Backend server replica instance.

Serves simple JSON content and exposes a heartbeat endpoint for the
load balancer's self-healing daemon.
"""
import os
from flask import Flask, jsonify

app = Flask(__name__)


SERVER_ID = os.environ.get("SERVER_ID", "Unknown")

@app.route("/home", methods=["GET"])
def home():
    """Return a simple greetings message identifying this server.

    Returns:
        JSON response with server ID and status successful, and HTTP 200.
    """
    return jsonify({
        "message": f"Hello from Server: {SERVER_ID}",
        "status": "successful"
    }), 200


@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    """Return an empty successful response to indicate the replica is alive.

    Used by the load balancer's background self-healing daemon.

    Returns:
        Empty response with HTTP status code 200.
    """
    return "", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)