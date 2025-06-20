// svg-watcher.js
// Detects file upload fields that accept SVGs
export function detectSvgUploads(inputs) {
  const fileInputs = inputs.filter(i => i.type === 'file');
  const svgInputs = fileInputs.filter(i => {
    const el = document.querySelector(`[name="${i.name}"]`);
    return el && /svg/i.test(el.accept || '');
  });
  if (svgInputs.length) {
    chrome.runtime.sendMessage({ type: 'svgUpload', count: svgInputs.length });
  }
}
