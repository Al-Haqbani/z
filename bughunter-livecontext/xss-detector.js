// xss-detector.js
// Looks for potential blind XSS sinks
export function detectBlindXSS(forms) {
  const suspiciousNames = ['comment', 'feedback', 'message', 'description', 'note'];
  const blindForms = forms.filter(f => {
    return suspiciousNames.some(name => {
      return Array.from(document.querySelectorAll(`input[name*="${name}"]`)).length > 0 ||
             Array.from(document.querySelectorAll(`textarea[name*="${name}"]`)).length > 0;
    }) || f.hasTextarea;
  });
  if (blindForms.length) {
    chrome.runtime.sendMessage({ type: 'blindXSS', count: blindForms.length });
  }
}
