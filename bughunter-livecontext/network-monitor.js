// network-monitor.js
// Captures network requests and forwards details to the extension UI
chrome.webRequest.onCompleted.addListener(
  details => {
    chrome.runtime.sendMessage({ type: 'network', details });
    storeRequest(details);
  },
  { urls: ['<all_urls>'] }
);

async function storeRequest(details) {
  const { reqLog = [] } = await chrome.storage.local.get('reqLog');
  reqLog.push({ method: details.method, url: details.url, time: Date.now() });
  await chrome.storage.local.set({ reqLog });
}
