import json
import os
import subprocess
import time
import threading
from flask import Flask, jsonify
import logging
from logging.handlers import SysLogHandler

WG_JSON_SCRIPT = os.getenv('WIREGUARD_MONITOR_WG_JSON_SCRIPT', './tools/wg-json.bash')
CONNECTED_INTERVAL = int(os.getenv('WIREGUARD_MONITOR_CONNECTED_INTERVAL', '30'))  # seconds
DISCONNECTED_INTERVAL = int(os.getenv('WIREGUARD_MONITOR_DISCONNECTED_INTERVAL', '130'))  # seconds
CHECK_INTERVAL = int(os.getenv('WIREGUARD_MONITOR_CHECK_INTERVAL', '30'))  # seconds
HOST = os.getenv('WIREGUARD_MONITOR_HOST', '0.0.0.0')
PORT = int(os.getenv('WIREGUARD_MONITOR_PORT', '5000'))

# Set up logging
logger = logging.getLogger('wireguard_monitor')
logger.setLevel(logging.INFO)
# Use SysLogHandler. Assumes /dev/log for local syslog.
handler = SysLogHandler(address='/dev/log')
formatter = logging.Formatter('%(name)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)
wg_status_data = {}  # Global variable to hold latest wg_status.json content

def get_wireguard_status():
    global wg_status_data
    try:
        result = subprocess.run(
            ['bash', WG_JSON_SCRIPT],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            wg_status_data = {"error": f"Script failed: {result.stderr}"}
        else:
            wg_status_data = json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        wg_status_data = {"error": "Script execution timed out"}
    except Exception as e:
        wg_status_data = {"error": str(e)}
    return wg_status_data

@app.route('/raw')
def raw_status():
    return jsonify(wg_status_data)

def analyze_peers(status):
    now = int(time.time())
    result = {}
    for interface, data in status.items():
        result[interface] = {}
        for peer_key, peer_data in data.get('peers', {}).items():
            last_handshake = peer_data['latestHandshake']
            delta = now - last_handshake
            if delta <= CONNECTED_INTERVAL:
                result[interface][peer_key] = {
                    "status": "connected",
                    "last_handshake_seconds_ago": delta,
                    "endpoint": peer_data.get("endpoint"),
                    "allowedIps": peer_data.get("allowedIps", [])
                }
            elif delta <= DISCONNECTED_INTERVAL:
                result[interface][peer_key] = {
                    "status": "disconnected",
                    "last_handshake_seconds_ago": delta,
                    "endpoint": peer_data.get("endpoint"),
                    "allowedIps": peer_data.get("allowedIps", [])
                }
            # If delta > DISCONNECTED_INTERVAL, do not show the peer
    return result

def monitor_loop():
    prev_analysis = None
    while True:
        try:
            status = get_wireguard_status()
            analysis = analyze_peers(status)
            if analysis != prev_analysis:
                output = {
                    "timestamp": int(time.time()),
                    "status": analysis
                }
                logger.info(json.dumps(output))
                prev_analysis = analysis
        except Exception as e:
            logger.error(json.dumps({"error": str(e)}))
        time.sleep(CHECK_INTERVAL)

def main():
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()
    app.run(host=HOST, port=PORT)

if __name__ == "__main__":
    main()
