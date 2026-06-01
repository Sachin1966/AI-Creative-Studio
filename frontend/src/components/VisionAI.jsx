import { useState, useRef } from 'react';
import { captionImage } from '../api';

export default function VisionAI({ goToImageTab }) {
  const [file, setFile]       = useState(null);
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [caption, setCaption] = useState('');
  const [error, setError]     = useState('');
  const [copied, setCopied]   = useState(false);
  const inputRef = useRef(null);

  const handleFile = (f) => {
    if (!f) return;
    setFile(f);
    setCaption('');
    setError('');
    const reader = new FileReader();
    reader.onload = e => setPreview(e.target.result);
    reader.readAsDataURL(f);
  };

  const handleCaption = async () => {
    if (!file) return;
    setLoading(true); setError(''); setCaption('');
    try {
      const data = await captionImage(file);
      setCaption(data.caption.charAt(0).toUpperCase() + data.caption.slice(1));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(caption);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <div className="page-header">
        <h2>🖼️ Vision AI</h2>
        <p>
          Upload any image and AI will describe it as a detailed generation prompt. Powered by{' '}
          <strong style={{ color: 'var(--accent)' }}>Pollinations Vision</strong> — free, no token needed!
        </p>
      </div>

      <div className="alert alert-info" style={{ marginBottom: 20 }}>
        ✨ <strong>Pollinations AI Vision</strong> — Works on Jio and all networks. No API key required.
      </div>

      <div className="card">
        <div
          className="drop-zone"
          onClick={() => inputRef.current?.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); handleFile(e.dataTransfer.files[0]); }}
        >
          {preview ? (
            <img src={preview} alt="Preview" style={{ maxHeight: 300, maxWidth: '100%', borderRadius: 8, marginBottom: 12 }} />
          ) : (
            <>
              <div className="drop-zone-icon">🔍</div>
              <p>Drag &amp; drop an image, or <span>click to browse</span></p>
              <p style={{ fontSize: 12, marginTop: 6, color: 'var(--text-muted)' }}>PNG, JPG, JPEG supported</p>
            </>
          )}
        </div>

        <input
          ref={inputRef}
          type="file"
          accept=".png,.jpg,.jpeg"
          style={{ display: 'none' }}
          onChange={e => handleFile(e.target.files[0])}
        />

        {preview && (
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8, marginBottom: 16 }}>
            📁 {file?.name} —{' '}
            <button className="btn btn-ghost btn-sm" onClick={() => { setFile(null); setPreview(''); setCaption(''); }}>
              Change image
            </button>
          </p>
        )}

        {error && <div className="alert alert-error">⚠️ {error}</div>}

        <button className="btn btn-primary btn-full" onClick={handleCaption} disabled={loading || !file}>
          {loading ? <><span className="spinner" /> Analyzing image with Pollinations Vision…</> : '🔍 Generate AI Caption'}
        </button>
      </div>

      {caption && (
        <div className="card" style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600 }}>📝 AI Caption</h3>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-ghost btn-sm" onClick={handleCopy}>
                {copied ? '✅ Copied!' : '📋 Copy'}
              </button>
            </div>
          </div>
          <div className="alert alert-success" style={{ marginBottom: 16 }}>
            <span style={{ fontSize: 14, lineHeight: 1.6 }}>"{caption}"</span>
          </div>
          <button className="btn btn-primary btn-full" onClick={() => goToImageTab(caption)}>
            ✨ Use as Image Prompt → Go Generate
          </button>
        </div>
      )}
    </div>
  );
}
