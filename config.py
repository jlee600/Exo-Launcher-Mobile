import os

class SystemConfig:
    USER = "boggs"
    HOST = "0.0.0.0"
    PORT = 8000
    API_PORT = 8321

class Local_Paths:
    ROOT = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(ROOT, "data")
    CONTROLLERS_DIR = "/home/boggs/hip-exo-controllers/controllers/"
    
    OUTPUT = os.path.join(DATA_DIR, "comparison_output.json")
    META = "/home/boggs/hip-exo-controllers/readiness/meta.json"
    FLEX_CONFIG = "/home/boggs/hip-exo-controllers/readiness/flexible_config.json"
    CONTROLLER_CONFIGS = "/home/boggs/hip-exo-controllers/controllers/controller_configs.json"
    
    SETUP_DEVICES_SCRIPT = "/home/boggs/trek/trek/util/misc/scripts/setup_devices.sh"
    DEVICES_SCRIPT = "/home/boggs/trek/trek/util/misc/scripts/devices.sh"

class Wifi_Credentials:
    SSID = "CAREN_5G"
    PASSWORD = "CARENCAREN"