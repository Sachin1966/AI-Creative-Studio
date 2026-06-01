import { useState, useEffect, useRef } from 'react';

const STYLES = [
  { id: 'none', label: 'None', suffix: '' },
  { id: 'anime', label: 'Anime Style', suffix: ', digital illustration, anime style, highly detailed, vivid colors, masterfully illustrated' },
  { id: 'photorealistic', label: 'Photorealistic', suffix: ', ultra photorealistic, 8k resolution, cinematic lighting, sharp focus' },
  { id: 'cyberpunk', label: 'Cyberpunk', suffix: ', cyberpunk style, neon lights, futuristic city, glowing details' },
  { id: '3d', label: '3D Render', suffix: ', highly detailed 3d render, unreal engine 5 style, volumetric lighting' },
];

export default function VoiceCanvas({ addToGallery }) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [style, setStyle] = useState('none');
  const [imageUrl, setImageUrl] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [supported, setSupported] = useState(true);

  const recognitionRef = useRef(null);

  useEffect(() => {
    // Check for browser support of Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = 'en-US';

    rec.onresult = (e) => {
      let finalTranscript = '';
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        if (e.results[i].isFinal) {
          finalTranscript += e.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        setTranscript((prev) => {
          const combined = prev ? prev + ' ' + finalTranscript : finalTranscript;
          return combined;
        });
      }
    };

    rec.onerror = (e) => {
      if (e.error === 'not-allowed') {
        setError('Microphone permission blocked. Please enable it in browser settings.');
      } else {
        setError(`Speech recognition error: ${e.error}`);
      }
      setIsListening(false);
    };

    rec.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = rec;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  const toggleListening = () => {
    if (!supported) return;
    setError('');

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        setError('Could not start recognition: ' + err.message);
      }
    }
  };

  const handleGenerate = async () => {
    if (!transcript.trim()) return;
    setGenerating(true);
    setError('');
    setImageUrl('');

    try {
      const selectedStyle = STYLES.find((s) => s.id === style);
      const fullPrompt = transcript.trim() + (selectedStyle ? selectedStyle.suffix : '');
      const seed = Math.floor(Math.random() * 1000000);
      
      // We call the free Pollinations Image API directly from the client for maximum responsiveness
      const url = `https://image.pollinations.ai/prompt/${encodeURIComponent(fullPrompt)}?width=1024&height=1024&seed=${seed}&nologo=true&model=flux`;
      
      // Prefetch image to ensure loading state resolves nicely
      const img = new Image();
      img.src = url;
      img.onload = () => {
        setImageUrl(url);
        setGenerating(false);
      };
      img.onerror = () => {
        throw new Error('Image load failed');
      };
    } catch (e) {
      setError('Failed to fetch image from pipeline.');
      setGenerating(false);
    }
  };

  const handleSaveToGallery = async () => {
    if (!imageUrl) return;
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64Data = reader.result.split(',')[1];
        addToGallery({
          image: base64Data,
          seed: Math.floor(Math.random() * 100000),
          prompt: `Voice Canvas: ${transcript}`,
          timestamp: new Date().toISOString(),
        });
        alert('Image saved to Gallery!');
      };
      reader.readAsDataURL(blob);
    } catch (err) {
      alert('Could not save to gallery: ' + err.message);
    }
  };

  return (
    <div className="voice-canvas-container">
      <div className="section-header">
        <h2>🎙️ Live Voice-to-Image Canvas</h2>
        <p>Speak to the canvas and watch your voice prompts materialize into artwork.</p>
      </div>

      {!supported && (
        <div className="warning-box">
          ⚠️ Speech Recognition is not supported by your browser. We recommend using Google Chrome or Microsoft Edge for this feature.
        </div>
      )}

      <div className="voice-canvas-workspace">
        {/* Left Side: Speech Controls */}
        <div className="voice-inputs-card">
          <h3>1. Speak to Describe</h3>

          {/* Mic Button & Waveform */}
          <div className="mic-wrapper">
            <button
              onClick={toggleListening}
              disabled={!supported}
              className={`mic-button ${isListening ? 'listening' : ''}`}
            >
              <span className="mic-icon">{isListening ? '⏹️' : '🎙️'}</span>
            </button>
            <p className="mic-status">
              {isListening ? 'Listening... Speak now' : 'Click to start speaking'}
            </p>

            {isListening && (
              <div className="audio-wave">
                <span className="stroke"></span>
                <span className="stroke"></span>
                <span className="stroke"></span>
                <span className="stroke"></span>
                <span className="stroke"></span>
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Live Transcription</label>
            <textarea
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Your spoken words will appear here. You can also edit this text manually..."
              rows={4}
            />
            {transcript && (
              <button 
                onClick={() => setTranscript('')} 
                className="btn-sm btn-clear-text"
              >
                Clear Text
              </button>
            )}
          </div>

          <div className="form-group">
            <label>Select Canvas Art Style</label>
            <div className="style-grid-selector">
              {STYLES.map((s) => (
                <button
                  key={s.id}
                  className={`style-thumb-btn ${style === s.id ? 'active' : ''}`}
                  onClick={() => setStyle(s.id)}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating || !transcript.trim()}
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '16px' }}
          >
            {generating ? '🎨 Creating Visuals...' : '🎨 Render Image'}
          </button>
        </div>

        {/* Right Side: Visual Canvas Output */}
        <div className="voice-output-canvas">
          {generating && (
            <div className="canvas-loading">
              <div className="canvas-spinner"></div>
              <p>Painting coordinates from voice wave...</p>
            </div>
          )}

          {!generating && !imageUrl && (
            <div className="canvas-empty-state">
              <div className="empty-icon">🎨</div>
              <p>Talk to the microphone and hit "Render Image" to paint your speech canvas.</p>
            </div>
          )}

          {imageUrl && !generating && (
            <div className="canvas-image-wrapper">
              <img src={imageUrl} alt="Speech generated visual" className="rendered-canvas-image" />
              <div className="canvas-actions">
                <button onClick={handleSaveToGallery} className="btn btn-primary">
                  🗂️ Save to Gallery
                </button>
                <a href={imageUrl} download="voice_canvas.png" className="btn btn-secondary">
                  💾 Download Image
                </a>
              </div>
            </div>
          )}

          {error && <div className="error-box" style={{ marginTop: '16px' }}>{error}</div>}
        </div>
      </div>
    </div>
  );
}
