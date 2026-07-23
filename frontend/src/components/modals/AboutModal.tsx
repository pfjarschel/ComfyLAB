import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { getBackendUrls } from '../../App';

interface AboutModalProps {
  onClose: () => void;
}

interface ServerInfo {
  port: number;
  token: string;
  local_url: string;
  remote_urls: Array<{
    ip: string;
    fqdn: string;
    display: string;
    raw_url: string;
  }>;
}

export const AboutModal: React.FC<AboutModalProps> = ({ onClose }) => {
  const [serverInfo, setServerInfo] = useState<ServerInfo | null>(null);
  const [showToken, setShowToken] = useState<boolean>(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

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

  // Fetch server access & security info
  useEffect(() => {
    let isMounted = true;
    const fetchServerInfo = async () => {
      try {
        const BACKEND_URL = getBackendUrls().http;
        const res = await axios.get(`${BACKEND_URL}/diagnostics/server_info`);
        if (isMounted && res.data && res.data.status === 'success') {
          setServerInfo(res.data);
        }
      } catch (err) {
        console.error('Failed to fetch server info in AboutModal:', err);
      }
    };
    fetchServerInfo();
    return () => {
      isMounted = false;
    };
  }, []);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

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
          maxWidth: '560px',
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto'
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
          <div style={{ marginBottom: '6px', fontWeight: 'bold', color: 'var(--text-muted)' }}>
            Version {import.meta.env.VITE_APP_VERSION}
          </div>
          <div style={{ marginBottom: '20px', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-muted)', marginRight: '6px' }}>Project Homepage:</span>
            <a 
              href="https://github.com/pfjarschel/ComfyLAB" 
              target="_blank" 
              rel="noopener noreferrer"
              style={{ color: 'var(--accent-color, #a855f7)', textDecoration: 'none', fontWeight: 500 }}
              title="Visit ComfyLAB repository on GitHub"
            >
              https://github.com/pfjarschel/ComfyLAB
            </a>
          </div>
          
          <p style={{ marginBottom: '20px', color: 'var(--text-color)', fontSize: '1.05rem' }}>
            <strong>Comfy LAB:</strong> <strong>Comf</strong>ortable <strong>L</strong>ab <strong>A</strong>utomation <strong>B</strong>locks
          </p>

          <p style={{ marginBottom: '20px', color: 'var(--text-color)' }}>
            A flexible, block-based data acquisition and instrument control environment designed to simplify experimental workflows.
          </p>

          <div style={{ textAlign: 'left', background: 'var(--input-bg)', padding: '16px', borderRadius: '8px', marginBottom: '16px', border: '1px solid var(--block-border)' }}>
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

          {/* Network Access & Security Section */}
          <div style={{
            textAlign: 'left',
            background: 'var(--input-bg)',
            padding: '14px 16px',
            borderRadius: '8px',
            marginBottom: '20px',
            border: '1px solid var(--block-border)',
            fontSize: '0.85rem'
          }}>
            <h4 style={{ margin: '0 0 10px 0', color: 'var(--text-color)', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              🌐 Network & Remote Access
            </h4>

            {serverInfo ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {/* Local Access */}
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', fontSize: '0.78rem' }}>
                    LOCAL BROWSER ACCESS
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--dnd-bg)', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--block-border)' }}>
                    <code style={{ color: 'var(--accent-color, #a855f7)', fontFamily: 'monospace' }}>{serverInfo.local_url}</code>
                    <button
                      onClick={() => copyToClipboard(serverInfo.local_url, 'local')}
                      className="button-secondary"
                      style={{ padding: '2px 8px', fontSize: '0.75rem', height: 'auto' }}
                    >
                      {copiedKey === 'local' ? '✓ Copied' : 'Copy'}
                    </button>
                  </div>
                </div>

                {/* Remote Access */}
                {serverInfo.remote_urls && serverInfo.remote_urls.length > 0 && (
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', fontSize: '0.78rem' }}>
                      REMOTE ACCESS
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {serverInfo.remote_urls.map((item, idx) => (
                        <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--dnd-bg)', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--block-border)' }}>
                          <span style={{ fontFamily: 'monospace', color: 'var(--text-color)', fontSize: '0.78rem', wordBreak: 'break-all' }}>
                            {item.display}
                          </span>
                          <button
                            onClick={() => copyToClipboard(item.raw_url, `remote-${idx}`)}
                            className="button-secondary"
                            style={{ padding: '2px 8px', fontSize: '0.75rem', height: 'auto', flexShrink: 0, marginLeft: '8px' }}
                          >
                            {copiedKey === `remote-${idx}` ? '✓ Copied' : 'Copy'}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Remote Access Token */}
                {serverInfo.token && (
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px', fontSize: '0.78rem' }}>
                      SESSION REMOTE ACCESS TOKEN
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--dnd-bg)', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--block-border)' }}>
                      <code style={{ color: 'var(--text-color)', fontFamily: 'monospace', fontWeight: 'bold' }}>
                        {showToken ? serverInfo.token : '••••••••••••'}
                      </code>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          onClick={() => setShowToken(!showToken)}
                          className="button-secondary"
                          style={{ padding: '2px 8px', fontSize: '0.75rem', height: 'auto' }}
                          title={showToken ? "Hide Access Token" : "Show Access Token"}
                        >
                          {showToken ? '👁 Hide' : '👁 Show'}
                        </button>
                        <button
                          onClick={() => copyToClipboard(serverInfo.token, 'token')}
                          className="button-secondary"
                          style={{ padding: '2px 8px', fontSize: '0.75rem', height: 'auto' }}
                        >
                          {copiedKey === 'token' ? '✓ Copied' : 'Copy'}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontStyle: 'italic' }}>
                Loading network access details...
              </div>
            )}
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
