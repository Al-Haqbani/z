// storage.js
export async function getHistory() {
  const { history = [] } = await chrome.storage.local.get('history');
  return history;
}

export async function getRequestLog() {
  const { reqLog = [] } = await chrome.storage.local.get('reqLog');
  return reqLog;
}
