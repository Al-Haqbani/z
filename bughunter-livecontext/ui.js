// ui.js


document.getElementById('savePayload').addEventListener('click', async () => {
  const payload = document.getElementById('payload').value;
  await chrome.storage.local.set({ blindPayload: payload });
  appendLog('Payload saved');
});

document.getElementById('startScan').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.id) {
    chrome.tabs.sendMessage(tab.id, { type: 'start-scan' });
    appendLog('Started scan...');
  }
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'network') {
    appendLog(`Network: ${msg.details.method} ${msg.details.url}`);
    appendRequest(msg.details.method, msg.details.url);
  } else if (msg.type === 'dom') {
    appendLog(`DOM: ${msg.forms.length} forms, ${msg.inputs.length} inputs`);
  } else if (msg.type === 'svgUpload') {
    appendLog(`⚠️ Potential SVG upload point (${msg.count})`);
  } else if (msg.type === 'blindXSS') {
    appendLog(`⚠️ Potential Blind XSS point (${msg.count} forms)`);
  } else if (msg.type === 'injection') {
    appendLog(`Injected payload into ${msg.count} fields`);
  } else if (msg.type === 'scan-complete') {
    appendLog(`Scan complete: ${msg.forms} forms, ${msg.inputs} inputs`);
  }
});

async function init() {
  const { blindPayload } = await chrome.storage.local.get('blindPayload');
  if (blindPayload) {
    document.getElementById('payload').value = blindPayload;
  }
}

function appendLog(text) {
  const log = document.getElementById('log');
  const div = document.createElement('div');
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

function appendRequest(method, url) {
  const tbody = document.querySelector('#requestTable tbody');
  if (!tbody) return;
  const row = document.createElement('tr');
  const methodCell = document.createElement('td');
  methodCell.textContent = method;
  const urlCell = document.createElement('td');
  urlCell.textContent = url;
  row.appendChild(methodCell);
  row.appendChild(urlCell);
  tbody.appendChild(row);
}

init();
