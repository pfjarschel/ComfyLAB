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


interface LoadWorkspaceModalProps {
  isOpen: boolean;
  workspaceBlueprints: { filename: string; path: string; isPackage?: boolean }[];
  onClose: () => void;
  onOpenPackage: (filename: string) => void;
  onLoadBlueprintByName: (filename: string) => void;
}

export const LoadWorkspaceModal = ({
  isOpen,
  workspaceBlueprints,
  onClose,
  onOpenPackage,
  onLoadBlueprintByName,
}: LoadWorkspaceModalProps) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" style={{ zIndex: 1000 }} onClick={onClose}>
      <div className="modal-content glass-panel" style={{ width: '450px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>📂</span> Load Blueprint from Workspace
          </h3>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '16px 20px', maxHeight: '350px', overflowY: 'auto' }}>
          {workspaceBlueprints.length === 0 ? (
            <div style={{ color: '#64748b', fontSize: '0.85rem', textAlign: 'center', padding: '20px', fontStyle: 'italic' }}>
              No blueprints found in the active workspace.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {workspaceBlueprints.map((bp) => (
                <div 
                  key={bp.filename} 
                  className="blueprint-list-item"
                  onClick={() => bp.isPackage ? onOpenPackage(bp.filename) : onLoadBlueprintByName(bp.filename)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 12px',
                    background: 'var(--dnd-bg)',
                    border: '1px solid var(--node-border)',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <span style={{ fontSize: '1.1rem' }}>{bp.isPackage ? '📦' : '📄'}</span>
                  <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-color)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {bp.filename}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={bp.path}>
                      {bp.path}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="modal-footer" style={{ padding: '12px 20px' }}>
          <button className="button-secondary" onClick={onClose} style={{ width: '100%' }}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
