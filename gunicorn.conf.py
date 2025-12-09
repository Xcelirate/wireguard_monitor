import os
bind = f"{os.environ.get('WIREGUARD_MONITOR_HOST', '127.0.0.1')}:{os.environ.get('WIREGUARD_MONITOR_PORT', '8000')}"

