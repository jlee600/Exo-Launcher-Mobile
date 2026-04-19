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
    if not os.path.exists(Local_Paths.OUTPUT):
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
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

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
    
    try:
        proc = subprocess.Popen(["bash", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            proc.wait(timeout=2.0)
            if proc.returncode != 0:
                err = proc.stderr.read().decode('utf-8').strip()
                return (False, f"Crashed immediately: {err}")
        except subprocess.TimeoutExpired:
            pass
    except Exception as e:
        return (False, str(e))

    devices_cmd = f"sudo -n bash {shlex.quote(Local_Paths.DEVICES_SCRIPT)}"
    subprocess.run(devices_cmd, shell=True)
    
    return (True, "Started successfully")

def run_flexible_controller(name, config):
    normalized = name if name.endswith(".py") else f"{name}.py"
    
    try:
        os.makedirs(os.path.dirname(Local_Paths.FLEX_CONFIG), exist_ok=True)
        with open(Local_Paths.FLEX_CONFIG, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        return (False, str(e))

    if config.get("Xsensors"):
        _kill_process("producer.py")
        user = SystemConfig.USER
        x_cmd = f"source ~/miniconda3/etc/profile.d/conda.sh && conda activate {user} && nohup python xscore/xscore_driver/xscore_driver/producer.py > /dev/null 2>&1 < /dev/null &"
        subprocess.Popen(["bash", "-c", x_cmd])
        time.sleep(2) 

    return run_controller(normalized)

def stop_controller(name):
    normalized = name if name.endswith(".py") else f"{name}.py"

    _kill_process("connection_hub.py")
    _kill_process(normalized)
    _kill_process("producer.py")

    setup_cmd = f"sudo -n bash {shlex.quote(Local_Paths.SETUP_DEVICES_SCRIPT)}"
    subprocess.run(setup_cmd, shell=True)
    
    return (True, "Stopped")