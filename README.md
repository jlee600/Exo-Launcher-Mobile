# Jetson-Mobile-Server (eflash-mobile)

This repository is the mobile-optimized version of the [Exo-Launcher (Laptop UI version)](https://github.com/jlee600/Exo-Launcher). It is designed to provide seamless, real-time control and monitoring of exoskeleton experiments using mobile devices (iOS/Android) or iOS Shortcuts, eliminating the need for a laptop in the field.

## 1. Overview & Motivation
The original Exo-Launcher relied on a laptop acting as a middleman server to send commands to the Jetson via SSH. In contrast, **Jetson-Mobile-Server** transforms the NVIDIA Jetson into a standalone Web and API server. By communicating directly with mobile devices, it minimizes communication latency and maximizes portability for lab and field experiments.

## 2. Technical Architecture

### Standalone Jetson Server Model
- **Backend**: Python 3 / Flask (REST API)
- **Frontend**: Mobile-first Vanilla JS / CSS3 (No external frameworks)
- **Process Management**: Local execution using Python `subprocess` & `Popen`
- **Hardware Sync**: Low-overhead local JSON polling

### Core Technical Modules
1. **Local Executor (`executor.py`)**: 
   - Replaces the SSH ControlMaster logic with direct local `subprocess` calls. 
   - Utilizes explicit Conda environment paths to prevent dependency conflicts with hardware libraries (e.g., MSCL).
   - Uses `nohup` to ensure controller processes remain active even if the web session or network connection is interrupted.
2. **Hardware Monitor (`monitor.py`)**: 
   - Runs a dedicated background thread to execute `setup_devices.sh`, scanning the CAN bus and USB ports. 
   - Generates `comparison_output.json` and `meta.json` locally, which are served immediately via API endpoints to provide real-time hardware readiness status.
3. **Network Manager (`wifi_manager.py`)**: 
   - Interfaces with Linux `nmcli` to manage automated connections to high-speed lab networks (e.g., CAREN_5G) and monitor signal stability.

## 3. Key API Endpoints
- `POST /api/run`: Executes a specific controller script (requires `name` parameter).
- `POST /api/stop`: Force-terminates all active controller processes and watchdogs using `pkill`.
- `POST /api/flexible-run`: Executes controllers with dynamic device-to-position mapping via `flexible_config.json`.
- `GET /api/status`: Returns current hardware connectivity and controller readiness state.

## 4. iOS Shortcuts Integration
Since the server provides a standard REST API, you can use the **"Get Contents of URL"** action in the iOS Shortcuts app to:
- **One-Tap Execution**: Launch specific experiment modes from a Home Screen widget.
- **Voice Control**: Trigger controllers using Siri (e.g., "Siri, start Hike Mode").
- **Emergency Stop**: Instantly halt all motors with a physical or digital shortcut without opening a browser.

## 5. Setup & Prerequisites
1. **Jetson Environment**: `miniconda3` must be installed. Ensure the `USER` variable in `config.py` matches your Jetson username.
2. **Dependencies**:
   ```bash
   pip install flask flask-cors
   ```
3. **Permissions**: Ensure the user has `sudo` privileges for `nmcli` and hardware-level bus restarts.

## 6. Usage
```bash
python main.py
```
Once the server is running, access the dashboard by navigating to `http://[Jetson_IP]:8000` on your mobile browser.