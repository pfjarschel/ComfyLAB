import React, { useEffect } from 'react';

interface AboutModalProps {
  onClose: () => void;
}

export const AboutModal: React.FC<AboutModalProps> = ({ onClose }) => {
  // Close on escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="modal-overlay"
      style={{ zIndex: 10000 }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div 
        className="modal-content glass-panel" 
        style={{
          maxWidth: '500px',
          width: '100%',
        }}
      >
        <div className="modal-header">
          <h3>About ComfyLAB</h3>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body" style={{ padding: '24px 20px', lineHeight: '1.6', textAlign: 'center' }}>
          <h2 style={{ marginBottom: '8px', fontSize: '2rem', color: 'var(--text-color)' }}>
            <a 
              href="https://github.com/pfjarschel/ComfyLAB" 
              target="_blank" 
              rel="noopener noreferrer"
              style={{ color: 'inherit', textDecoration: 'none' }}
              title="Visit ComfyLAB on GitHub"
            >
              ComfyLAB
            </a>
          </h2>
          <div style={{ marginBottom: '20px', fontWeight: 'bold', color: 'var(--text-muted)' }}>
            Version {import.meta.env.VITE_APP_VERSION}
          </div>
          
          <p style={{ marginBottom: '20px', color: 'var(--text-color)', fontSize: '1.05rem' }}>
            <strong>Comfy LAB:</strong> <strong>Comf</strong>ortable <strong>L</strong>ab <strong>A</strong>utomation <strong>B</strong>locks
          </p>

          <p style={{ marginBottom: '20px', color: 'var(--text-color)' }}>
            A flexible, block-based data acquisition and instrument control environment designed to simplify experimental workflows.
          </p>

          <div style={{ textAlign: 'left', background: 'var(--input-bg)', padding: '16px', borderRadius: '8px', marginBottom: '20px', border: '1px solid var(--block-border)' }}>
            <h4 style={{ margin: '0 0 10px 0', color: 'var(--text-color)' }}>Core Features</h4>
            <ul style={{ margin: '0 0 16px 0', paddingLeft: '24px', color: 'var(--text-muted)' }}>
              <li>Intuitive block-based visual scripting interface</li>
              <li>Seamless hardware interfacing via PyVISA</li>
              <li>Real-time data visualization and array processing</li>
              <li>Dynamic execution engine with block clustering</li>
            </ul>

            <h4 style={{ margin: '0 0 10px 0', color: 'var(--text-color)' }}>Powered By</h4>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <span style={{ padding: '4px 8px', background: 'var(--dnd-bg)', borderRadius: '4px', border: '1px solid var(--block-border)' }}>React</span>
              <span style={{ padding: '4px 8px', background: 'var(--dnd-bg)', borderRadius: '4px', border: '1px solid var(--block-border)' }}>XYFlow</span>
              <span style={{ padding: '4px 8px', background: 'var(--dnd-bg)', borderRadius: '4px', border: '1px solid var(--block-border)' }}>FastAPI</span>
              <span style={{ padding: '4px 8px', background: 'var(--dnd-bg)', borderRadius: '4px', border: '1px solid var(--block-border)' }}>PyVISA</span>
              <span style={{ padding: '4px 8px', background: 'var(--dnd-bg)', borderRadius: '4px', border: '1px solid var(--block-border)' }}>Plotly.js</span>
            </div>
          </div>

          <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '20px' }}>
            <p>Copyright &copy; 2026 Paulo Felipe Jarschel</p>
            <p>Released under the GNU General Public License v3.0</p>
          </div>
        </div>
        <div className="modal-footer" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'center' }}>
          <button 
            className="button-secondary" 
            onClick={onClose} 
            style={{ width: '120px' }}
            autoFocus
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
