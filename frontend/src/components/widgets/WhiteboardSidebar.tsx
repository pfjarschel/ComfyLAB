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


interface WhiteboardSidebarProps {
  isOpen: boolean;
  drawTool: string;
  setDrawTool: (tool: any) => void;
  lineStartCap: 'none' | 'arrow' | 'dot' | 'bar';
  setLineStartCap: (cap: any) => void;
  lineEndCap: 'none' | 'arrow' | 'dot' | 'bar';
  setLineEndCap: (cap: any) => void;
  drawColor: string;
  setDrawColor: (color: string) => void;
  drawStyle: 'flat' | 'neon' | 'dashed' | 'neon-dashed';
  setDrawStyle: (style: any) => void;
  drawWidth: number;
  setDrawWidth: (width: number) => void;
  drawFillEnable: boolean;
  setDrawFillEnable: (enable: boolean) => void;
  drawFillColor: string;
  setDrawFillColor: (color: string) => void;
  drawFillOpacity: number;
  setDrawFillOpacity: (opacity: number) => void;
  onClearAll: () => void;
  onDone: () => void;
  setEditingTextId: (id: string | null) => void;
}

export const WhiteboardSidebar = ({
  isOpen,
  drawTool,
  setDrawTool,
  lineStartCap,
  setLineStartCap,
  lineEndCap,
  setLineEndCap,
  drawColor,
  setDrawColor,
  drawStyle,
  setDrawStyle,
  drawWidth,
  setDrawWidth,
  drawFillEnable,
  setDrawFillEnable,
  drawFillColor,
  setDrawFillColor,
  drawFillOpacity,
  setDrawFillOpacity,
  onClearAll,
  onDone,
  setEditingTextId,
}: WhiteboardSidebarProps) => {
  if (!isOpen) return null;

  return (
    <div
      className="sidebar-container right-sidebar glass-panel nodrag nowheel animate-slide-in-right"
      style={{
        zIndex: 1000,
        pointerEvents: 'auto',
      }}
      onMouseDown={(e) => e.stopPropagation()}
    >
      <div className="sidebar-header">
        <h3>✏️ Whiteboard</h3>
        <button
          className="sidebar-close-btn"
          onClick={onDone}
          title="Exit Drawing Mode"
        >
          ✕
        </button>
      </div>

      <div className="sidebar-content">
        {/* Tools Grid */}
        <div className="sidebar-section">
          <span className="sidebar-label">Drawing Tools</span>
          <div className="tools-grid">
            {[
              { id: 'pen', label: 'Pen', icon: '✏️' },
              { id: 'eraser', label: 'Eraser', icon: '🧹' },
              { id: 'text', label: 'Text Note', icon: '🔤' },
              { id: 'line', label: 'Line', icon: '➖' },
              { id: 'circle', label: 'Circle', icon: '⚪' },
              { id: 'rectangle', label: 'Rectangle', icon: '⬜' },
              { id: 'polyline', label: 'Polyline', icon: '📈' },
              { id: 'polygon', label: 'Polygon', icon: '⬟' },
            ].map((t) => (
              <button
                key={t.id}
                className={`tool-grid-btn ${drawTool === t.id ? 'active' : ''}`}
                onClick={() => { setDrawTool(t.id as any); setEditingTextId(null); }}
                title={t.label}
              >
                <span className="tool-icon">{t.icon}</span>
                <span className="tool-name">{t.label}</span>
              </button>
            ))}
          </div>
        </div>

        {drawTool !== 'eraser' && (
          <>
            <div className="sidebar-divider" />

            {/* Line/Polyline settings (Start/End Caps) */}
            {(drawTool === 'line' || drawTool === 'polyline') && (
              <div className="sidebar-section">
                <div className="sidebar-flex-row">
                  <div className="sidebar-flex-item">
                    <span className="sidebar-label">Start Cap</span>
                    <select
                      value={lineStartCap}
                      onChange={(e) => setLineStartCap(e.target.value as any)}
                      className="toolbar-select"
                      style={{ width: '100%', marginTop: '4px' }}
                    >
                      <option value="none">None</option>
                      <option value="arrow">Arrow</option>
                      <option value="dot">Dot</option>
                      <option value="bar">Bar</option>
                    </select>
                  </div>
                  <div className="sidebar-flex-item">
                    <span className="sidebar-label">End Cap</span>
                    <select
                      value={lineEndCap}
                      onChange={(e) => setLineEndCap(e.target.value as any)}
                      className="toolbar-select"
                      style={{ width: '100%', marginTop: '4px' }}
                    >
                      <option value="none">None</option>
                      <option value="arrow">Arrow</option>
                      <option value="dot">Dot</option>
                      <option value="bar">Bar</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Stroke Settings */}
            <div className="sidebar-section">
              <span className="sidebar-label">Stroke Color</span>
              <div className="preset-colors">
                {[
                  { hex: '#00f3ff', label: 'Cyan' },
                  { hex: '#39ff14', label: 'Green' },
                  { hex: '#ff073a', label: 'Red' },
                  { hex: '#fff01f', label: 'Yellow' },
                  { hex: '#ff007f', label: 'Pink' },
                  { hex: '#d0d0d0', label: 'Light Gray' },
                  { hex: '#303030', label: 'Dark Gray' },
                ].map((c) => (
                  <button
                    key={c.hex}
                    className={`preset-color-dot ${drawColor === c.hex ? 'active' : ''}`}
                    style={{
                      backgroundColor: c.hex,
                      boxShadow: `0 0 8px ${c.hex}`,
                    }}
                    onClick={() => setDrawColor(c.hex)}
                    title={c.label}
                  />
                ))}
                <div className="color-picker-wrapper" title="Custom Color">
                  <input
                    type="color"
                    value={drawColor}
                    onChange={(e) => setDrawColor(e.target.value)}
                    className="toolbar-color-picker"
                  />
                </div>
              </div>
            </div>

            <div className="sidebar-section">
              <div className="sidebar-flex-row">
                <div className="sidebar-flex-item">
                  <span className="sidebar-label">Style</span>
                  <select
                    value={drawStyle}
                    onChange={(e) => setDrawStyle(e.target.value as any)}
                    className="toolbar-select"
                    style={{ width: '100%', marginTop: '4px' }}
                  >
                    <option value="flat">Flat</option>
                    <option value="neon">Neon</option>
                    <option value="dashed">Dashed</option>
                    <option value="neon-dashed">Neon Dashed</option>
                  </select>
                </div>
                <div className="sidebar-flex-item" style={{ flexGrow: 1.2 }}>
                  <span className="sidebar-label">Width: {drawWidth}px</span>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={drawWidth}
                    onChange={(e) => setDrawWidth(Number(e.target.value))}
                    className="toolbar-slider"
                    style={{ width: '100%', marginTop: '8px' }}
                  />
                </div>
              </div>
            </div>

            {/* Fill Settings (for rect, circle, polygon) */}
            {(drawTool === 'rectangle' || drawTool === 'circle' || drawTool === 'polygon') && (
              <>
                <div className="sidebar-divider" />
                <div className="sidebar-section">
                  <label className="sidebar-checkbox-label">
                    <input
                      type="checkbox"
                      checked={drawFillEnable}
                      onChange={(e) => setDrawFillEnable(e.target.checked)}
                    />
                    <span>Fill Shape</span>
                  </label>

                  {drawFillEnable && (
                    <div className="sidebar-fill-panel animate-fade-in" style={{ marginTop: '10px' }}>
                      <div className="sidebar-flex-row" style={{ alignItems: 'center' }}>
                        <span className="sidebar-label" style={{ marginRight: '8px' }}>Color:</span>
                        <div
                          className="color-picker-wrapper"
                          style={{
                            width: '28px',
                            height: '20px',
                            borderRadius: '4px',
                            background: drawFillColor,
                            border: '1px solid rgba(255, 255, 255, 0.4)',
                            position: 'relative',
                            overflow: 'hidden',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                          }}
                          title="Custom Fill Color"
                        >
                          <input
                            type="color"
                            value={drawFillColor}
                            onChange={(e) => setDrawFillColor(e.target.value)}
                            className="toolbar-color-picker"
                            style={{
                              position: 'absolute',
                              width: '100%',
                              height: '100%',
                              opacity: 0,
                              cursor: 'pointer',
                            }}
                          />
                        </div>
                      </div>
                      <div style={{ marginTop: '8px' }}>
                        <span className="sidebar-label">Opacity: {Math.round(drawFillOpacity * 100)}%</span>
                        <input
                          type="range"
                          min="0.1"
                          max="1.0"
                          step="0.1"
                          value={drawFillOpacity}
                          onChange={(e) => setDrawFillOpacity(Number(e.target.value))}
                          className="toolbar-slider"
                          style={{ width: '100%', marginTop: '4px' }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </>
        )}

        <div className="sidebar-divider" />

        {/* Actions */}
        <div className="sidebar-actions">
          <button
            className="toolbar-action-btn danger"
            onClick={onClearAll}
            title="Clear All Annotations"
            style={{ width: '100%', display: 'block' }}
          >
            🗑️ Clear All
          </button>
          <button
            className="toolbar-action-btn"
            onClick={onDone}
            style={{ width: '100%', marginTop: '8px', display: 'block' }}
          >
            Done Drawing
          </button>
        </div>
      </div>
    </div>
  );
};
