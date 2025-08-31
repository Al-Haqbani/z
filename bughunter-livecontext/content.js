// Extracts form fields and other potential entry points from the page
document.addEventListener('DOMContentLoaded', () => {
  const forms = Array.from(document.querySelectorAll('form')).map(f => ({action: f.action, method: f.method}));
  const inputs = Array.from(document.querySelectorAll('input, textarea, select, button')).map(el => ({tag: el.tagName.toLowerCase(), name: el.name || el.id || ''}));
  chrome.runtime.sendMessage({ type: 'dom', forms, inputs });
});
