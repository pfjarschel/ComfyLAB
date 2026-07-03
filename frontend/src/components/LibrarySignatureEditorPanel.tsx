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

import { useState, useEffect, useCallback, useRef } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface LibraryArg {
  id: string;         // local-only UUID for React key stability
  name: string;
  c_type: string;
  direction: string;  // "in" | "out" | "inout"
  size_arg: string;   // for "out": blank = scalar pointer, filled = buffer array
}

interface LibrarySignatureEditorPanelProps {
  isOpen: boolean;
  nodeId: string;
  nodeName: string;
  /** Current library_args property value (serialised array from node data) */
  libraryArgs: LibraryArg[];
  onSave: (args: LibraryArg[]) => void;
  onClose: () => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const C_TYPE_OPTIONS = [
  'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32',
  'int64', 'uint64', 'float32', 'float64', 'bool', 'c_char_p',
];

const DIRECTION_OPTIONS: { value: string; label: string }[] = [
  { value: 'in',    label: 'Input' },
  { value: 'out',   label: 'Output' },
  { value: 'inout', label: 'Input/Output' },
];

const DIRECTION_COLORS: Record<string, string> = {
  in:    '#60a5fa',   // blue
  out:   '#34d399',   // green
  inout: '#f59e0b',   // amber
};

const DIRECTION_BADGES: Record<string, string> = {
  in:    '→',
  out:   '←',
  inout: '⇄',
};

let _idCounter = 0;
const newId = () => `libarg_${Date.now()}_${_idCounter++}`;

const freshArg = (): LibraryArg => ({
  id: newId(),
  name: '',
  c_type: 'float32',
  direction: 'in',
  size_arg: '',
});

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const LibrarySignatureEditorPanel = ({
  isOpen,
  nodeId,
  nodeName,
  libraryArgs,
  onSave,
  onClose,
}: LibrarySignatureEditorPanelProps) => {
  const [args, setArgs] = useState<LibraryArg[]>([]);
  const [drawerWidth, setDrawerWidth] = useState(560);
  const isResizingRef = useRef(false);

  // Sync incoming libraryArgs whenever the panel opens or the source node changes
  useEffect(() => {
    if (isOpen) {
      // Ensure every entry has a stable local id
      setArgs(
        libraryArgs.map(a => ({ ...a, id: a.id || newId() }))
      );
    }
  }, [isOpen, nodeId]);

  // --- Resize handle (matches ScriptEditorPanel pattern) ---
  const handleResize = useCallback((e: MouseEvent) => {
    if (!isResizingRef.current) return;
    const newWidth = window.innerWidth - e.clientX;
    if (newWidth >= 380 && newWidth <= window.innerWidth * 0.85) {
      setDrawerWidth(newWidth);
    }
  }, []);

  const stopResize = useCallback(() => {
    isResizingRef.current = false;
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', stopResize);
  }, [handleResize]);

  const startResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isResizingRef.current = true;
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', stopResize);
  }, [handleResize, stopResize]);

  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleResize);
      document.removeEventListener('mouseup', stopResize);
    };
  }, [handleResize, stopResize]);

  // --- Escape key ---
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // --- Arg mutation helpers ---
  const addArg = () => setArgs(prev => [...prev, freshArg()]);

  const removeArg = (id: string) =>
    setArgs(prev => prev.filter(a => a.id !== id));

  const updateArg = (id: string, field: keyof LibraryArg, value: string) =>
    setArgs(prev =>
      prev.map(a => {
        if (a.id !== id) return a;
        const updated = { ...a, [field]: value };
        // Clear size_arg when direction is no longer "out"
        if (field === 'direction' && value !== 'out') {
          updated.size_arg = '';
        }
        return updated;
      })
    );

  const moveArg = (id: string, delta: -1 | 1) => {
    setArgs(prev => {
      const idx = prev.findIndex(a => a.id === id);
      if (idx < 0) return prev;
      const next = idx + delta;
      if (next < 0 || next >= prev.length) return prev;
      const arr = [...prev];
      [arr[idx], arr[next]] = [arr[next], arr[idx]];
      return arr;
    });
  };

  // --- Derived pin preview ---
  const previewIns = args.filter(a =>
    a.direction === 'in' || a.direction === 'inout'
  );
  const previewOuts = args.filter(a =>
    a.direction === 'out' ||
    a.direction === 'inout'
  );

  const handleApply = () => {
    onSave(args);
    onClose();
  };

  // ---------------------------------------------------------------------------
  // Styles (inline to avoid polluting App.css with a single-use panel)
  // ---------------------------------------------------------------------------
  const borderCol = 'var(--node-border, rgba(148,163,184,0.12))';
  const textMuted = 'var(--text-muted, #64748b)';
  const textColor = 'var(--text-color, #e2e8f0)';
  const inputBg = 'var(--input-bg, rgba(2,6,23,0.6))';

  const cellStyle: React.CSSProperties = {
    padding: '4px 6px',
    verticalAlign: 'middle',
  };

  const inputStyle: React.CSSProperties = {
    background: inputBg,
    border: `1px solid ${borderCol}`,
    borderRadius: '5px',
    color: textColor,
    fontSize: '0.78rem',
    padding: '4px 7px',
    width: '100%',
    outline: 'none',
    fontFamily: 'monospace',
  };

  const selectStyle: React.CSSProperties = {
    ...inputStyle,
    cursor: 'pointer',
  };

  return (
    <div
      className="script-editor-drawer nodrag nowheel"
      style={{ width: `${drawerWidth}px` }}
      onKeyDown={e => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
          e.preventDefault();
          handleApply();
        }
      }}
      tabIndex={0}
    >
      {/* Resize handle */}
      <div className="script-editor-resize-handle" onMouseDown={startResize} />

      {/* ---- Header ---- */}
      <div className="script-editor-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="script-editor-icon">⚡</span>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>
              DLL/SO Signature Editor
            </h3>
            <span
              className="script-editor-node-id"
              style={{ marginTop: '2px', fontFamily: 'monospace', fontSize: '0.7rem', color: textMuted }}
            >
              {nodeName || nodeId}
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center', fontSize: '0.72rem', color: textMuted }}>
          <span>{args.length} argument{args.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* ---- Hint banner ---- */}
      <div
        className="script-editor-hint"
        style={{ fontSize: '0.75rem', lineHeight: 1.5 }}
      >
        Define the C function's argument list in order. Each row becomes a
        DataIn/DataOut pin on the node. For <strong>Output</strong> arrays,
        specify a <strong>Size Arg</strong> matching the name of the input
        argument that holds the element count.
      </div>

      {/* ---- Table body ---- */}
      <div
        className="script-editor-body"
        style={{ padding: '12px 16px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}
      >
        {args.length === 0 && (
          <div
            style={{
              textAlign: 'center',
              color: textMuted,
              fontSize: '0.82rem',
              padding: '40px 20px',
              border: `1px dashed ${borderCol}`,
              borderRadius: '8px',
            }}
          >
            No arguments defined yet.
            <br />
            Click <strong>+ Add Argument</strong> below to start.
          </div>
        )}

        {args.map((arg, idx) => {
          const dirColor = DIRECTION_COLORS[arg.direction] || textMuted;
          const dirBadge = DIRECTION_BADGES[arg.direction] || '?';
          return (
            <div
              key={arg.id}
              style={{
                background: `${inputBg}`,
                border: `1px solid ${borderCol}`,
                borderLeft: `3px solid ${dirColor}`,
                borderRadius: '7px',
                padding: '10px 12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              {/* Row header: index badge + direction badge + move + delete */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    color: textMuted,
                    minWidth: '18px',
                    textAlign: 'center',
                    background: 'rgba(148,163,184,0.08)',
                    borderRadius: '4px',
                    padding: '2px 4px',
                  }}
                >
                  {idx + 1}
                </span>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    color: dirColor,
                    background: `${dirColor}18`,
                    border: `1px solid ${dirColor}40`,
                    borderRadius: '4px',
                    padding: '2px 6px',
                    fontFamily: 'monospace',
                  }}
                >
                  {dirBadge}
                </span>
                <span style={{ flex: 1, fontSize: '0.8rem', fontWeight: 600, color: textColor, fontFamily: 'monospace' }}>
                  {arg.name || <span style={{ color: textMuted, fontStyle: 'italic' }}>unnamed</span>}
                </span>
                <button
                  onClick={() => moveArg(arg.id, -1)}
                  disabled={idx === 0}
                  title="Move up"
                  style={{
                    background: 'none', border: 'none', cursor: idx === 0 ? 'not-allowed' : 'pointer',
                    color: idx === 0 ? borderCol : textMuted, fontSize: '0.75rem', padding: '2px 5px',
                    borderRadius: '4px', lineHeight: 1,
                  }}
                >▲</button>
                <button
                  onClick={() => moveArg(arg.id, 1)}
                  disabled={idx === args.length - 1}
                  title="Move down"
                  style={{
                    background: 'none', border: 'none', cursor: idx === args.length - 1 ? 'not-allowed' : 'pointer',
                    color: idx === args.length - 1 ? borderCol : textMuted, fontSize: '0.75rem', padding: '2px 5px',
                    borderRadius: '4px', lineHeight: 1,
                  }}
                >▼</button>
                <button
                  onClick={() => removeArg(arg.id)}
                  title="Remove argument"
                  style={{
                    background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)',
                    color: '#f87171', cursor: 'pointer', fontSize: '0.7rem', padding: '2px 7px',
                    borderRadius: '4px', fontWeight: 700,
                  }}
                >✕</button>
              </div>

              {/* Fields grid */}
              <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 0' }}>
                <tbody>
                  <tr>
                    <td style={{ ...cellStyle, width: '70px' }}>
                      <span style={{ fontSize: '0.68rem', color: textMuted, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>Name</span>
                    </td>
                    <td style={cellStyle}>
                      <input
                        type="text"
                        value={arg.name}
                        placeholder="arg_name"
                        onChange={e => updateArg(arg.id, 'name', e.target.value)}
                        style={inputStyle}
                        spellCheck={false}
                      />
                    </td>
                    <td style={{ ...cellStyle, width: '80px', paddingLeft: '10px' }}>
                      <span style={{ fontSize: '0.68rem', color: textMuted, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>C Type</span>
                    </td>
                    <td style={{ ...cellStyle, width: '110px' }}>
                      <select
                        value={arg.c_type}
                        onChange={e => updateArg(arg.id, 'c_type', e.target.value)}
                        style={selectStyle}
                      >
                        {C_TYPE_OPTIONS.map(t => (
                          <option key={t} value={t}>{t}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                  <tr>
                    <td style={{ ...cellStyle, paddingTop: '6px' }}>
                      <span style={{ fontSize: '0.68rem', color: textMuted, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>Direction</span>
                    </td>
                    <td style={{ ...cellStyle, paddingTop: '6px' }} colSpan={3}>
                      <select
                        value={arg.direction}
                        onChange={e => updateArg(arg.id, 'direction', e.target.value)}
                        style={{ ...selectStyle, borderColor: `${dirColor}60` }}
                      >
                        {DIRECTION_OPTIONS.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                  {arg.direction === 'out' && (
                    <tr>
                      <td style={{ ...cellStyle, paddingTop: '6px' }}>
                        <span style={{ fontSize: '0.68rem', color: '#f59e0b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>Size Arg</span>
                      </td>
                      <td style={{ ...cellStyle, paddingTop: '6px' }} colSpan={3}>
                        <input
                          type="text"
                          value={arg.size_arg}
                          placeholder="Input arg name holding element count (leave blank for scalar)"
                          onChange={e => updateArg(arg.id, 'size_arg', e.target.value)}
                          style={{ ...inputStyle, borderColor: 'rgba(245,158,11,0.4)' }}
                          spellCheck={false}
                        />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>

              {/* Inline pin hint */}
              <div style={{ fontSize: '0.68rem', color: textMuted, paddingLeft: '2px' }}>
                {arg.direction === 'in' && (
                  <span>Creates <span style={{ color: '#60a5fa' }}>Input pin ("{arg.name || '...'}")</span></span>
                )}
                {arg.direction === 'out' && !arg.size_arg && (
                  <span>Creates <span style={{ color: '#34d399' }}>Output pin ("{arg.name || '...'}")</span> — single {arg.c_type} value</span>
                )}
                {arg.direction === 'out' && arg.size_arg && (
                  <span>Creates <span style={{ color: '#34d399' }}>Output pin ("{arg.name || '...'}")</span> — array of {arg.c_type}, size from <em>{arg.size_arg}</em></span>
                )}
                {arg.direction === 'inout' && (
                  <span>Creates <span style={{ color: '#60a5fa' }}>Input pin</span> + <span style={{ color: '#f59e0b' }}>Output pin ("{arg.name || '...'}")</span> — buffer modified in-place</span>
                )}
              </div>
            </div>
          );
        })}

        {/* Add button */}
        <button
          onClick={addArg}
          style={{
            background: 'rgba(59,130,246,0.1)',
            border: '1px dashed rgba(59,130,246,0.4)',
            borderRadius: '7px',
            color: '#60a5fa',
            cursor: 'pointer',
            fontSize: '0.82rem',
            fontWeight: 600,
            padding: '10px',
            width: '100%',
            transition: 'background 0.15s, border-color 0.15s',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = 'rgba(59,130,246,0.18)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'rgba(59,130,246,0.1)')}
        >
          + Add Argument
        </button>

        {/* Pin preview section */}
        {args.length > 0 && (
          <div
            style={{
              marginTop: '6px',
              padding: '12px 14px',
              background: 'rgba(2,6,23,0.4)',
              border: `1px solid ${borderCol}`,
              borderRadius: '8px',
            }}
          >
            <div style={{ fontSize: '0.72rem', color: textMuted, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '10px' }}>
              Generated Pins Preview
            </div>
            <div style={{ display: 'flex', gap: '20px' }}>
              {/* DataIn pins */}
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.7rem', color: textMuted, marginBottom: '6px' }}>DataIn (inputs):</div>
                {/* Static pins always present */}
                {['Library', 'FunctionName', 'ReturnType'].map(p => (
                  <div key={p} style={{ fontSize: '0.7rem', color: '#475569', fontFamily: 'monospace', padding: '2px 0' }}>
                    ● {p} <span style={{ color: '#334155', fontSize: '0.65rem' }}>(static)</span>
                  </div>
                ))}
                {previewIns.map(a => (
                  <div
                    key={a.id}
                    style={{
                      fontSize: '0.72rem',
                      color: DIRECTION_COLORS[a.direction],
                      fontFamily: 'monospace',
                      padding: '2px 0',
                    }}
                  >
                    ● {a.name || '(unnamed)'}
                    {a.direction === 'inout' && <span style={{ color: textMuted, fontSize: '0.65rem' }}> (in/out)</span>}
                  </div>
                ))}
                {previewIns.length === 0 && (
                  <div style={{ fontSize: '0.68rem', color: '#334155', fontStyle: 'italic' }}>No dynamic inputs</div>
                )}
              </div>
              {/* DataOut pins */}
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.7rem', color: textMuted, marginBottom: '6px' }}>DataOut (outputs):</div>
                {['ReturnValue', 'Status'].map(p => (
                  <div key={p} style={{ fontSize: '0.7rem', color: '#475569', fontFamily: 'monospace', padding: '2px 0' }}>
                    ● {p} <span style={{ color: '#334155', fontSize: '0.65rem' }}>(static)</span>
                  </div>
                ))}
                {previewOuts.map(a => (
                  <div
                    key={a.id}
                    style={{
                      fontSize: '0.72rem',
                      color: DIRECTION_COLORS[a.direction],
                      fontFamily: 'monospace',
                      padding: '2px 0',
                    }}
                  >
                    ● {a.name || '(unnamed)'}
                    {a.direction === 'inout' && <span style={{ color: textMuted, fontSize: '0.65rem' }}> (in/out)</span>}
                  </div>
                ))}
                {previewOuts.length === 0 && (
                  <div style={{ fontSize: '0.68rem', color: '#334155', fontStyle: 'italic' }}>No dynamic outputs</div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ---- Footer ---- */}
      <div className="script-editor-footer">
        <button className="button-secondary" onClick={onClose} style={{ flex: 1 }}>
          Cancel
        </button>
        <button className="button-primary" onClick={handleApply} style={{ flex: 1.5 }}>
          ⚡ Apply &amp; Close
        </button>
      </div>
    </div>
  );
};
