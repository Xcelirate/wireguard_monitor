# Changelog

## 1.1.0 - 2026-06-02
- Add `WIREGUARD_MONITOR_INTERFACES` environment variable to restrict monitoring to a comma-separated allow-list of WireGuard interfaces. When unset (default), all interfaces are monitored. Filtering is applied in `main.py` after parsing the script output, so `tools/wg-json.bash` is unchanged and `/raw`, status analysis, and logging all see a consistent view. Configured interfaces that are not present on the host trigger a one-time warning log.

## 1.0.4 - 2026-02-02
- Change logging from SysLogHandler (syslog) to StreamHandler (stdout) for compatibility with systemd and containerized environments. Logs now go to stdout instead of /dev/log.

## 1.0.3 - 2025-12-18
- Handle fresh peers that have never connected by checking for `latestHandshake` field existence.
- Mark peers without `latestHandshake` as "never_connected" status instead of causing errors.

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
