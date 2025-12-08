# WireGuard Monitor

A Flask-based application that monitors WireGuard VPN interface status and peer connectivity in real-time.

## Features

- **Real-time Monitoring**: Continuously executes a bash script to get WireGuard interface and peer status
- **REST API**: Exposes status information via a simple HTTP endpoint
- **Peer Status Analysis**: Automatically classifies peers as "connected" or "disconnected" based on handshake timing
- **Syslog Logging**: Streams status changes as JSON to the system journal for easy integration with other tools
- **Multi-interface Support**: Handles multiple WireGuard interfaces simultaneously
- **Configurable Intervals**: Adjustable thresholds for connection status determination
- **Custom Script Support**: Point to any bash script that outputs WireGuard status as JSON

## Requirements

- Python 3.13+
- Flask 3.1.2+

## Installation

1. Clone the repository:
```bash
git clone <repository-url> wireguard_monitor
cd wireguard_monitor
```

2. Install dependencies using [uv](https://github.com/astral-sh/uv):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

Start the monitoring application:
```bash
python main.py
```

The application will:
1. Start a Flask web server on the configured host and port (default: `0.0.0.0:5000`)
2. Periodically execute the configured bash script (default: `./tools/wg-json.bash`) to get WireGuard status
3. Log JSON status changes to the system journal (syslog)

To run with custom configuration:
```bash
WIREGUARD_MONITOR_HOST=127.0.0.1 WIREGUARD_MONITOR_PORT=8080 python main.py
```

To use a custom script:
```bash
WIREGUARD_MONITOR_WG_JSON_SCRIPT=/path/to/custom/script.bash python main.py
```

### API Endpoints

#### `/raw`
Returns the raw WireGuard status data from the latest JSON file.

**Response Example:**
```json
{
  "wg_secpipe_e1": {
    "privateKey": "...",
    "publicKey": "...",
    "listenPort": 51823,
    "peers": {
      "peer_public_key": {
        "endpoint": "57.128.189.209:51823",
        "latestHandshake": 1765189425,
        "transferRx": 1966140,
        "transferTx": 4085712,
        "persistentKeepalive": 25,
        "allowedIps": ["10.150.94.2/32"]
      }
    }
  }
}
```

### Configuration

All configuration is controlled via environment variables with the `WIREGUARD_MONITOR_` prefix:

- **WIREGUARD_MONITOR_HOST** (default: `0.0.0.0`): Host address to bind the Flask server to
- **WIREGUARD_MONITOR_PORT** (default: `5000`): Port to listen on
- **WIREGUARD_MONITOR_WG_JSON_SCRIPT** (default: `./tools/wg-json.bash`): Path to the bash script that outputs WireGuard status as JSON
- **WIREGUARD_MONITOR_CONNECTED_INTERVAL** (default: `30`): Time threshold (seconds) to consider a peer as "connected"
- **WIREGUARD_MONITOR_DISCONNECTED_INTERVAL** (default: `130`): Time threshold (seconds) to consider a peer as "disconnected"
- **WIREGUARD_MONITOR_CHECK_INTERVAL** (default: `30`): How often (seconds) to check and analyze the status

**Example:**
```bash
WIREGUARD_MONITOR_HOST=127.0.0.1 WIREGUARD_MONITOR_PORT=8080 WIREGUARD_MONITOR_CONNECTED_INTERVAL=60 python main.py
```

### Status Output

The application logs JSON to the system journal (syslog) when status changes are detected:

```json
{
  "timestamp": 1765189500,
  "status": {
    "wg_secpipe_e1": {
      "peer_public_key": {
        "status": "connected",
        "last_handshake_seconds_ago": 15,
        "endpoint": "57.128.189.209:51823",
        "allowedIps": ["10.150.94.2/32", "10.161.1.101/32"]
      }
    }
  }
}
```

## Data Source

The application executes a bash script that outputs WireGuard status as JSON. By default, it uses the `./tools/wg-json.bash` script from the [WireGuard tools repository](https://github.com/WireGuard/wireguard-tools).

The script output should be valid JSON with the following structure:

```json
{
  "interface_name": {
    "privateKey": "...",
    "publicKey": "...",
    "listenPort": 51820,
    "peers": {
      "peer_public_key": {
        "endpoint": "ip:port",
        "latestHandshake": unix_timestamp,
        "transferRx": bytes,
        "transferTx": bytes,
        "persistentKeepalive": seconds,
        "allowedIps": ["ip/mask"]
      }
    }
  }
}
```

## Architecture

- **Monitor Loop**: Runs in a background thread that continuously reads and analyzes WireGuard status
- **Flask Server**: Provides HTTP endpoints for status queries
- **Status Analysis**: Compares current timestamps with handshake timestamps to determine peer connectivity

## Example Workflow

1. Application starts and launches Flask server
2. Monitor loop runs in background, executing the bash script every 30 seconds
3. Script output (JSON) is parsed to extract WireGuard interface and peer data
4. Peers are analyzed based on their last handshake time:
   - If handshake was ≤30 seconds ago → "connected"
   - If handshake was 31-130 seconds ago → "disconnected"
   - If handshake was >130 seconds ago → not shown
5. Status changes are logged to stdout as JSON
6. Current status is available via `/raw` endpoint

## Troubleshooting

- **No output or error "Script execution timed out"**: The bash script is taking too long to execute. Ensure the script at `WIREGUARD_MONITOR_WG_JSON_SCRIPT` completes within 10 seconds
- **Error "Script failed"**: The bash script exited with a non-zero status. Check the error message and ensure the script has proper permissions (chmod +x)
- **JSON parsing error**: Ensure the bash script outputs valid JSON. Test it manually: `bash ./tools/wg-json.bash`
- **Connection issues**: Verify the Flask server is running on the configured host and port (check `WIREGUARD_MONITOR_HOST` and `WIREGUARD_MONITOR_PORT` environment variables)
- **Configuration not applied**: Ensure environment variables are set before running the application

## License

This project is licensed under the GNU General Public License v3.0. See the LICENSE file for details.
