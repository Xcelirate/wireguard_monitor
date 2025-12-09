# Changelog

## [1.0.1] - 2025-12-09
### Changed
- Ensure monitor_loop thread starts reliably in both development and production (Gunicorn) by using @app.before_request and a thread-safe lock.
- Remove usage of @app.before_first_request for compatibility with all Flask versions.
- Update README with Gunicorn config file instructions for dynamic host/port binding via environment variables.

## [1.0.0] - Initial Release
### Added
- Initial implementation of WireGuard Monitor with Flask REST API.
- Real-time monitoring of WireGuard peer status using a bash script.
- Peer status analysis (connected/disconnected) based on handshake timing.
- Syslog logging of peer status changes and initial status.
- Multi-interface and multi-peer support.
- Configurable intervals and script path via environment variables.
- /raw endpoint for current WireGuard status.
- GPLv3 license and documentation.

