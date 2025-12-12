# Changelog

## 1.0.2 - 2025-12-12
- Always use sudo and explicit /usr/bin/bash for the WireGuard status script subprocess.
- Update default monitoring intervals: connected (180s), disconnected (240s), check interval (10s).
- Update WG_JSON_SCRIPT default path for consistency.

## 1.0.1 - 2025-12-12
- Add support for running monitor_loop with Gunicorn and environment variable-based host/port configuration.
- Improve peer status change detection and logging.
- Only log all peers on start; log individual peer status changes after.
- Maintain timestamp field in logs.
- Use GPLv3 license.

## 1.0.0 - 2025-12-11
- Initial release with Flask app, WireGuard peer monitoring, and syslog integration.
- Basic peer connection/disconnection detection and logging.
- Raw status endpoint.
