// network-monitor.js
// Captures network requests and forwards details to the extension UI
chrome.webRequest.onCompleted.addListener(
  details => {
    chrome.runtime.sendMessage({ type: 'network', details });
  },
  { urls: ['<all_urls>'] }
);
