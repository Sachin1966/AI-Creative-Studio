const BASE = '/api';  // proxied to localhost:8000 via vite

async function request(method, path, body, isForm = false) {
  const opts = { method };
  if (body) {
    if (isForm) {
      opts.body = body;
    } else {
      opts.headers = { 'Content-Type': 'application/json' };
      opts.body = JSON.stringify(body);
    }
  }
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const generateImage   = (payload) => request('POST', '/generate-image', payload);
export const enhancePrompt   = (prompt)  => request('GET', `/enhance-prompt?prompt=${encodeURIComponent(prompt)}`);
export const captionImage    = (file)    => { const fd = new FormData(); fd.append('file', file); return request('POST', '/caption-image', fd, true); };
export const generateTTS     = (payload) => request('POST', '/tts', payload);
export const transcribeAudio = (file)    => { const fd = new FormData(); fd.append('file', file); return request('POST', '/transcribe', fd, true); };
export const getTemplates    = ()        => request('GET', '/prompt-templates');
export const generateText      = (payload) => request('POST', '/generate-text', payload);


