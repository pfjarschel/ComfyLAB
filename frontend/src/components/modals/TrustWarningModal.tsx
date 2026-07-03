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


interface TrustWarningModalProps {
  isOpen: boolean;
  trustWarningMessage: string;
  pendingBlueprint: any;
  onClose: () => void;
  onAlwaysTrust: () => void;
  onTrustOnce: () => void;
}

export const TrustWarningModal = ({
  isOpen,
  trustWarningMessage,
  pendingBlueprint,
  onClose,
  onAlwaysTrust,
  onTrustOnce,
}: TrustWarningModalProps) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" style={{ zIndex: 1001 }} onClick={onClose}>
      <div className="modal-content glass-panel" style={{ width: '450px', border: '1px solid #f59e0b' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header" style={{ borderBottom: '1px solid rgba(245, 158, 11, 0.2)' }}>
          <h3 style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
            ⚠️ Security Trust Warning
          </h3>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px' }}>
          <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.5', color: '#e2e8f0' }}>
            {trustWarningMessage}
          </p>
          <div style={{ padding: '10px', borderRadius: '4px', background: 'rgba(245, 158, 11, 0.05)', border: '1px solid rgba(245, 158, 11, 0.15)', fontSize: '12px', color: '#cbd5e1' }}>
            <strong>Creator Identity:</strong> <code style={{ color: '#f59e0b' }}>{pendingBlueprint?.origin_uuid || "Unknown"}</code>
            <br /><br />
            Running blueprints from untrusted creators or sources can execute arbitrary Python/JavaScript code on your system.
          </div>
        </div>
        <div className="modal-footer" style={{ display: 'flex', gap: '10px', padding: '16px 20px', justifyContent: 'flex-end', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <button className="button-secondary" style={{ marginRight: 'auto' }} onClick={onClose}>
            Cancel
          </button>
          {pendingBlueprint?.origin_uuid && (
            <button 
              className="button-secondary"
              onClick={onAlwaysTrust}
            >
              Always Trust Origin
            </button>
          )}
          <button 
            className="button-primary" 
            style={{ background: '#f59e0b', color: '#090d16', fontWeight: 'bold' }}
            onClick={onTrustOnce}
          >
            Trust Once & Load
          </button>
        </div>
      </div>
    </div>
  );
};
