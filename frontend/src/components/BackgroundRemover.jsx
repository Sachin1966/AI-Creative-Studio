import { useState, useRef } from 'react';
import { removeBackground } from '@imgly/background-removal';

export default function BackgroundRemover({ gallery, addToGallery }) {
  const [selectedImg, setSelectedImg] = useState(null); // base64 or object URL
  const [outputImg, setOutputImg] = useState(null); // blob URL
  const [processing, setProcessing] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [percent, setPercent] = useState(0);
  const [error, setError] = useState('');
  
  const fileInputRef = useRef(null);

  // Handle local file upload
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    setOutputImg(null);
    
    const reader = new FileReader();
    reader.onload = () => {
      setSelectedImg(reader.result);
    };
    reader.readAsDataURL(file);
  };

  // Handle selecting an image from the studio gallery
  const handleSelectFromGallery = (item) => {
    setError('');
    setOutputImg(null);
    // Gallery item images are stored as base64 string
    setSelectedImg(`data:image/png;base64,${item.image}`);
  };

  // Process background removal using @imgly/background-removal
  const handleRemoveBackground = async () => {
    if (!selectedImg) return;
    setProcessing(true);
    setError('');
    setProgressMsg('Initializing removal models...');
    setPercent(0);

    try {
      // Set configuration with progress logs
      const config = {
        progress: (key, current, total) => {
          const action = key.split(':')[0];
          const pct = Math.round((current / total) * 100);
          setPercent(pct);
          if (action === 'fetch') {
            setProgressMsg(`Fetching model asset: ${pct}%`);
          } else if (action === 'compute') {
            setProgressMsg(`Analyzing edges & segmenting: ${pct}%`);
          } else {
            setProgressMsg(`Processing background: ${pct}%`);
          }
        }
      };

      const resultBlob = await removeBackground(selectedImg, config);
      const url = URL.createObjectURL(resultBlob);
      setOutputImg(url);
    } catch (e) {
      setError(e.message || 'Background removal failed. Please check file format.');
    } finally {
      setProcessing(false);
      setProgressMsg('');
    }
  };

  // Convert blob URL to base64 for saving back to gallery
  const handleSaveToGallery = async () => {
    if (!outputImg) return;
    try {
      const response = await fetch(outputImg);
      const blob = await response.blob();
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64Data = reader.result.split(',')[1];
        addToGallery({
          image: base64Data,
          seed: 1000000 + Math.floor(Math.random() * 10000),
          prompt: 'Background removed asset',
          timestamp: new Date().toISOString(),
        });
        alert('Saved to Gallery!');
      };
      reader.readAsDataURL(blob);
    } catch (err) {
      alert('Failed to save to gallery: ' + err.message);
    }
  };

  return (
    <div className="bgremover-container">
      <div className="section-header">
        <h2>✂️ Client-Side Background Remover</h2>
        <p>Isolate subjects and create transparent assets instantly. Runs 100% locally in your browser.</p>
      </div>

      <div className="bgremover-workspace">
        {/* Selection / Controls Panel */}
        <div className="bgremover-controls-card">
          <h3>1. Select Source Image</h3>
          
          {/* File Upload Dropzone */}
          <div 
            className="remover-dropzone"
            onClick={() => fileInputRef.current?.click()}
          >
            <span className="dropzone-icon">📤</span>
            <p>Upload a local PNG or JPEG</p>
            <input 
              type="file" 
              ref={fileInputRef} 
              style={{ display: 'none' }} 
              accept="image/*"
              onChange={handleFileChange}
            />
          </div>

          {/* Quick Select from Studio Gallery */}
          {gallery && gallery.length > 0 && (
            <div className="gallery-quickselect-section">
              <h4>Or pick from your generated gallery:</h4>
              <div className="quickselect-grid">
                {gallery.slice(0, 8).map((item, idx) => (
                  <button 
                    key={idx} 
                    className="quickselect-thumb-btn"
                    onClick={() => handleSelectFromGallery(item)}
                  >
                    <img 
                      src={`data:image/png;base64,${item.image}`} 
                      alt="Gallery thumbnail" 
                      className="quickselect-thumb"
                    />
                  </button>
                ))}
              </div>
            </div>
          )}

          <div style={{ marginTop: '20px' }}>
            <button
              onClick={handleRemoveBackground}
              disabled={processing || !selectedImg}
              className="btn btn-primary"
              style={{ width: '100%' }}
            >
              {processing ? '✂️ Processing...' : '✂️ Remove Background'}
            </button>
          </div>
        </div>

        {/* Editing Preview Panel */}
        <div className="bgremover-preview-card">
          {processing && (
            <div className="remover-processing-overlay">
              <div className="remover-loader-ring"></div>
              <h4>{progressMsg}</h4>
              <div className="progress-bar-container">
                <div className="progress-bar-fill" style={{ width: `${percent}%` }}></div>
              </div>
            </div>
          )}

          {!selectedImg && !processing && (
            <div className="remover-empty-preview">
              <div className="empty-icon">🖼️</div>
              <p>Select an image to preview background removal workspace.</p>
            </div>
          )}

          {selectedImg && !processing && (
            <div className="remover-split-view">
              <div className="preview-pane">
                <h5>Source Image</h5>
                <div className="image-frame">
                  <img src={selectedImg} alt="Source" />
                </div>
              </div>

              <div className="preview-pane">
                <h5>Transparent Output</h5>
                <div className="image-frame transparent-checkerboard">
                  {outputImg ? (
                    <img src={outputImg} alt="Transparent background result" />
                  ) : (
                    <div className="waiting-placeholder">
                      <p>Click "Remove Background" to see result.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {error && <div className="error-box" style={{ marginTop: '16px' }}>{error}</div>}

          {outputImg && !processing && (
            <div className="remover-output-actions">
              <a 
                href={outputImg} 
                download="transparent_subject.png"
                className="btn btn-primary"
              >
                💾 Download Transparent PNG
              </a>
              <button 
                onClick={handleSaveToGallery}
                className="btn btn-secondary"
              >
                🗂️ Save back to Gallery
              </button>
              <button
                onClick={() => {
                  setSelectedImg(null);
                  setOutputImg(null);
                }}
                className="btn btn-danger"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
