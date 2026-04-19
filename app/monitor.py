import os
import json
import time
import threading
import subprocess
from config import Local_Paths
from app.logger import logger

class HardwareMonitor:
    def __init__(self, interval=3):
        self.interval = interval
        self.running = False
        self._thread = None

    def _get_meta(self):
        try:
            if os.path.exists(Local_Paths.META):
                with open(Local_Paths.META, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"[MONITOR] Error reading meta: {e}")
        return {}

    def _get_configs(self):
        try:
            if os.path.exists(Local_Paths.CONTROLLER_CONFIGS):
                with open(Local_Paths.CONTROLLER_CONFIGS, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"[MONITOR] Error reading configs: {e}")
        return {}

    def _run_comparison(self, meta, configs):
        controllers = {}
        connected_imus = set(meta.get("IMUs", []))
        connected_motors = {m["id"]: m["type"] for m in meta.get("Motors", [])}
        x_available = meta.get("Xsensors", False)

        for name, req in configs.items():
            status = 1
            missing = []

            req_imus = req.get("IMUs", [])
            if isinstance(req_imus, list):
                for imu_id in req_imus:
                    if imu_id not in connected_imus:
                        status = 0
                        missing.append(f"IMU:id_missing({imu_id})")
            elif isinstance(req_imus, int):
                if len(connected_imus) < req_imus:
                    status = 0
                    missing.append(f"IMU:count_insufficient(req:{req_imus}, got:{len(connected_imus)})")

            req_motors = req.get("Motors", {})
            for loc, m_req in req_motors.items():
                m_id = m_req.get("motor_id")
                m_type = m_req.get("motor_type")
                if m_id not in connected_motors:
                    status = 0
                    missing.append(f"Motor:{loc}=id_missing({m_id})")
                elif connected_motors.get(m_id) != m_type:
                    status = 0
                    missing.append(f"Motor:{loc}=type_mismatch(req:{m_type}, got:{connected_motors.get(m_id)})")

            if req.get("Xsensors") and not x_available:
                status = 0
                missing.append("Xsensors:unavailable")

            controllers[name] = {"status": status, "missing": missing}

        return {
            "controllers": controllers,
            "summary": {
                "ready": sum(1 for c in controllers.values() if c["status"] == 1),
                "blocked": sum(1 for c in controllers.values() if c["status"] == 0),
                "unknown": 0
            }
        }

    def update_cycle(self):
        while self.running:
            try:
                subprocess.run(["sudo", "bash", Local_Paths.SETUP_DEVICES_SCRIPT], capture_output=True)
                
                meta = self._get_meta()
                configs = self._get_configs()
                comparison = self._run_comparison(meta, configs)
                
                with open(Local_Paths.OUTPUT, 'w') as f:
                    json.dump(comparison, f, indent=2)
                
            except Exception as e:
                logger.error(f"[MONITOR] Loop error: {e}")
            
            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self.update_cycle, daemon=True)
            self._thread.start()
            logger.info("[MONITOR] Hardware monitor started")