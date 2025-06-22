// content.js - main content script
import { inspectDOM } from './dom-inspector.js';
import { detectSvgUploads } from './svg-watcher.js';
import { detectBlindXSS } from './xss-detector.js';
import { autoInject } from './injector.js';


async function runScan() {
  const { forms, inputs } = inspectDOM();
  detectSvgUploads(inputs);
  detectBlindXSS(forms);
  const { blindPayload } = await chrome.storage.local.get('blindPayload');
  if (blindPayload) {
    await autoInject(blindPayload);
  }
  chrome.runtime.sendMessage({
    type: 'scan-complete',
    forms: forms.length,
    inputs: inputs.length
  });
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'start-scan') {
    runScan();
  }
});
