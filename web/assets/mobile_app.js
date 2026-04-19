const API_BASE = window.location.origin;
let runningController = null;
let currentFlexTarget = null;

async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    const data = await res.json();
    if (data.ok) {
      updateUI(data.output, data.meta);
      const badge = document.getElementById('connection-status');
      badge.textContent = "Online";
      badge.className = "status-badge online";
    }
  } catch (err) {
    document.getElementById('connection-status').textContent = "Offline";
    document.getElementById('connection-status').className = "status-badge";
  }
}

function updateUI(output, meta) {
  const list = document.getElementById('controller-list');
  const controllers = output.controllers || {};
  
  list.innerHTML = "";
  Object.entries(controllers).forEach(([name, info]) => {
    const isReady = info.status === 1;
    const isRunning = runningController === name;
    const isFlex = name.toLowerCase().includes('flex');
    
    // Safety check for missing array
    const errors = (info.missing || []).map(m => `• ${m}`).join('<br>');

    const card = document.createElement('div');
    card.className = `card ${isReady ? 'ready' : 'blocked'}`;
    card.innerHTML = `
      <div class="card-info">
        <div class="card-name">${name.replace('.py', '')}</div>
        <div class="card-status">
          ${isReady ? '<span style="color:var(--success)">● Ready</span>' : 
                      '<span style="color:var(--danger)">● Blocked</span><br><small>'+errors+'</small>'}
        </div>
      </div>
      <button class="btn-action ${isRunning ? 'btn-stop' : (isReady ? 'btn-run' : 'btn-disabled')}" 
              onclick="handleActionClick('${name}', ${isRunning}, ${isReady}, ${isFlex})">
        ${isRunning ? 'STOP' : 'RUN'}
      </button>
    `;
    list.appendChild(card);
  });

  document.getElementById('wifi-name').textContent = meta.WiFi || "—";
  document.getElementById('jetson-host').textContent = meta.JetsonHost || "—";
  document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
}

function handleActionClick(name, isRunning, isReady, isFlex) {
  if (isRunning) {
    callApi('/api/stop', { name });
  } else if (isReady) {
    if (isFlex) {
      currentFlexTarget = name;
      document.getElementById('flex-modal').hidden = false;
    } else {
      callApi('/api/run', { name });
    }
  }
}

async function submitFlexRun() {
  const config = {
    IMUs: {
      pelvis: Number(document.getElementById('f-imu-pelvis').value),
      "right.thigh": Number(document.getElementById('f-imu-rt').value),
      "left.thigh": Number(document.getElementById('f-imu-lt').value)
    },
    Motors: {
      "right.hip": { motor_id: Number(document.getElementById('f-motor-rh').value), motor_type: "AK80-9" },
      "left.hip": { motor_id: Number(document.getElementById('f-motor-lh').value), motor_type: "AK80-9", is_inverted: true }
    },
    Xsensors: true
  };
  
  await callApi('/api/flexible-run', { name: currentFlexTarget, config });
  closeFlexModal();
}

function closeFlexModal() {
  document.getElementById('flex-modal').hidden = true;
}

async function callApi(path, body) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.ok) {
      runningController = path.includes('stop') ? null : body.name;
      showToast(data.message || "Success");
    } else {
      showToast("Error: " + data.message);
    }
    fetchStatus();
  } catch (err) {
    showToast("Server Connection Failed");
  }
}

function showToast(msg) {
  const container = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = 'toast';
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

setInterval(fetchStatus, 4000);
fetchStatus();