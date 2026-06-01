import { useState } from 'react';
import { generateText } from '../api';

const GENRES = ['Sci-Fi', 'Fantasy', 'Noir', 'Comedy', 'Thriller', 'Drama', 'Adventure'];
const TONES = ['Epic', 'Dramatic', 'Mysterious', 'Cyberpunk', 'Whimsical', 'Dark', 'Futuristic'];

export default function CreativeWriter({ goToImageTab }) {
  const [prompt, setPrompt] = useState('');
  const [genre, setGenre] = useState('Sci-Fi');
  const [tone, setTone] = useState('Epic');
  const [wordCount, setWordCount] = useState(150);
  const [loading, setLoading] = useState(false);
  const [script, setScript] = useState('');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError('');
    setScript('');
    setCopied(false);

    try {
      const response = await generateText({
        prompt: prompt.trim(),
        genre,
        tone,
        word_count: wordCount,
      });
      setScript(response.text);
    } catch (e) {
      setError(e.message || 'Failed to generate creative script.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(script);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="creative-writer-container">
      <div className="section-header">
        <h2>✍️ AI Creative Scriptwriter</h2>
        <p>Brainstorm scripts, stories, or character dialogues instantly using open LLMs.</p>
      </div>

      <div className="writer-workspace">
        {/* Left Inputs Pane */}
        <div className="writer-inputs-card">
          <div className="form-group">
            <label>What is your story concept / character hook?</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. A cybernetic detective uncovers a glitch in the city's virtual sky grid..."
              rows={4}
            />
          </div>

          <div className="form-group">
            <label>Genre</label>
            <div className="tag-selector">
              {GENRES.map((g) => (
                <button
                  key={g}
                  className={`tag-btn ${genre === g ? 'active' : ''}`}
                  onClick={() => setGenre(g)}
                >
                  {g}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>Tone</label>
            <div className="tag-selector">
              {TONES.map((t) => (
                <button
                  key={t}
                  className={`tag-btn ${tone === t ? 'active' : ''}`}
                  onClick={() => setTone(t)}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label>Target Word Count</label>
              <span className="slider-value">{wordCount} words</span>
            </div>
            <input
              type="range"
              min={50}
              max={400}
              step={25}
              value={wordCount}
              onChange={(e) => setWordCount(Number(e.target.value))}
              className="slider"
            />
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading || !prompt.trim()}
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '12px' }}
          >
            {loading ? '✍️ Writing Script...' : '✍️ Write Script'}
          </button>
        </div>

        {/* Right Output Pane */}
        <div className="writer-output-card">
          {loading && (
            <div className="writer-loading-state">
              <div className="writer-spinner"></div>
              <p className="typing-placeholder">Weaving characters and plotting narrative arcs...</p>
            </div>
          )}

          {!loading && !script && !error && (
            <div className="writer-empty-state">
              <div className="empty-icon">📝</div>
              <p>Configure options and click "Write Script" to view the generated narrative.</p>
            </div>
          )}

          {error && <div className="error-box">{error}</div>}

          {script && !loading && (
            <div className="writer-content-wrapper">
              <div className="writer-actions-bar">
                <button onClick={handleCopy} className="btn-sm">
                  {copied ? '✅ Copied!' : '📋 Copy Script'}
                </button>
                <button
                  onClick={() => goToImageTab(script.slice(0, 300))}
                  className="btn-sm btn-primary-sm"
                >
                  🎨 Generate Image from this
                </button>
              </div>
              <div className="writer-text-area">
                {script.split('\n').map((para, i) => (
                  <p key={i} className="writer-paragraph">{para}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
