import { useState, useRef, useCallback } from 'react';
import { generateTTS, transcribeAudio } from '../api';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'ta', label: 'Tamil (தமிழ்)' },
  { code: 'hi', label: 'Hindi (हिन्दी)' },
  { code: 'es', label: 'Spanish (Español)' },
  { code: 'fr', label: 'French (Français)' },
  { code: 'de', label: 'German (Deutsch)' },
  { code: 'ja', label: 'Japanese (日本語)' },
  { code: 'ko', label: 'Korean (한국어)' },
];

const BG_LOOPS = ['None', 'Calm Zen Pad ✨', 'Deep Tech Pulse 🥁', 'Cosmic Drone 🚀'];
const VOICES   = ['nova', 'alloy', 'echo', 'fable', 'onyx', 'shimmer'];

// ─── Web Audio Mixer ──────────────────────────────────────────
function useMixer() {
  const ctxRef      = useRef(null);
  const nodesRef    = useRef([]);
  const bufferRef   = useRef(null);
  const animRef     = useRef(null);
  const canvasRef   = useRef(null);

  const stop = useCallback(() => {
    nodesRef.current.forEach(n => { try { n.stop(0); } catch {} });
    nodesRef.current = [];
    if (animRef.current) { cancelAnimationFrame(animRef.current); animRef.current = null; }
    const c = canvasRef.current;
    if (c) c.getContext('2d').clearRect(0, 0, c.width, c.height);
  }, []);

  const init = useCallback(async (b64Audio) => {
    if (!ctxRef.current) ctxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    const ctx = ctxRef.current;
    const bin = atob(b64Audio);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    bufferRef.current = await ctx.decodeAudioData(bytes.buffer);
  }, []);

  const addBg = useCallback((ctx, duration, loopName, vol) => {
    if (loopName === 'None') return [];
    const gain = ctx.createGain();
    gain.gain.value = vol;
    gain.connect(ctx.destination);
    const nodes = [];

    if (loopName.includes('Calm')) {
      [130.81, 164.81, 196, 246.94].forEach(f => {
        const o = ctx.createOscillator(); o.type = 'sine'; o.frequency.value = f;
        o.connect(gain); nodes.push(o);
      });
    } else if (loopName.includes('Tech')) {
      const o = ctx.createOscillator(); o.type = 'triangle'; o.frequency.value = 82.41;
      const pg = ctx.createGain(); pg.gain.value = vol;
      const lfo = ctx.createOscillator(); lfo.type = 'sine'; lfo.frequency.value = 1.5;
      const lg = ctx.createGain(); lg.gain.value = vol * 0.8;
      lfo.connect(lg); lg.connect(pg.gain); o.connect(pg); pg.connect(ctx.destination);
      nodes.push(o, lfo);
    } else if (loopName.includes('Cosmic')) {
      const o1 = ctx.createOscillator(); o1.type = 'sine'; o1.frequency.value = 65.41;
      const o2 = ctx.createOscillator(); o2.type = 'sawtooth'; o2.frequency.value = 65.7;
      const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.Q.value = 5;
      lp.frequency.setValueAtTime(200, 0);
      lp.frequency.exponentialRampToValueAtTime(800, duration / 2);
      lp.frequency.exponentialRampToValueAtTime(200, duration);
      o1.connect(lp); o2.connect(lp); lp.connect(gain);
      nodes.push(o1, o2);
    }
    return nodes;
  }, []);

  const visualize = useCallback((analyser) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.width  = canvas.clientWidth;
    canvas.height = canvas.clientHeight;
    const ctx2d = canvas.getContext('2d');
    const data  = new Uint8Array(analyser.frequencyBinCount);
    const draw  = () => {
      animRef.current = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(data);
      ctx2d.fillStyle = '#030712';
      ctx2d.fillRect(0, 0, canvas.width, canvas.height);
      const bw = (canvas.width / data.length) * 1.5;
      let x = 0;
      data.forEach(v => {
        const h = v / 2;
        const g = ctx2d.createLinearGradient(0, canvas.height, 0, 0);
        g.addColorStop(0, '#047857'); g.addColorStop(1, '#10b981');
        ctx2d.fillStyle = g;
        ctx2d.fillRect(x, canvas.height - h, bw - 1, h);
        x += bw;
      });
    };
    draw();
  }, []);

  const play = useCallback(async (b64Audio, speed, bgLoop, bgVol) => {
    stop();
    const ctx = ctxRef.current;
    if (!bufferRef.current) await init(b64Audio);
    const src = ctx.createBufferSource();
    src.buffer = bufferRef.current;
    src.playbackRate.value = speed;
    const analyser = ctx.createAnalyser(); analyser.fftSize = 64;
    src.connect(analyser); analyser.connect(ctx.destination);
    visualize(analyser);
    const dur = bufferRef.current.duration / speed;
    const synths = addBg(ctx, dur, bgLoop, bgVol / 100);
    nodesRef.current = [src, ...synths];
    src.start(0); synths.forEach(s => s.start(0));
    src.onended = stop;
    return dur;
  }, [stop, init, addBg, visualize]);

  return { canvasRef, play, stop };
}

