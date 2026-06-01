import { useState, useEffect } from 'react';
import { getTemplates } from '../api';

export default function PromptLibrary({ goToImageTab }) {
  const [templates, setTemplates] = useState({});
  const [category, setCategory]   = useState('');
  const [loading, setLoading]     = useState(true);
  const [toast, setToast]         = useState('');

  useEffect(() => {
    getTemplates()
      .then(data => {
        setTemplates(data);
        setCategory(Object.keys(data)[0] || '');
      })
      .catch(() => setTemplates({}))
      .finally(() => setLoading(false));
  }, []);

  const handleUse = (prompt) => {
    goToImageTab(prompt);
    setToast('✅ Prompt set! Switching to Image Generator…');
    setTimeout(() => setToast(''), 3000);
  };

  if (loading) return (
    <div>
      <div className="page-header"><h2>📚 Prompt Library</h2></div>
      <div className="loading-overlay"><span className="spinner spinner-lg" /><p>Loading templates…</p></div>
    </div>
  );

  const categories = Object.keys(templates);
  const prompts    = templates[category] || [];

  return (
    <div>
      <div className="page-header">
        <h2>📚 Prompt Library</h2>
        <p>48+ curated AI prompts. Click "Use Prompt" to instantly load it into the Image Generator.</p>
      </div>

      {toast && <div className="alert alert-success">{toast}</div>}

      {/* Category Pills */}
      <div className="tab-bar" style={{ flexWrap: 'wrap', width: '100%', marginBottom: 20 }}>
        {categories.map(cat => (
          <button key={cat} className={`tab-btn ${category === cat ? 'active' : ''}`}
            onClick={() => setCategory(cat)} style={{ fontSize: 12 }}>
            {cat}
          </button>
        ))}
      </div>

      {/* Prompts */}
      <div>
        {prompts.map((p, idx) => (
          <div key={idx} className="prompt-card">
            <p>"{p}"</p>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary btn-sm" onClick={() => handleUse(p)}>
                ⚡ Use Prompt
              </button>
              <button className="btn btn-ghost btn-sm"
                onClick={() => { navigator.clipboard.writeText(p); }}>
                📋 Copy
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
