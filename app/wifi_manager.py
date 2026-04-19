import subprocess
from app.logger import logger

def get_current_ssid():
    try:
        res = subprocess.run(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"], capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if line.startswith("yes:"):
                return line.split(":")[1]
    except Exception:
        pass
    return "Unknown"

def connect_wifi(ssid, password):
    try:
        res = subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password], capture_output=True, text=True)
        return res.returncode == 0
    except Exception as e:
        logger.error(f"[WIFI] Error: {e}")
        return False