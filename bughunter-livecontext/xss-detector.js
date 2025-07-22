// xss-detector.js
// Looks for potential blind XSS sinks
export function detectBlindXSS(forms) {
  const keywords = [
    'comment',
    'feedback',
    'message',
    'description',
    'note',
    'bio',
    'about',
    'username',
    'profile'
  ];

  const blindForms = forms.filter(f => {
    const matchesField = keywords.some(name => {
      const q1 = document.querySelectorAll(`input[name*="${name}"]`);
      const q2 = document.querySelectorAll(`textarea[name*="${name}"]`);
      return q1.length > 0 || q2.length > 0;
    });
    const editable = document.querySelectorAll('[contenteditable="true"]');
    return matchesField || f.hasTextarea || editable.length > 0;
  });

  if (blindForms.length) {
    chrome.runtime.sendMessage({ type: 'blindXSS', count: blindForms.length });
  }
}
