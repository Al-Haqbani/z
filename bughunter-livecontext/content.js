// content.js - main content script
import { inspectDOM } from './dom-inspector.js';
import { detectSvgUploads } from './svg-watcher.js';
import { detectBlindXSS } from './xss-detector.js';
import { autoInject } from './injector.js';
import { analyze } from './ai-engine.js';

(async () => {
  const { forms, inputs } = inspectDOM();
  detectSvgUploads(inputs);
  detectBlindXSS(forms);
  const { blindPayload } = await chrome.storage.local.get('blindPayload');
  if (blindPayload) {
    await autoInject(blindPayload);
  }
  const contextPrompt = `Forms: ${forms.length}, Inputs: ${inputs.length}`;
  const ai = await analyze(contextPrompt);
  if (!ai.error) {
    chrome.runtime.sendMessage({ type: 'ai', result: ai });
  }
})();
