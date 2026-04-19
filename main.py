import signal
import sys
import time
from app.api_server import app
from app.monitor import HardwareMonitor
from app.wifi_manager import connect_wifi
from config import SystemConfig, Wifi_Credentials
from app.logger import logger

def main():
    logger.info("Starting Jetson Mobile Server...")

    if not connect_wifi(Wifi_Credentials.SSID, Wifi_Credentials.PASSWORD):
        logger.warning("Wi-Fi connection failed, continuing with local network...")

    monitor = HardwareMonitor(interval=4)
    monitor.start()

    def handle_exit(sig, frame):
        logger.warning("Shutting down...")
        monitor.running = False
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    logger.info(f"API Server running on http://{SystemConfig.HOST}:{SystemConfig.PORT}")
    app.run(host=SystemConfig.HOST, port=SystemConfig.PORT, debug=False, threaded=True)

if __name__ == "__main__":
    main()