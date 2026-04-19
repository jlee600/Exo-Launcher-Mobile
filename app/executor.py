import os
import json
import time
import re
import shlex
import subprocess
from config import Local_Paths, SystemConfig
from app.logger import logger

SAFE_NAME_RE = re.compile(r'^[A-Za-z0-9_\-\.]+$')

def ready_locally(name):
    if not SAFE_NAME_RE.match(name):
        return False
    try:
        with open(Local_Paths.OUTPUT, "r") as f:
            cmp = json.load(f)
        controllers = cmp.get("controllers", {})
        entry = controllers.get(name) or controllers.get(f"{name}.py")
        return bool(entry and entry.get("status") == 1)
    except Exception as e:
        logger.error(f"[EXECUTOR] Failed to read readiness: {e}")
        return False

def _kill_process(pattern):
    cmd = f"sudo pkill -15 -f {shlex.quote(pattern)}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        logger.info(f"[EXECUTOR] Stopped process matching: {pattern}")
    return result

def run_controller(name):
    normalized = name if name.endswith(".py") else f"{name}.py"
    if not ready_locally(normalized):
        return (False, f"Controller not ready or unknown: {normalized}")
    
    _kill_process("setup_watchdog.py")

    user = SystemConfig.USER
    conda_env = f"/home/{user}/miniconda3/envs/{user}"
    
    cmd = (
        f"source ~/miniconda3/etc/profile.d/conda.sh && "
        f"conda activate {conda_env} && "
        f"cd {shlex.quote(Local_Paths.CONTROLLERS_DIR)} && "
        f"nohup {conda_env}/bin/python {shlex.quote(normalized)} > controller.log 2>&1 < /dev/null &"
    )
    
    logger.warning(f"[EXECUTOR] Running {normalized} locally...")
    
    try:
        proc = subprocess.Popen(["bash", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            proc.wait(timeout=2.0)
            if proc.returncode != 0:
                err = proc.stderr.read().decode('utf-8').strip()
                return (False, f"Crashed immediately:\n{err}")
        except subprocess.TimeoutExpired:
            logger.info("[EXECUTOR] Controller started successfully in background.")
    except Exception as e:
        return (False, f"Failed to start controller: {str(e)}")

    devices_cmd = f"sudo -n bash {shlex.quote(Local_Paths.DEVICES_SCRIPT)}"
    logger.warning("[EXECUTOR] Setting up active devices...")
    res = subprocess.run(devices_cmd, shell=True, capture_output=True, text=True)
    
    if res.returncode != 0:
        logger.error(f"[EXECUTOR] Device setup failed:\n{res.stderr}")
    else:
        logger.info("[EXECUTOR] Active device setup successful.")

    return (True, "Local controller started successfully")


def run_flexible_controller(name, config):
    """
    Flexible Controller용 Config를 로컬에 저장하고 실행합니다.
    (기존 SCP 전송 로직이 완전히 제거되었습니다.)
    """
    normalized = name if name.endswith(".py") else f"{name}.py"
    
    try:
        with open(Local_Paths.FLEX_CONFIG, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"[EXECUTOR] Flexible config written to {Local_Paths.FLEX_CONFIG}")
    except Exception as e:
        return (False, f"Failed to write local flexible config: {e}")

    if config.get("Xsensors"):
        logger.warning("[EXECUTOR] Xsensors enabled. Launching xscore-producer...")
        _kill_process("producer.py")
        
        user = SystemConfig.USER
        xsens_cmd = (
            f"source ~/miniconda3/etc/profile.d/conda.sh && "
            f"conda activate /home/{user}/miniconda3/envs/{user} && "
            "nohup python xscore/xscore_driver/xscore_driver/producer.py > /dev/null 2>&1 < /dev/null &"
        )
        subprocess.Popen(["bash", "-c", xsens_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2) 

    return run_controller(normalized)


def stop_controller(name):
    """
    실행 중인 컨트롤러와 관련 프로세스를 강제 종료하고 초기 상태로 되돌립니다.
    """
    normalized = name if name.endswith(".py") else f"{name}.py"

    _kill_process("connection_hub.py")
    
    logger.warning(f"[EXECUTOR] Stopping local controller: {normalized}")
    _kill_process(normalized)
    
    _kill_process("producer.py")

    setup_cmd = f"sudo -n bash {shlex.quote(Local_Paths.SETUP_DEVICES_SCRIPT)}"
    logger.warning("[EXECUTOR] Resetting CAN bus and devices...")
    res = subprocess.run(setup_cmd, shell=True, capture_output=True, text=True)
    
    if res.returncode != 0:
        logger.error(f"[EXECUTOR] Device reset failed:\n{res.stderr}")
    else:
        logger.info("[EXECUTOR] Device reset successful.")

    return (True, "Stopped successfully.")