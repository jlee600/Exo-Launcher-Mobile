import os
import time
import threading
import subprocess
import shlex
from config import Local_Paths
from app.logger import logger

def _kill_process(pattern):
    subprocess.run(f"sudo pkill -15 -f {shlex.quote(pattern)}", shell=True)

class HardwareMonitor:
    def __init__(self, interval=3):
        self.interval = interval
        self.running = False
        os.makedirs(os.path.dirname(Local_Paths.OUTPUT), exist_ok=True)

    def update_cycle(self):
        logger.info("[MONITOR] Cleaning up old watchdogs...")
        _kill_process("connection_hub.py")
        _kill_process("setup_watchdog.py")
        
        logger.info("[MONITOR] Running initial setup_devices.sh...")
        subprocess.run(["sudo", "-n", "bash", Local_Paths.SETUP_DEVICES_SCRIPT])

        compare_cmd = (
            f"python3 {shlex.quote(Local_Paths.COMPARE_SCRIPT)} "
            f"--req {shlex.quote(Local_Paths.CONTROLLER_CONFIGS)} "
            f"--meta {shlex.quote(Local_Paths.META)} "
            f"--out {shlex.quote(Local_Paths.OUTPUT)}"
        )

        while self.running:
            try:
                subprocess.run(["bash", "-c", compare_cmd], capture_output=True)
            except Exception as e:
                logger.error(f"[MONITOR] Compare loop error: {e}")
            
            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.update_cycle, daemon=True).start()
            logger.info("[MONITOR] Hardware monitor started")