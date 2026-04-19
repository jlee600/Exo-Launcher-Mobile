const API_BASE = window.location.origin; 
let runningController = null;

async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    const data = await res.json();
    if (data.ok) {
      updateUI(data.output, data.meta);
      document.getElementById('connection-status').textContent = "Online";
      document.getElementById('connection-status').classList.add('online');
    }
  } catch (err) {
    document.getElementById('connection-status').textContent = "Offline";
    document.getElementById('connection-status').classList.remove('online');
  }
}

function updateUI(output, meta) {
  const list = document.getElementById('controller-list');
  const controllers = output.controllers || {};
  
  list.innerHTML = "";
  Object.entries(controllers).forEach(([name, info]) => {
    const card = document.createElement('div');
    const isReady = info.status === 1;
    const isRunning = runningController === name;
    
    card.className = `card ${isReady ? 'ready' : 'blocked'}`;
    card.innerHTML = `
      <div class="card-info">
        <div class="card-name">${name.replace('.py', '')}</div>
        <div class="card-status">${isReady ? 'Ready to run' : info.missing.join(', ')}</div>
      </div>
      <button class="btn-action ${isRunning ? 'btn-stop' : (isReady ? 'btn-run' : 'btn-disabled')}" 
              onclick="handleAction('${name}', ${isRunning}, ${isReady})">
        ${isRunning ? 'STOP' : 'RUN'}
      </button>
    `;
    list.appendChild(card);
  });

  document.getElementById('wifi-name').textContent = meta.WiFi || "Unknown";
  document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
}

async function handleAction(name, isRunning, isReady) {
  if (!isRunning && !isReady) return;

  const endpoint = isRunning ? '/api/stop' : '/api/run';
  showToast(isRunning ? "Stopping..." : "Starting...");

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name })
    });
    const data = await res.json();

    if (data.ok) {
      runningController = isRunning ? null : name;
      showToast(data.message);
    } else {
      showToast("Error: " + data.message);
    }
  } catch (err) {
    showToast("Server connection error");
  }
}

function showToast(msg) {
  const container = document.getElementById('toast-root') || document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

setInterval(fetchStatus, 4000);
fetchStatus();