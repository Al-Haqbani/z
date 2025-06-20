// ui.js
import { saveKey, loadKey } from './storage.js';

document.getElementById('saveKey').addEventListener('click', async () => {
  const key = document.getElementById('apiKey').value;
  await saveKey(key);
  appendLog('API key saved');
});

document.getElementById('savePayload').addEventListener('click', async () => {
  const payload = document.getElementById('payload').value;
  await chrome.storage.local.set({ blindPayload: payload });
  appendLog('Payload saved');
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'network') {
    appendLog(`Network: ${msg.details.method} ${msg.details.url}`);
  } else if (msg.type === 'dom') {
    appendLog(`DOM: ${msg.forms.length} forms, ${msg.inputs.length} inputs`);
  } else if (msg.type === 'svgUpload') {
    appendLog(`⚠️ Potential SVG upload point (${msg.count})`);
  } else if (msg.type === 'blindXSS') {
    appendLog(`⚠️ Potential Blind XSS point (${msg.count} forms)`);
  } else if (msg.type === 'injection') {
    appendLog(`Injected payload into ${msg.count} fields`);
  } else if (msg.type === 'ai') {
    appendLog(`AI: ${msg.result.choices?.[0]?.message?.content || ''}`);
  }
});

async function init() {
  const { openaiKey } = await loadKey();
  if (openaiKey) {
    document.getElementById('apiKey').value = openaiKey;
  }
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
}

init();
