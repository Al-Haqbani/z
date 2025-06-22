// storage.js
export function saveKey(key) {
  return chrome.storage.local.set({ openaiKey: key });
}

export function loadKey() {
  return chrome.storage.local.get('openaiKey');
}

export async function getHistory() {
  const { history = [] } = await chrome.storage.local.get('history');
  return history;
}

export async function getRequestLog() {
  const { reqLog = [] } = await chrome.storage.local.get('reqLog');
  return reqLog;
}
