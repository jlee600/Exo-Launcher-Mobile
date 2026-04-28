const API_BASE = window.location.origin;
let runningController = null;
let currentFlexTarget = null;
let lastMeta = null;

async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    const data = await res.json();
    if (data.ok) {
      lastMeta = data.meta;
      updateUI(data.output, data.meta);
      updateHWStatus(data.meta);
      document.getElementById('connection-status').className = "status-badge online";
      document.getElementById('connection-status').textContent = "Online";
    }
  } catch (err) {
    document.getElementById('connection-status').className = "status-badge";
    document.getElementById('connection-status').textContent = "Offline";
  }
}

function updateHWStatus(meta) {
  const sBody = document.querySelector('#sensor-table tbody');
  const mBody = document.querySelector('#motor-table tbody');
  
  sBody.innerHTML = (meta.IMUs || []).map(id => `<tr><td>${id}</td><td>IMU</td></tr>`).join('');
  mBody.innerHTML = (meta.Motors || []).map(m => `<tr><td>${m.id}</td><td>${m.type}</td></tr>`).join('');
}

function updateUI(output, meta) {
  const list = document.getElementById('controller-list');
  const query = document.getElementById('ctrl-search').value.toLowerCase();
  const controllers = output.controllers || {};
  
  list.innerHTML = "";
  Object.entries(controllers).forEach(([name, info]) => {
    if (query && !name.toLowerCase().includes(query) && !info.missing?.join(' ').toLowerCase().includes(query)) return;

    const isReady = info.status === 1;
    const isRunning = runningController === name;
    const isFlex = name.toLowerCase().includes('flex');
    const errors = (info.missing || []).map(m => `• ${m}`).join('<br>');

    const card = document.createElement('div');
    card.className = `card ${isReady ? 'ready' : 'blocked'}`;
    card.innerHTML = `
      <div class="card-info">
        <div class="card-name">${name.replace('.py', '')}</div>
        <div class="card-status">${isReady ? '<span style="color:var(--success)">Ready</span>' : '<small>'+errors+'</small>'}</div>
      </div>
      <button class="btn-action ${isRunning ? 'btn-stop' : (isReady ? 'btn-run' : 'btn-disabled')}" 
              onclick="handleActionClick('${name}', ${isRunning}, ${isReady}, ${isFlex})">
        ${isRunning ? 'STOP' : 'RUN'}
      </button>
    `;
    list.appendChild(card);
  });
}

function openFlexModal(name) {
  currentFlexTarget = name;
  const imus = lastMeta?.IMUs || [];
  const motors = (lastMeta?.Motors || []).map(m => m.id);
  
  const imuSelects = ['f-imu-pelvis', 'f-imu-rt', 'f-imu-rs', 'f-imu-lt', 'f-imu-ls'];
  const motorSelects = ['f-motor-rh', 'f-motor-lh'];

  imuSelects.forEach(id => {
    const el = document.getElementById(id);
    el.innerHTML = '<option value="0">-- select --</option>' + imus.map(v => `<option value="${v}">${v}</option>`).join('');
  });
  motorSelects.forEach(id => {
    const el = document.getElementById(id);
    el.innerHTML = '<option value="0">-- select --</option>' + motors.map(v => `<option value="${v}">${v}</option>`).join('');
  });

  document.getElementById('flex-modal').hidden = false;
}

async function submitFlexRun() {
  const config = {
    IMUs: {
      pelvis: Number(document.getElementById('f-imu-pelvis').value),
      "right.thigh": Number(document.getElementById('f-imu-rt').value),
      "right.shank": Number(document.getElementById('f-imu-rs').value),
      "left.thigh": Number(document.getElementById('f-imu-lt').value),
      "left.shank": Number(document.getElementById('f-imu-ls').value)
    },
    Motors: {
      "right.hip": { motor_id: Number(document.getElementById('f-motor-rh').value), motor_type: "AK80-9" },
      "left.hip": { motor_id: Number(document.getElementById('f-motor-lh').value), motor_type: "AK80-9", is_inverted: true }
    },
    Xsensors: document.getElementById('f-xsensors').checked
  };
  await callApi('/api/flexible-run', { name: currentFlexTarget, config });
  closeFlexModal();
}

function handleActionClick(name, isRunning, isReady, isFlex) {
  if (isRunning) callApi('/api/stop', { name });
  else if (isReady) isFlex ? openFlexModal(name) : callApi('/api/run', { name });
}

async function callApi(path, body) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const d = await res.json();
    if (d.ok) {
      runningController = path.includes('stop') ? null : body.name;
      showToast(d.message);
    } else showToast("Error: " + d.message);
  } catch (err) { showToast("Connection Failed"); }
}

function closeFlexModal() { document.getElementById('flex-modal').hidden = true; }
function showToast(msg) {
  const container = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = 'toast';
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

document.getElementById('ctrl-search').oninput = () => fetchStatus();
setInterval(fetchStatus, 3500);
fetchStatus();