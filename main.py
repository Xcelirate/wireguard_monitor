import json
import os
import subprocess
import time
import threading
from flask import Flask, jsonify
import logging
from logging.handlers import SysLogHandler

WG_JSON_SCRIPT = os.getenv('WIREGUARD_MONITOR_WG_JSON_SCRIPT', './tools/wg-json.bash')
CONNECTED_INTERVAL = int(os.getenv('WIREGUARD_MONITOR_CONNECTED_INTERVAL', '120'))  # seconds
DISCONNECTED_INTERVAL = int(os.getenv('WIREGUARD_MONITOR_DISCONNECTED_INTERVAL', '180'))  # seconds
CHECK_INTERVAL = int(os.getenv('WIREGUARD_MONITOR_CHECK_INTERVAL', '20'))  # seconds
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

def strip_handshake_times(analysis):
    # Recursively remove 'last_handshake_seconds_ago' from the analysis dict
    if isinstance(analysis, dict):
        new_analysis = {}
        for k, v in analysis.items():
            if isinstance(v, dict):
                new_analysis[k] = strip_handshake_times(v)
            elif k != 'last_handshake_seconds_ago':
                new_analysis[k] = v
        return new_analysis
    return analysis

def monitor_loop():
    prev_peer_status = {}  # {interface: {peer_key: status}}
    first_run = True
    while True:
        try:
            status = get_wireguard_status()
            analysis = analyze_peers(status)
            current_peer_status = {}
            now_ts = int(time.time())
            # Build current status dict
            for interface, peers in analysis.items():
                current_peer_status[interface] = {}
                for peer_key, peer_info in peers.items():
                    current_peer_status[interface][peer_key] = peer_info["status"]
            if first_run:
                # On first run, log all peers' status
                for interface, peers in analysis.items():
                    for peer_key, peer_info in peers.items():
                        logger.info(json.dumps({
                            "event": "initial_status",
                            "timestamp": now_ts,
                            "interface": interface,
                            "peer": peer_key,
                            "status": peer_info["status"],
                            "endpoint": peer_info.get("endpoint"),
                            "allowedIps": peer_info.get("allowedIps", [])
                        }))
                first_run = False
            else:
                # On subsequent runs, only log status changes
                for interface, peers in current_peer_status.items():
                    for peer_key, status in peers.items():
                        prev_status = prev_peer_status.get(interface, {}).get(peer_key)
                        if prev_status and prev_status != status:
                            logger.info(json.dumps({
                                "event": "status_change",
                                "timestamp": now_ts,
                                "interface": interface,
                                "peer": peer_key,
                                "new_status": status
                            }))
                        elif prev_status is None:
                            # New peer appeared
                            logger.info(json.dumps({
                                "event": "new_peer",
                                "timestamp": now_ts,
                                "interface": interface,
                                "peer": peer_key,
                                "status": status
                            }))
            prev_peer_status = current_peer_status
        except Exception as e:
            logger.error(json.dumps({"error": str(e), "timestamp": int(time.time())}))
        time.sleep(CHECK_INTERVAL)

def main():
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()
    app.run(host=HOST, port=PORT)

if __name__ == "__main__":
    main()
