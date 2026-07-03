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


interface SaveWorkspaceModalProps {
  isOpen: boolean;
  saveFilenameInput: string;
  exportAsPackage: boolean;
  setSaveFilenameInput: (value: string) => void;
  setExportAsPackage: (value: boolean) => void;
  onClose: () => void;
  onSubmit: () => void;
}

export const SaveWorkspaceModal = ({
  isOpen,
  saveFilenameInput,
  exportAsPackage,
  setSaveFilenameInput,
  setExportAsPackage,
  onClose,
  onSubmit,
}: SaveWorkspaceModalProps) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" style={{ zIndex: 1000 }} onClick={onClose}>
      <div className="modal-content glass-panel" style={{ width: '400px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>💾</span> Save Blueprint to Workspace
          </h3>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '16px 20px' }}>
          <div className="input-group">
            <label>Blueprint Name</label>
            <input
              type="text"
              placeholder="e.g. calibration_routine"
              value={saveFilenameInput}
              onChange={(e) => setSaveFilenameInput(e.target.value)}
              style={{ background: 'var(--input-bg)', border: '1px solid var(--node-border)', color: 'var(--text-color)', padding: '8px', borderRadius: '6px' }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  onSubmit();
                }
              }}
              autoFocus
            />
            <span className="setting-description">
              The blueprint will be saved inside your active workspace directory.
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px' }}>
            <input
              type="checkbox"
              id="exportAsPackageCheck"
              checked={exportAsPackage}
              onChange={(e) => setExportAsPackage(e.target.checked)}
              style={{ cursor: 'pointer', width: '16px', height: '16px' }}
            />
            <label htmlFor="exportAsPackageCheck" style={{ fontSize: '0.85rem', color: 'var(--text-color)', cursor: 'pointer', margin: 0, fontWeight: 500 }}>
              📦 Export as CFY Package (includes custom nodes & macros)
            </label>
          </div>
        </div>

        <div className="modal-footer" style={{ display: 'flex', gap: '10px', padding: '12px 20px' }}>
          <button className="button-secondary" onClick={onClose} style={{ flex: 1 }}>
            Cancel
          </button>
          <button 
            className="button-primary" 
            onClick={onSubmit}
            style={{ flex: 1.5, background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
          >
            💾 Save Blueprint
          </button>
        </div>
      </div>
    </div>
  );
};
