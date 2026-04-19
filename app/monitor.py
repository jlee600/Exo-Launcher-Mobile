import time
import threading
import subprocess
import shlex
from config import Local_Paths, SystemConfig
from app.logger import logger

class HardwareMonitor:
    def __init__(self, interval=4):
        self.interval = interval
        self.running = False

    def update_cycle(self):
        user = SystemConfig.USER
        
        compare_cmd = (
            f"python3 {shlex.quote(Local_Paths.COMPARE_SCRIPT)} "
            f"--req {shlex.quote(Local_Paths.CONTROLLER_CONFIGS)} "
            f"--meta {shlex.quote(Local_Paths.META)} "
            f"--out {shlex.quote(Local_Paths.OUTPUT)}"
        )

        while self.running:
            try:
                subprocess.run(["sudo", "-n", "bash", Local_Paths.SETUP_DEVICES_SCRIPT], capture_output=True)
                subprocess.run(["bash", "-c", compare_cmd], capture_output=True)
                
            except Exception as e:
                logger.error(f"[MONITOR] Loop error: {e}")
            
            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.update_cycle, daemon=True).start()
            logger.info("[MONITOR] Hardware monitor started via config_compare.py")