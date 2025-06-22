// dom-inspector.js
// Scans forms and inputs then reports them to the background script
export function inspectDOM() {
  const forms = Array.from(document.querySelectorAll('form')).map(f => ({
    action: f.action,
    method: f.method || 'get',
    hasTextarea: f.querySelector('textarea') !== null
  }));
  const inputs = Array.from(document.querySelectorAll('input, textarea, select, button, [contenteditable="true"]')).map(el => ({
    tag: el.tagName.toLowerCase(),
    type: el.type || '',
    name: el.name || el.id || ''
  }));
  chrome.runtime.sendMessage({ type: 'dom', forms, inputs });
  return { forms, inputs };
}
