// Monitors network requests and sends details to the extension UI
chrome.webRequest.onCompleted.addListener(
  (details) => {
    chrome.runtime.sendMessage({ type: 'network', details });
  },
  { urls: ['<all_urls>'] }
);
