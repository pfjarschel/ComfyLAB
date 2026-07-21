/*
 * Copyright (C) 2026 Paulo Felipe Jarschel
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 */


interface GlobalSettingsProps {
  isOpen: boolean;
  settings: {
    custom_node_dirs: string[];
    script_timeout: number;
    visa_backend: string;
    last_workspace: string;
    enable_lua_scripting: boolean;
    enable_julia_scripting: boolean;
    enable_js_scripting: boolean;
    enable_rust_scripting: boolean;
    enable_r_scripting: boolean;
    enable_octave_scripting: boolean;
    enable_wolfram_scripting: boolean;
    external_python_path: string;
    creator_identity: string;
    trusted_origins: string[];
    custom_users: Record<string, string>;
  };
  setSettings: (settings: any) => void;
  newDirInput: string;
  setNewDirInput: (value: string) => void;
  settingsTab: 'general' | 'diagnostics';
  setSettingsTab: (tab: 'general' | 'diagnostics') => void;
  diagnosticsData: any;
  loadingDiagnostics: boolean;
  fetchDiagnostics: () => void;
  onSave: () => void;
  onClose: () => void;
}

export const GlobalSettingsModal = ({
  isOpen,
  settings,
  setSettings,
  newDirInput,
  setNewDirInput,
  settingsTab,
  setSettingsTab,
  diagnosticsData,
  loadingDiagnostics,
  fetchDiagnostics,
  onSave,
  onClose,
}: GlobalSettingsProps) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" style={{ zIndex: 1000 }} onClick={onClose}>
      <div className="modal-content glass-panel" style={{ width: '500px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>⚙️</span> Global Settings
          </h3>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px' }}>
          
          {/* --- TAB HEADERS --- */}
          <div className="settings-tabs-row" style={{ display: 'flex', borderBottom: '1px solid var(--block-border)', marginBottom: '8px', gap: '8px' }}>
            <button 
              className={`settings-tab-btn ${settingsTab === 'general' ? 'active' : ''}`}
              onClick={() => setSettingsTab('general')}
              style={{
                padding: '8px 16px',
                background: 'none',
                border: 'none',
                borderBottom: settingsTab === 'general' ? '2px solid #3b82f6' : 'none',
                color: settingsTab === 'general' ? 'var(--text-color)' : 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: 500
              }}
            >
              ⚙️ General
            </button>
            <button 
              className={`settings-tab-btn ${settingsTab === 'diagnostics' ? 'active' : ''}`}
              onClick={() => setSettingsTab('diagnostics')}
              style={{
                padding: '8px 16px',
                background: 'none',
                border: 'none',
                borderBottom: settingsTab === 'diagnostics' ? '2px solid #3b82f6' : 'none',
                color: settingsTab === 'diagnostics' ? 'var(--text-color)' : 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: 500
              }}
            >
              🛠️ Languages & Diagnostics
            </button>
          </div>

          {settingsTab === 'general' && (
            <>
              {/* Script Timeout */}
              <div className="setting-group">
                <label className="setting-label">Python Script Timeout (seconds)</label>
                <input
                  type="number"
                  min="1"
                  max="300"
                  value={settings.script_timeout}
                  onChange={(e) => setSettings({ ...settings, script_timeout: parseFloat(e.target.value) || 30 })}
                  className="setting-input-number"
                />
                <span className="setting-description">
                  Maximum duration a custom block script is allowed to execute.
                </span>
              </div>

              {/* VISA Backend */}
              <div className="setting-group">
                <label className="setting-label">VISA Backend</label>
                <select
                  value={settings.visa_backend}
                  onChange={(e) => setSettings({ ...settings, visa_backend: e.target.value })}
                  className="setting-select"
                >
                  <option value="">Auto Detect (System Default)</option>
                  <option value="@py">PyVISA-py (pure Python backend)</option>
                  <option value="@ni">National Instruments NI-VISA</option>
                </select>
                <span className="setting-description">
                  Select PyVISA backend wrapper library for hardware communication.
                </span>
              </div>

              {/* External Python Executable Path */}
              <div className="setting-group" style={{ marginTop: '12px' }}>
                <label className="setting-label">External Python Executable Path</label>
                <input
                  type="text"
                  placeholder="e.g. /usr/bin/python3 or C:\miniconda3\python.exe"
                  value={settings.external_python_path || ""}
                  onChange={(e) => setSettings({ ...settings, external_python_path: e.target.value })}
                  className="setting-input-text"
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid var(--block-border)',
                    background: 'var(--bg-card)',
                    color: 'var(--text-color)',
                    fontSize: '0.85rem',
                    outline: 'none',
                    marginTop: '4px'
                  }}
                />
                <span className="setting-description" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '4px' }}>
                  Default Python interpreter path used by the "External Python" script block. Leave empty to use the server's running interpreter.
                </span>
              </div>

              {/* Custom Block Directories */}
              <div className="setting-group">
                <label className="setting-label">Custom Discovery Folders</label>
                <div className="directories-list">
                  {settings.custom_node_dirs.length === 0 ? (
                    <div className="no-directories">No custom folders added.</div>
                  ) : (
                    settings.custom_node_dirs.map((dir, index) => (
                      <div key={index} className="directory-item">
                        <span className="directory-path" title={dir}>{dir}</span>
                        <button
                          className="directory-delete-btn"
                          onClick={() => {
                            const updatedDirs = settings.custom_node_dirs.filter((_, i) => i !== index);
                            setSettings({ ...settings, custom_node_dirs: updatedDirs });
                          }}
                          title="Remove folder"
                        >
                          ✕
                        </button>
                      </div>
                    ))
                  )}
                </div>
                
                <div className="add-directory-row">
                  <input
                    type="text"
                    placeholder="e.g. /home/user/my_blocks"
                    value={newDirInput}
                    onChange={(e) => setNewDirInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        const trimmed = newDirInput.trim();
                        if (trimmed && !settings.custom_node_dirs.includes(trimmed)) {
                          setSettings({
                            ...settings,
                            custom_node_dirs: [...settings.custom_node_dirs, trimmed]
                          });
                          setNewDirInput('');
                        }
                      }
                    }}
                    className="add-directory-input"
                  />
                  <button
                    type="button"
                    className="button-secondary"
                    onClick={() => {
                      const trimmed = newDirInput.trim();
                      if (trimmed && !settings.custom_node_dirs.includes(trimmed)) {
                        setSettings({
                          ...settings,
                          custom_node_dirs: [...settings.custom_node_dirs, trimmed]
                        });
                        setNewDirInput('');
                      }
                    }}
                    style={{ padding: '8px 12px' }}
                  >
                    ➕ Add
                  </button>
                </div>
                <span className="setting-description">
                  Paths to scan at startup for custom Python blocks.
                </span>
              </div>
            </>
          )}

          {settingsTab === 'diagnostics' && (
            <>
              {/* Scripting language toggles */}
              <div className="setting-group">
                <label className="setting-label">Enable Scripting Blocks</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '6px', background: 'var(--dnd-bg)', padding: '12px', borderRadius: '6px', border: '1px solid var(--block-border)' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '0.85rem' }}>
                    <input
                      type="checkbox"
                      checked={settings.enable_lua_scripting}
                      onChange={(e) => setSettings({ ...settings, enable_lua_scripting: e.target.checked })}
                    />
                    <span>🌙 Enable Lua Script Block</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '0.85rem' }}>
                    <input
                      type="checkbox"
                      checked={settings.enable_julia_scripting}
                      onChange={(e) => setSettings({ ...settings, enable_julia_scripting: e.target.checked })}
                    />
                    <span>👩‍🏫 Enable Julia Script Block</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '0.85rem' }}>
                    <input
                      type="checkbox"
                      checked={settings.enable_js_scripting}
                      onChange={(e) => setSettings({ ...settings, enable_js_scripting: e.target.checked })}
                    />
                    <span>☕ / 🟦 Enable JS/TS Script Block</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '0.85rem' }}>
                    <input
                      type="checkbox"
                      checked={settings.enable_rust_scripting}
                      onChange={(e) => setSettings({ ...settings, enable_rust_scripting: e.target.checked })}
                    />
                    <span>🦀 Enable Rust Script Block</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '0.85rem' }}>
                    <input
                      type="checkbox"
                      checked={settings.enable_r_scripting}
                      onChange={(e) => setSettings({ ...settings, enable_r_scripting: e.target.checked })}
                    />
                    <span>📊 Enable R Script Block</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '0.85rem' }}>
                    <input
                      type="checkbox"
                      checked={settings.enable_octave_scripting}
                      onChange={(e) => setSettings({ ...settings, enable_octave_scripting: e.target.checked })}
                    />
                    <span>📐 Enable Octave Script Block</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '0.85rem' }}>
                    <input
                      type="checkbox"
                      checked={settings.enable_wolfram_scripting}
                      onChange={(e) => setSettings({ ...settings, enable_wolfram_scripting: e.target.checked })}
                    />
                    <span>🧠 Enable Wolfram Script Block</span>
                  </label>
                </div>
              </div>

              {/* Diagnostics Checks */}
              <div className="setting-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label className="setting-label">System Dependencies Check</label>
                  <button 
                    className="button-secondary"
                    onClick={fetchDiagnostics}
                    disabled={loadingDiagnostics}
                    style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                  >
                    🔄 Refresh
                  </button>
                </div>
                {loadingDiagnostics ? (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', padding: '10px 0' }}>Checking system PATH binaries...</div>
                ) : diagnosticsData ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px', maxHeight: '180px', overflowY: 'auto', paddingRight: '4px' }}>
                    {Object.entries(diagnosticsData.dependencies || {}).map(([key, info]: [string, any]) => (
                      <div key={key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 10px', background: 'var(--input-bg)', border: '1px solid var(--block-border)', borderRadius: '6px' }}>
                        <div>
                          <div style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-color)' }}>{info.description}</div>
                          <div style={{ fontSize: '0.7rem', color: info.installed ? '#22c55e' : '#f97316' }}>{info.version}</div>
                        </div>
                        <span style={{ fontSize: '1rem' }}>{info.installed ? '✅' : '❌'}</span>
                      </div>
                    ))}
                    {Object.keys(diagnosticsData.instructions || {}).length > 0 && (
                      <div style={{ marginTop: '10px', padding: '10px', background: 'rgba(249, 115, 22, 0.08)', border: '1px solid rgba(249, 115, 22, 0.2)', borderRadius: '6px' }}>
                        <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f97316', marginBottom: '4px' }}>⚠️ Missing Dependencies Instructions:</div>
                        {Object.entries(diagnosticsData.instructions).map(([lang, inst]: [string, any]) => {
                          const renderTextWithLinks = (text: string) => {
                            const urlRegex = /(https?:\/\/[^\s\)]+)/g;
                            const parts = text.split(urlRegex);
                            return parts.map((part, i) => {
                              if (part.match(/^https?:\/\//)) {
                                let url = part;
                                let trailing = "";
                                if (url.endsWith(".")) {
                                  trailing = ".";
                                  url = url.slice(0, -1);
                                }
                                return (
                                  <span key={i}>
                                    <a
                                      href={url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      style={{ color: '#3b82f6', textDecoration: 'underline', wordBreak: 'break-all' }}
                                    >
                                      {url}
                                    </a>
                                    {trailing}
                                  </span>
                                );
                              }
                              return part;
                            });
                          };
                          return (
                            <div key={lang} style={{ fontSize: '0.75rem', color: 'var(--text-color)', marginTop: '2px' }}>
                              • <strong>{lang.toUpperCase()}:</strong> {renderTextWithLinks(inst)}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', padding: '10px 0' }}>Diagnostics status unavailable.</div>
                )}
              </div>
            </>
          )}

        </div>
        <div className="modal-footer" style={{ display: 'flex', gap: '10px', padding: '16px 20px' }}>
          <button
            className="button-secondary"
            onClick={onClose}
            style={{ flex: 1 }}
          >
            Cancel
          </button>
          <button
            className="button-primary"
            onClick={onSave}
            style={{ flex: 1.5, background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)' }}
          >
            💾 Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};
