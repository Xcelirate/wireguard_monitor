# WireGuard Monitor

A Flask-based application that monitors WireGuard VPN interface status and peer connectivity in real-time.

## Features

- **Real-time Monitoring**: Continuously executes a bash script (now always run with `sudo /usr/bin/bash`) to get WireGuard interface and peer status
- **REST API**: Exposes status information via a simple HTTP endpoint
- **Peer Status Analysis**: Automatically classifies peers as "connected" or "disconnected" based on handshake timing
- **Syslog Logging**: Streams status changes as JSON to the system journal for easy integration with other tools
- **Multi-interface Support**: Handles multiple WireGuard interfaces simultaneously
- **Configurable Intervals**: Adjustable thresholds for connection status determination
- **Custom Script Support**: Point to any bash script that outputs WireGuard status as JSON

## Requirements

See `requirements.txt` for full dependency list.
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

### Running the Application (Development)

To run the Flask development server (not recommended for production):

```bash
uv run main.py
```

### Running with Gunicorn (Production)

To run the application in production mode using Gunicorn and environment variables for host and port:

```bash
uv sync  # or pip install -r requirements.txt
export WIREGUARD_MONITOR_HOST=0.0.0.0
export WIREGUARD_MONITOR_PORT=5000
.venv/bin/gunicorn main:app -c gunicorn.conf.py
```

- The app will listen on the host and port specified by the environment variables, as set in gunicorn.conf.py.
- This approach allows you to configure the address dynamically without changing the command.
- Logging will be sent to the system journal via syslog.
- The WireGuard status script is always executed with `sudo /usr/bin/bash` for required privileges.

## Configuration

You can configure the following environment variables:
- `WIREGUARD_MONITOR_WG_JSON_SCRIPT`: Path to the WireGuard status script (default: `tools/wg-json.bash`)
- `WIREGUARD_MONITOR_CONNECTED_INTERVAL`: Seconds to consider a peer as connected (default: `180`)
- `WIREGUARD_MONITOR_DISCONNECTED_INTERVAL`: Seconds to consider a peer as disconnected (default: `240`)
- `WIREGUARD_MONITOR_CHECK_INTERVAL`: How often to check status (default: `10`)
- `WIREGUARD_MONITOR_HOST`: Host for Flask app (default: `0.0.0.0`, only used for development server)
- `WIREGUARD_MONITOR_PORT`: Port for Flask app (default: `5000`, only used for development server)

## Status Output

The application logs JSON to the system journal (syslog) when status changes are detected:

```json
{
  "event": "status_change",
  "timestamp": 1765189500,
  "interface": "wg0",
  "peer": "peer_public_key",
  "new_status": "connected"
}
```

On startup, the initial status of all peers is logged:

```json
{
  "event": "initial_status",
  "timestamp": 1765189500,
  "interface": "wg0",
  "peer": "peer_public_key",
  "status": "connected",
  "endpoint": "57.128.189.209:51823",
  "allowedIps": ["10.150.94.2/32", "10.161.1.101/32"]
}
```

## Data Source

The application executes a bash script that outputs WireGuard status as JSON. By default, it uses the `tools/wg-json.bash` script from the [WireGuard tools repository](https://github.com/WireGuard/wireguard-tools). The script is always run with `sudo /usr/bin/bash` for required privileges.

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
5. Status changes are logged to syslog as JSON
6. Current status is available via `/raw` endpoint

## Troubleshooting

- **No output or error "Script execution timed out"**: The bash script is taking too long to execute. Ensure the script at `WIREGUARD_MONITOR_WG_JSON_SCRIPT` completes within 10 seconds
- **Error "Script failed"**: The bash script exited with a non-zero status. Check the error message and ensure the script has proper permissions (chmod +x)
- **JSON parsing error**: Ensure the bash script outputs valid JSON. Test it manually: `bash ./tools/wg-json.bash`
- **Connection issues**: Verify the Flask server is running on the configured host and port (check `WIREGUARD_MONITOR_HOST` and `WIREGUARD_MONITOR_PORT` environment variables)
- **Configuration not applied**: Ensure environment variables are set before running the application

## License

This project is licensed under the GNU General Public License v3.0. See the LICENSE file for details.
