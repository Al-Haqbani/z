// Handles UI logic for saving API key and displaying logs
document.getElementById('saveKey').addEventListener('click', async () => {
  const key = document.getElementById('apiKey').value;
  await saveKey(key);
  appendLog('API key saved');
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'network') {
    appendLog(`Network: ${msg.details.method} ${msg.details.url}`);
  } else if (msg.type === 'dom') {
    appendLog(`DOM analyzed: ${msg.forms.length} forms, ${msg.inputs.length} inputs`);
  }
});

function appendLog(text) {
  const log = document.getElementById('log');
  const div = document.createElement('div');
  div.textContent = text;
  log.appendChild(div);
}
