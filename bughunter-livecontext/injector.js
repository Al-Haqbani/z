// injector.js
// Attempts to inject a blind XSS payload into input fields
export async function autoInject(payload) {
  if (!payload) return;
  const inputs = document.querySelectorAll('input[type="text"], textarea');
  inputs.forEach(input => {
    input.value = payload;
  });
  const forms = document.querySelectorAll('form');
  forms.forEach(form => form.dispatchEvent(new Event('submit', { cancelable: true })));
  const { history = [] } = await chrome.storage.local.get('history');
  history.push({ payload, url: location.href, time: Date.now() });
  await chrome.storage.local.set({ history });
  chrome.runtime.sendMessage({ type: 'injection', count: inputs.length });
}
