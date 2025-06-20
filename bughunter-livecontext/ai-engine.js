// ai-engine.js
// Calls OpenAI API using stored API key
export async function analyze(prompt) {
  const { openaiKey } = await chrome.storage.local.get('openaiKey');
  if (!openaiKey) {
    return { error: 'No API key' };
  }
  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${openaiKey}`
    },
    body: JSON.stringify({
      model: 'gpt-4',
      temperature: 0.2,
      messages: [{ role: 'user', content: prompt }]
    })
  });
  return res.json();
}
