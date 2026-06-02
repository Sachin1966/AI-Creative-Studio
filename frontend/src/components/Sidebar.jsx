const NAV_ITEMS = [
  { id: 'image',       icon: '🎨', label: 'Image Generator' },
  { id: 'writer',      icon: '✍️', label: 'AI Scriptwriter' },
  { id: 'voicecanvas', icon: '🎙️', label: 'Voice Canvas' },
  { id: 'bgremover',   icon: '✂️', label: 'Background Remover' },
  { id: 'avatar',      icon: '🎭', label: 'Talking Avatar' },

  { id: 'audio',       icon: '🔊', label: 'Audio Suite' },
  { id: 'vision',      icon: '🖼️', label: 'Vision AI' },
  { id: 'library',     icon: '📚', label: 'Prompt Library' },
  { id: 'gallery',     icon: '🗂️', label: 'My Gallery' },
];

export default function Sidebar({ activeTab, setActiveTab, galleryCount }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">✨</div>
        <div className="sidebar-logo-text">
          <h1>AI Studio</h1>
          <p>Creative Suite v2.0</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ id, icon, label }) => (
          <button
            key={id}
            className={`nav-item ${activeTab === id ? 'active' : ''}`}
            onClick={() => setActiveTab(id)}
          >
            <span className="nav-icon">{icon}</span>
            <span>{label}</span>
            {id === 'gallery' && galleryCount > 0 && (
              <span className="nav-badge">{galleryCount}</span>
            )}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-section-title">Stack</div>
        <div style={{ padding: '0 14px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {[
            { label: 'Backend', value: 'FastAPI', color: 'tag-green' },
            { label: 'Frontend', value: 'React + Vite', color: 'tag-blue' },
            { label: 'Images', value: 'Pollinations AI', color: 'tag-purple' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>{label}</span>
              <span className={`tag ${color}`}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
