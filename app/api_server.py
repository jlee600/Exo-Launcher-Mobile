from flask import Flask, request, jsonify
from flask_cors import CORS
from app.executor import run_controller, stop_controller, run_flexible_controller
from config import SystemConfig
from app.logger import logger
import os
import json

app = Flask(__name__)
CORS(app)

@app.route('/api/run', methods=['POST'])
def api_run():
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({"ok": False, "message": "Name is required"}), 400
    
    ok, msg = run_controller(name)
    status_code = 200 if ok else 400
    return jsonify({"ok": ok, "message": msg}), status_code

@app.route('/api/stop', methods=['POST'])
def api_stop():
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({"ok": False, "message": "Name is required"}), 400
    
    ok, msg = stop_controller(name)
    status_code = 200 if ok else 400
    return jsonify({"ok": ok, "message": msg}), status_code

@app.route('/api/flexible-run', methods=['POST'])
def api_flexible_run():
    data = request.get_json() or {}
    name = data.get('name')
    config = data.get('config')
    
    if not name or not config:
        return jsonify({"ok": False, "message": "Name and config are required"}), 400
    
    ok, msg = run_flexible_controller(name, config)
    status_code = 200 if ok else 400
    return jsonify({"ok": ok, "message": msg}), status_code

@app.route('/api/status', methods=['GET'])
def api_status():
    from config import Local_Paths
    
    try:
        if os.path.exists(Local_Paths.OUTPUT):
            with open(Local_Paths.OUTPUT, 'r') as f:
                output_data = json.load(f)
        else:
            output_data = {}
            
        if os.path.exists(Local_Paths.META):
            with open(Local_Paths.META, 'r') as f:
                meta_data = json.load(f)
        else:
            meta_data = {}

        return jsonify({
            "ok": True,
            "output": output_data,
            "meta": meta_data
        })
    except Exception as e:
        logger.error(f"[API] Error reading status: {e}")
        return jsonify({"ok": False, "message": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({"ok": True, "status": "running"}), 200

def start_server():
    app.run(host=SystemConfig.HOST, port=SystemConfig.PORT, threaded=True)

if __name__ == '__main__':
    start_server()