// ─── Synthesis Tab ────────────────────────────────────────────
function SynthesisTab() {
  const [mode, setMode]       = useState('google');
  const [text, setText]       = useState('Hello! Welcome to AI Creative Studio.');
  const [lang, setLang]       = useState('en');
  const [voice, setVoice]     = useState('nova');
  const [speed, setSpeed]     = useState(1.0);
  const [bgLoop, setBgLoop]   = useState('None');
  const [bgVol, setBgVol]     = useState(15);
  const [apiKey, setApiKey]   = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus]   = useState('READY');
  const [audioB64, setAudioB64] = useState('');
  const [translated, setTranslated] = useState('');
  const [error, setError]     = useState('');

  const { canvasRef, play, stop } = useMixer();

  const handleRender = async () => {
    if (!text.trim()) { setError('Please enter some text.'); return; }
    setError(''); setLoading(true); setStatus('LOADING');
    try {
      const data = await generateTTS({ text, mode, language: lang, voice, api_key: apiKey });
      setAudioB64(data.audio);
      if (data.translated_text !== text) setTranslated(data.translated_text);
      setStatus('READY');
    } catch (e) {
      setError(e.message); setStatus('READY');
    } finally {
      setLoading(false);
    }
  };

  const handlePlay = async () => {
    if (!audioB64) return;
    setStatus('PLAYING');
    try { await play(audioB64, speed, bgLoop, bgVol); }
    catch (e) { setError(e.message); }
    finally { setStatus('READY'); }
  };

  const handleDownload = () => {
    if (!audioB64) return;
    const a = document.createElement('a');
    a.href = `data:audio/mp3;base64,${audioB64}`;
    a.download = 'ai_speech.mp3';
    a.click();
  };

  return (
    <div>
      {/* Mode */}
      <div className="form-group">
        <label>Audio Provider</label>
        <div className="radio-group">
          <button className={`radio-pill ${mode === 'google' ? 'active' : ''}`} onClick={() => setMode('google')}>
            🌐 Google TTS (Free, Jio Compatible)
          </button>
          <button className={`radio-pill ${mode === 'pollinations' ? 'active' : ''}`} onClick={() => setMode('pollinations')}>
            🎙️ Pollinations AI
          </button>
        </div>
      </div>

      {mode === 'pollinations' && (
        <div className="form-group">
          <label>Pollinations API Key</label>
          <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)}
            placeholder="Enter your Pollinations API key…" />
        </div>
      )}

      {/* Text */}
      <div className="form-group">
        <label>Text to Speak</label>
        <textarea value={text} onChange={e => setText(e.target.value)} rows={4}
          placeholder="Enter the text you want to convert to speech…" />
      </div>

      {/* Language / Voice */}
      <div className="grid-2">
        {mode === 'google' ? (
          <div className="form-group">
            <label>Target Language</label>
            <select value={lang} onChange={e => setLang(e.target.value)}>
              {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
          </div>
        ) : (
          <div className="form-group">
            <label>Voice</label>
            <select value={voice} onChange={e => setVoice(e.target.value)}>
              {VOICES.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
        )}
        <div className="form-group">
          <label>Playback Speed: <strong style={{ color: 'var(--accent)' }}>{speed.toFixed(1)}x</strong></label>
          <div className="range-row">
            <input type="range" min={0.5} max={2} step={0.1} value={speed}
              onChange={e => setSpeed(parseFloat(e.target.value))} />
            <span className="range-value">{speed.toFixed(1)}x</span>
          </div>
        </div>
      </div>

      {/* Background Mixer */}
      <div className="grid-2">
        <div className="form-group">
          <label>Background Soundtrack</label>
          <select value={bgLoop} onChange={e => setBgLoop(e.target.value)}>
            {BG_LOOPS.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>Music Volume: <strong style={{ color: 'var(--accent)' }}>{bgVol}%</strong></label>
          <div className="range-row">
            <input type="range" min={0} max={50} step={5} value={bgVol}
              onChange={e => setBgVol(Number(e.target.value))} />
            <span className="range-value">{bgVol}%</span>
          </div>
        </div>
      </div>

      {error && <div className="alert alert-error">⚠️ {error}</div>}
      {translated && (
        <div className="alert alert-info">📝 Translated: <em>{translated}</em></div>
      )}

      <button className="btn btn-primary btn-full" onClick={handleRender} disabled={loading}>
        {loading ? <><span className="spinner" /> Rendering audio…</> : '🎙️ Render Audio'}
      </button>

      {/* Mixer Panel */}
      {audioB64 && (
        <div className="mixer-panel">
          <div className="mixer-header">
            <span className="mixer-label">🎧 Active Mixer Console</span>
            <span className={`mixer-status ${status === 'PLAYING' ? 'playing' : ''}`}>{status}</span>
          </div>
          <canvas id="visualizer" ref={canvasRef} />
          <div className="mixer-controls">
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={handlePlay} disabled={status === 'PLAYING'}>
              ▶ Play Mix
            </button>
            <button className="btn btn-danger" onClick={stop}>⏹ Stop</button>
            <button className="btn btn-secondary" onClick={handleDownload}>📥 Download MP3</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Transcription Tab ────────────────────────────────────────
function TranscriptionTab() {
  const [file, setFile]           = useState(null);
  const [loading, setLoading]     = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError]         = useState('');

  const handleTranscribe = async () => {
    if (!file) { setError('Please upload a WAV file first.'); return; }
    setError(''); setLoading(true); setTranscript('');
    try {
      const data = await transcribeAudio(file);
      setTranscript(data.transcription);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadTranscript = () => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([transcript], { type: 'text/plain' }));
    a.download = 'transcript.txt';
    a.click();
  };

  return (
    <div>
      <div className="form-group">
        <label>Upload WAV Audio File</label>
        <div
          className="drop-zone"
          onClick={() => document.getElementById('wav-input').click()}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); setFile(e.dataTransfer.files[0]); }}
        >
          <div className="drop-zone-icon">🎤</div>
          {file ? (
            <p>✅ <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)</p>
          ) : (
            <p>Drag & drop a WAV file, or <span>click to browse</span></p>
          )}
        </div>
        <input id="wav-input" type="file" accept=".wav" style={{ display: 'none' }}
          onChange={e => setFile(e.target.files[0])} />
      </div>

      {error && <div className="alert alert-error">⚠️ {error}</div>}

      <button className="btn btn-primary btn-full" onClick={handleTranscribe} disabled={loading || !file}>
        {loading ? <><span className="spinner" /> Transcribing…</> : '📝 Transcribe Audio'}
      </button>

      {transcript && (
        <div style={{ marginTop: 20 }}>
          <div className="alert alert-success">✅ Transcription complete!</div>
          <div className="form-group">
            <label>Transcription Result</label>
            <textarea value={transcript} readOnly rows={6} style={{ resize: 'vertical' }} />
          </div>
          <button className="btn btn-secondary" onClick={downloadTranscript}>📥 Download as .txt</button>
        </div>
      )}
    </div>
  );
}

// ─── Main AudioSuite ──────────────────────────────────────────
export default function AudioSuite() {
  const [tab, setTab] = useState('synthesis');
  return (
    <div>
      <div className="page-header">
        <h2>🔊 Audio Suite</h2>
        <p>Convert text to speech with multilingual support, a real-time audio mixer, and speech transcription</p>
      </div>

      <div className="tab-bar">
        <button className={`tab-btn ${tab === 'synthesis' ? 'active' : ''}`} onClick={() => setTab('synthesis')}>
          🎙️ Speech Synthesis & Mixer
        </button>
        <button className={`tab-btn ${tab === 'transcription' ? 'active' : ''}`} onClick={() => setTab('transcription')}>
          📝 Speech-to-Text
        </button>
      </div>

      <div className="card">
        {tab === 'synthesis'    && <SynthesisTab />}
        {tab === 'transcription' && <TranscriptionTab />}
      </div>
    </div>
  );
}
