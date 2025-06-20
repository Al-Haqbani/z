// background.js - service worker
importScripts('network-monitor.js');

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === 'injection') {
    console.log('Injection attempt', msg.count);
  }
});
