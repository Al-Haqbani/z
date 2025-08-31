// Simple wrappers around chrome.storage for settings
function saveKey(key) {
  return chrome.storage.local.set({ openaiKey: key });
}

function loadKey() {
  return chrome.storage.local.get('openaiKey');
}
