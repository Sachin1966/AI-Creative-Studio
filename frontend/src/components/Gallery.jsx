import JSZip from 'jszip';
import { saveAs } from 'file-saver';

export default function Gallery({ gallery, setGallery }) {
  const downloadSingle = (item, idx) => {
    const a = document.createElement('a');
    a.href = item.image;
    a.download = `gallery_${idx + 1}_seed${item.seed}.png`;
    a.click();
  };

  const exportAll = async () => {
    if (!gallery.length) return;
    const zip = new JSZip();
    gallery.forEach((item, idx) => {
      const b64 = item.image.replace(/^data:image\/\w+;base64,/, '');
      zip.file(`ai_image_${idx + 1}_seed${item.seed}.png`, b64, { base64: true });
    });
    const blob = await zip.generateAsync({ type: 'blob' });
    saveAs(blob, 'ai_creative_studio_gallery.zip');
  };

  const clearGallery = () => {
    if (window.confirm(`Clear all ${gallery.length} images from your gallery?`)) {
      setGallery([]);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>🗂️ My Gallery</h2>
        <p>All images generated in this browser — persisted across sessions via localStorage.</p>
      </div>

      {gallery.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🖼️</div>
          <h3>No images yet</h3>
          <p>Generate images from the Image Generator tab — they'll appear here automatically.</p>
        </div>
      ) : (
        <>
          {/* Action bar */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: 14 }}>
              {gallery.length} image{gallery.length !== 1 ? 's' : ''} saved
            </span>
            <button className="btn btn-secondary btn-sm" onClick={exportAll} style={{ marginLeft: 'auto' }}>
              📦 Export All as ZIP
            </button>
            <button className="btn btn-danger btn-sm" onClick={clearGallery}>
              🗑️ Clear Gallery
            </button>
          </div>

          {/* Grid */}
          <div className="gallery-grid">
            {gallery.map((item, idx) => (
              <div key={idx} className="gallery-item">
                <img src={item.image} alt={`Gallery ${idx + 1}`} />
                <div className="gallery-item-footer">
                  <div className="gallery-item-prompt" title={item.prompt}>
                    {item.prompt}
                  </div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      Seed {item.seed} · {item.timestamp}
                    </span>
                    <button className="btn btn-ghost btn-sm" onClick={() => downloadSingle(item, idx)}>
                      📥
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
