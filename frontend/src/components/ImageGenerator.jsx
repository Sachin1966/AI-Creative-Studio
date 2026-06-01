import { useState, useEffect } from 'react';
import { generateImage, enhancePrompt } from '../api';

const STYLES = [
  { value: 'none',          label: 'None' },
  { value: 'photorealistic', label: '📸 Ultra-Photorealistic' },
  { value: 'anime',         label: '🎨 Digital Art & Anime' },
  { value: 'cyberpunk',     label: '🌆 Cyberpunk & Sci-Fi' },
  { value: '3d',            label: '👾 3D / Unreal Engine 5' },
];

const RATIOS = ['1:1', '16:9', '9:16', '4:3', '3:4'];

export default function ImageGenerator({ addToGallery, sharedPrompt, setSharedPrompt }) {
  const [provider, setProvider]     = useState('pollinations');
  const [prompt, setPrompt]         = useState('');
  const [negPrompt, setNegPrompt]   = useState('');
  const [style, setStyle]           = useState('photorealistic');
  const [ratio, setRatio]           = useState('1:1');
  const [batchCount, setBatchCount] = useState(1);
  const [seed, setSeed]             = useState(0);
  const [images, setImages]         = useState([]);
  const [loading, setLoading]       = useState(false);
  const [enhancing, setEnhancing]   = useState(false);
  const [error, setError]           = useState('');

  // Pick up shared prompt from PromptLibrary / VisionAI
  useEffect(() => {
    if (sharedPrompt) {
      setPrompt(sharedPrompt);
      setSharedPrompt('');
    }
  }, [sharedPrompt, setSharedPrompt]);

  const handleEnhance = async () => {
    if (!prompt.trim()) return;
    setEnhancing(true);
    try {
      const data = await enhancePrompt(prompt);
      setPrompt(data.enhanced);
    } catch (e) {
      setError(e.message);
    } finally {
      setEnhancing(false);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) { setError('Please enter a prompt.'); return; }
    setError('');
    setLoading(true);
    setImages([]);
    try {
      const data = await generateImage({
        prompt, negative_prompt: negPrompt,
        style, aspect_ratio: ratio,
        batch_count: batchCount, seed, provider,
      });

      const valid = data.images.filter(i => i.image);
      setImages(valid);

      valid.forEach(img => {
        addToGallery({
          image: `data:image/png;base64,${img.image}`,
          seed: img.seed,
          prompt,
          style,
          timestamp: new Date().toLocaleTimeString(),
        });
      });

      if (valid.length === 0) setError('Generation failed — all images returned errors.');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = (b64, seed) => {
    const a = document.createElement('a');
    a.href = `data:image/png;base64,${b64}`;
    a.download = `ai_image_seed${seed}.png`;
    a.click();
  };

  return (
    <div>
      <div className="page-header">
        <h2>🎨 Image Generator</h2>
        <p>Create stunning AI images with Pollinations AI or Hugging Face FLUX</p>
      </div>

      <div className="card">
        {/* Provider */}
        <div className="form-group">
          <label>Provider</label>
          <div className="radio-group">
            <button className={`radio-pill ${provider === 'pollinations' ? 'active' : ''}`}
              onClick={() => setProvider('pollinations')}>
              🚀 Pollinations AI (Free, No Token)
            </button>
            <button className={`radio-pill ${provider === 'huggingface' ? 'active' : ''}`}
              onClick={() => setProvider('huggingface')}>
              🤗 Hugging Face FLUX
            </button>
          </div>
        </div>

        {/* Prompt + Enhance */}
        <div className="form-group">
          <label>Image Prompt</label>
          <div className="input-row" style={{ alignItems: 'flex-start' }}>
            <textarea
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              placeholder="Describe the image you want to generate…"
              style={{ minHeight: '80px' }}
            />
            <button
              className="btn btn-secondary"
              style={{ marginTop: '0', flexShrink: 0, alignSelf: 'flex-start' }}
              onClick={handleEnhance}
              disabled={enhancing || !prompt.trim()}
              title="Enhance prompt with AI"
            >
              {enhancing ? <span className="spinner" /> : '✨'} Enhance
            </button>
          </div>
        </div>

        {/* Negative Prompt */}
        <div className="form-group">
          <label>Negative Prompt <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>
          <input
            type="text"
            value={negPrompt}
            onChange={e => setNegPrompt(e.target.value)}
            placeholder="e.g. blurry, low quality, watermark, text"
          />
        </div>

        {/* Style + Ratio */}
        <div className="grid-2">
          <div className="form-group">
            <label>Style Preset</label>
            <select value={style} onChange={e => setStyle(e.target.value)}>
              {STYLES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Aspect Ratio</label>
            <select value={ratio} onChange={e => setRatio(e.target.value)}>
              {RATIOS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
        </div>

        {/* Batch + Seed */}
        <div className="grid-2">
          <div className="form-group">
            <label>Batch Count: <strong style={{ color: 'var(--accent)' }}>{batchCount}</strong></label>
            <div className="range-row">
              <input type="range" min={1} max={4} value={batchCount}
                onChange={e => setBatchCount(Number(e.target.value))} />
              <span className="range-value">{batchCount}</span>
            </div>
          </div>
          <div className="form-group">
            <label>Seed <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(0 = random)</span></label>
            <input type="number" value={seed} min={0} onChange={e => setSeed(Number(e.target.value))} />
          </div>
        </div>

        {error && <div className="alert alert-error">⚠️ {error}</div>}

        <button className="btn btn-primary btn-full btn-lg" onClick={handleGenerate} disabled={loading}>
          {loading ? <><span className="spinner" /> Generating{batchCount > 1 ? ` ${batchCount} images` : ''}…</> : `⚡ Generate${batchCount > 1 ? ` ${batchCount} Images` : ' Image'}`}
        </button>
      </div>

      {/* Results */}
      {loading && (
        <div className="loading-overlay">
          <span className="spinner spinner-lg" />
          <p>Generating your {batchCount > 1 ? `${batchCount} images` : 'image'}, please wait…<br />
            <small style={{ color: 'var(--text-muted)' }}>Each image takes ~10–15 seconds</small>
          </p>
        </div>
      )}

      {images.length > 0 && (
        <>
          <div className="alert alert-success" style={{ marginTop: 20 }}>
            ✅ Generated {images.length} image{images.length > 1 ? 's' : ''} successfully! Auto-saved to Gallery.
          </div>
          <div className="image-grid">
            {images.map((img, idx) => (
              <div key={idx} className="image-card">
                <img src={`data:image/png;base64,${img.image}`} alt={`Generated ${idx + 1}`} />
                <div className="image-card-footer">
                  <span className="image-meta">Seed: {img.seed}</span>
                  <button className="btn btn-secondary btn-sm" onClick={() => downloadImage(img.image, img.seed)}>
                    📥 Download
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
