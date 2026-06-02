import { useState, useRef } from 'react';
import { generateTalkingAvatar } from '../api';

export default function TalkingAvatar({ gallery }) {
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [audioFile, setAudioFile] = useState(null);
  const [audioPreview, setAudioPreview] = useState('');
  const [stillMode, setStillMode] = useState(true);
  const [useEnhancer, setUseEnhancer] = useState(false);
  const [preprocess, setPreprocess] = useState('crop');
  const [pipelineMode, setPipelineMode] = useState('colab'); // 'hf' or 'colab'
  const [customEndpoint, setCustomEndpoint] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [videoB64, setVideoB64] = useState('');

  const imageInputRef = useRef(null);
  const audioInputRef = useRef(null);

  // File handlers
  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setError('');
    setVideoB64('');
    const reader = new FileReader();
    reader.onload = () => setImagePreview(reader.result);
    reader.readAsDataURL(file);
  };

  const handleSelectFromGallery = async (item) => {
    setError('');
    setVideoB64('');
    try {
      // Gallery item images are base64 string
      const base64Data = item.image.startsWith('data:') ? item.image : `data:image/png;base64,${item.image}`;
      setImagePreview(base64Data);

      // Convert base64 back to a File object to send to the backend API
      const res = await fetch(base64Data);
      const blob = await res.blob();
      const file = new File([blob], 'gallery_image.png', { type: 'image/png' });
      setImageFile(file);
    } catch (err) {
      setError('Could not import photo from gallery: ' + err.message);
    }
  };

  const handleAudioChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAudioFile(file);
    setError('');
    setVideoB64('');
    setAudioPreview(URL.createObjectURL(file));
  };

  const handleGenerate = async () => {
    if (!imageFile) { setError('Please select a source portrait image.'); return; }
    if (!audioFile) { setError('Please select a driving audio file.'); return; }
    if (pipelineMode === 'colab' && !customEndpoint.trim()) {
      setError('Please paste your Google Colab Gradio endpoint URL (e.g. https://xxxx.gradio.live).');
      return;
    }

    setGenerating(true);
    setError('');
    setVideoB64('');

    try {
      const endpoint = pipelineMode === 'hf' ? '' : customEndpoint.trim();
      const response = await generateTalkingAvatar(
        imageFile,
        audioFile,
        stillMode,
        useEnhancer,
        preprocess,
        endpoint
      );

      if (response && response.video) {
        setVideoB64(response.video);
      } else {
        throw new Error('Video generation resolved with missing output binary.');
      }
    } catch (err) {
      setError(err.message || 'Failed to animate avatar.');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!videoB64) return;
    const link = document.createElement('a');
    link.href = `data:video/mp4;base64,${videoB64}`;
    link.download = `talking_avatar_${Date.now()}.mp4`;
    link.click();
  };

  return (
    <div className="talking-avatar-container">
      <div className="section-header">
        <h2>🎭 AI Talking Avatar</h2>
        <p>Animate portrait photos into speaking videos powered by SadTalker. Connect your own Colab GPU tunnel to bypass network blocks.</p>
      </div>

      <div className="avatar-workspace">
        {/* Left Input Pane */}
        <div className="avatar-inputs-card">
          <h3>1. Setup Assets & Route</h3>

          {/* Pipeline Switch */}
          <div className="form-group">
            <label>Pipeline Endpoint Routing</label>
            <div className="radio-group" style={{ marginBottom: '12px' }}>
              <button 
                className={`radio-pill ${pipelineMode === 'colab' ? 'active' : ''}`} 
                onClick={() => setPipelineMode('colab')}
              >
                ⚡ Google Colab Tunnel (Recommended)
              </button>
              <button 
                className={`radio-pill ${pipelineMode === 'hf' ? 'active' : ''}`} 
                onClick={() => setPipelineMode('hf')}
              >
                ☁️ Public HF Space (May block DNS)
              </button>
            </div>

            {pipelineMode === 'colab' && (
              <div className="colab-endpoint-box">
                <input 
                  type="text" 
                  value={customEndpoint}
                  onChange={(e) => setCustomEndpoint(e.target.value)}
                  placeholder="e.g. https://da312e4f0a2d21a2.gradio.live" 
                  className="endpoint-input"
                />
                <p className="help-text">
                  Run a SadTalker colab, copy the <strong>gradio.live</strong> URL, and paste it here. Runs 10x faster with Colab GPUs!
                </p>
              </div>
            )}
          </div>

          {/* Image Upload Area */}
          <div className="form-group">
            <label>Select Portrait Photo</label>
            <div 
              className="drop-zone" 
              style={{ minHeight: '120px' }}
              onClick={() => imageInputRef.current.click()}
            >
              {imagePreview ? (
                <img src={imagePreview} alt="Portrait preview" className="portrait-preview-thumbnail" />
              ) : (
                <>
                  <span className="drop-zone-icon">👤</span>
                  <p>Upload portrait photo or click to browse</p>
                </>
              )}
            </div>
            <input 
              type="file" 
              ref={imageInputRef} 
              accept="image/*" 
              style={{ display: 'none' }} 
              onChange={handleImageChange} 
            />

            {/* Quick select from gallery */}
            {gallery && gallery.length > 0 && (
              <div className="gallery-quickselect-section" style={{ marginTop: '10px' }}>
                <span className="sub-label">Or choose from Studio Gallery:</span>
                <div className="quickselect-grid" style={{ marginTop: '6px' }}>
                  {gallery.slice(0, 8).map((item, idx) => (
                    <button 
                      key={idx} 
                      className="quickselect-thumb-btn"
                      onClick={() => handleSelectFromGallery(item)}
                    >
                      <img 
                        src={item.image.startsWith('data:') ? item.image : `data:image/png;base64,${item.image}`} 
                        alt="Gallery thumb" 
                        className="quickselect-thumb" 
                      />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Audio Upload Area */}
          <div className="form-group">
            <label>Upload Speech/Voice Audio</label>
            <div 
              className="drop-zone" 
              style={{ minHeight: '90px' }}
              onClick={() => audioInputRef.current.click()}
            >
              {audioFile ? (
                <p className="audio-loaded-msg">🔊 {audioFile.name} ({(audioFile.size / 1024).toFixed(1)} KB)</p>
              ) : (
                <>
                  <span className="drop-zone-icon">🎙️</span>
                  <p>Upload MP3 or WAV audio</p>
                </>
              )}
            </div>
            <input 
              type="file" 
              ref={audioInputRef} 
              accept="audio/*" 
              style={{ display: 'none' }} 
              onChange={handleAudioChange} 
            />
            {audioPreview && (
              <audio src={audioPreview} controls style={{ width: '100%', marginTop: '8px' }} />
            )}
          </div>

          {/* Additional ML config settings */}
          <div className="form-group settings-group-box">
            <label>SadTalker Parameters</label>
            
            <div className="flex-row-checkboxes">
              <label className="checkbox-container">
                <input 
                  type="checkbox" 
                  checked={stillMode} 
                  onChange={(e) => setStillMode(e.target.checked)} 
                />
                <span className="checkmark"></span>
                Still Mode (represses head motion)
              </label>

              <label className="checkbox-container" style={{ marginTop: '8px' }}>
                <input 
                  type="checkbox" 
                  checked={useEnhancer} 
                  onChange={(e) => setUseEnhancer(e.target.checked)} 
                />
                <span className="checkmark"></span>
                GFPGAN Enhancer (high-resolution face)
              </label>
            </div>

            <div style={{ marginTop: '12px' }}>
              <label className="sub-label">Preprocessing Mode</label>
              <select value={preprocess} onChange={(e) => setPreprocess(e.target.value)} className="select-input">
                <option value="crop">Crop (Face only - Recommended)</option>
                <option value="resize">Resize (Stretch to fit)</option>
                <option value="full">Full (Entire frame)</option>
              </select>
            </div>
          </div>

          <button 
            onClick={handleGenerate} 
            disabled={generating || !imageFile || !audioFile} 
            className="btn btn-primary btn-full"
            style={{ marginTop: '12px' }}
          >
            {generating ? (
              <>
                <span className="spinner" /> Generating Speaking Face…
              </>
            ) : (
              '🎭 Generate Talking Avatar'
            )}
          </button>
        </div>

        {/* Right Output Card */}
        <div className="avatar-preview-card">
          {generating && (
            <div className="avatar-loading-overlay">
              <div className="avatar-loader-ring"></div>
              <h4>Rendering Lip Synchronization...</h4>
              <p className="help-text">This will take ~30-60 seconds on a Colab GPU, or slightly longer on public CPUs.</p>
            </div>
          )}

          {!generating && !videoB64 && !error && (
            <div className="avatar-empty-preview">
              <div className="empty-icon">🎭</div>
              <p>Configure inputs, set your pipeline URL, and click "Generate" to visualize your talking photo.</p>
            </div>
          )}

          {error && (
            <div className="error-box" style={{ width: '100%' }}>
              <h4>⚠️ Generation Failed</h4>
              <p>{error}</p>
              {pipelineMode === 'colab' && (
                <p style={{ fontSize: '11px', marginTop: '6px', color: 'var(--text-muted)' }}>
                  Verify that your Colab cell is actively running and you've pasted the correct public `.gradio.live` URL.
                </p>
              )}
            </div>
          )}

          {videoB64 && !generating && (
            <div className="avatar-video-wrapper">
              <h5>Output Synchronized Video</h5>
              <div className="video-frame">
                <video 
                  src={`data:video/mp4;base64,${videoB64}`} 
                  controls 
                  autoPlay 
                  loop 
                  className="rendered-avatar-video"
                />
              </div>
              <div className="avatar-output-actions">
                <button onClick={handleDownload} className="btn btn-primary">
                  💾 Download Video (MP4)
                </button>
                <button 
                  onClick={() => {
                    setImageFile(null);
                    setImagePreview('');
                    setAudioFile(null);
                    setAudioPreview('');
                    setVideoB64('');
                  }}
                  className="btn btn-danger"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
