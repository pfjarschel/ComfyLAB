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


interface PackageImportModalProps {
  isOpen: boolean;
  packageFilename: string;
  packagePreviewData: any;
  importDestination: 'workspace' | 'user';
  importPermanent: boolean;
  trustAndSign: boolean;
  deletePackageAfterImport: boolean;
  onClose: () => void;
  setImportDestination: (value: 'workspace' | 'user') => void;
  setImportPermanent: (value: boolean) => void;
  setTrustAndSign: (value: boolean) => void;
  setDeletePackageAfterImport: (value: boolean) => void;
  onImport: () => void;
}

export const PackageImportModal = ({
  isOpen,
  packageFilename,
  packagePreviewData,
  importDestination,
  importPermanent,
  trustAndSign,
  deletePackageAfterImport,
  onClose,
  setImportDestination,
  setImportPermanent,
  setTrustAndSign,
  setDeletePackageAfterImport,
  onImport,
}: PackageImportModalProps) => {
  if (!isOpen || !packagePreviewData) return null;

  const hasUntrusted = !packagePreviewData.blueprint_status?.is_trusted || 
                       packagePreviewData.blocks?.some((n: any) => !n.is_trusted) || 
                       packagePreviewData.clusters?.some((m: any) => !m.is_trusted);

  return (
    <div className="modal-overlay" style={{ zIndex: 1001 }} onClick={onClose}>
      <div className="modal-content glass-panel" style={{ width: '500px', border: '1px solid var(--block-border)' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header" style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-color)' }}>
            <span>📦</span> Preview Package: {packageFilename}
          </h3>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px', maxHeight: '450px', overflowY: 'auto' }}>
          
          {/* Trust Status Overview */}
          {hasUntrusted ? (
            <div style={{ padding: '12px', borderRadius: '6px', background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.25)', color: '#f59e0b', fontSize: '0.85rem', lineHeight: '1.4' }}>
              <strong>⚠️ Security Warning:</strong> This package contains unsigned or untrusted components. Running unsigned code can pose security risks. If you trust this code, you can authorize it below.
            </div>
          ) : (
            <div style={{ padding: '12px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.25)', color: '#10b981', fontSize: '0.85rem', lineHeight: '1.4' }}>
              <strong>🛡️ Verified Package:</strong> All custom code in this package is signed and trusted.
            </div>
          )}

          {/* Blueprint Info */}
          <div style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '12px' }}>
            <h4 style={{ margin: '0 0 6px 0', fontSize: '0.9rem', color: 'var(--text-color)' }}>Blueprint:</h4>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.02)', padding: '6px 10px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.05)' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{packageFilename.replace(/\.cfy$/, '.json')}</span>
              <span style={{ fontSize: '0.8rem', color: packagePreviewData.blueprint_status?.is_trusted ? '#10b981' : '#f59e0b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                {packagePreviewData.blueprint_status?.is_trusted ? '🛡️ Trusted' : '⚠️ Untrusted'}
              </span>
            </div>
          </div>

          {/* Blocks List */}
          {packagePreviewData.blocks && packagePreviewData.blocks.length > 0 && (
            <div style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '12px' }}>
              <h4 style={{ margin: '0 0 6px 0', fontSize: '0.9rem', color: 'var(--text-color)' }}>Custom Blocks:</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {packagePreviewData.blocks.map((block: any) => (
                  <div key={block.filename} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.02)', padding: '6px 10px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{block.filename}</span>
                    <span style={{ fontSize: '0.8rem', color: block.is_trusted ? '#10b981' : '#f59e0b' }}>
                      {block.is_trusted ? '🛡️ Trusted' : '⚠️ Untrusted'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Clusters List */}
          {packagePreviewData.clusters && packagePreviewData.clusters.length > 0 && (
            <div style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '12px' }}>
              <h4 style={{ margin: '0 0 6px 0', fontSize: '0.9rem', color: 'var(--text-color)' }}>Clusters:</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {packagePreviewData.clusters.map((cluster: any) => (
                  <div key={cluster.filename} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.02)', padding: '6px 10px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{cluster.filename}</span>
                    <span style={{ fontSize: '0.8rem', color: cluster.is_trusted ? '#10b981' : '#f59e0b' }}>
                      {cluster.is_trusted ? '🛡️ Trusted' : '⚠️ Untrusted'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Permanent Import Toggle Checkbox */}
          <div style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '12px', marginBottom: '4px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer', fontWeight: 500, color: 'var(--text-color)' }}>
              <input 
                type="checkbox" 
                checked={importPermanent} 
                onChange={(e) => setImportPermanent(e.target.checked)}
                style={{ width: '16px', height: '16px' }}
              />
              <span>📥 Import package permanently to workspace/user directory</span>
            </label>
          </div>

          {/* Destination Selector */}
          <div className="input-group" style={{ display: 'flex', flexDirection: 'column', gap: '6px', opacity: importPermanent ? 1 : 0.5 }}>
            <label style={{ fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-color)' }}>Destination Directory</label>
            <div style={{ display: 'flex', gap: '16px', marginTop: '4px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', cursor: importPermanent ? 'pointer' : 'not-allowed', color: 'var(--text-color)' }}>
                <input 
                  type="radio" 
                  name="importDest" 
                  checked={importDestination === 'workspace'} 
                  onChange={() => importPermanent && setImportDestination('workspace')}
                  disabled={!importPermanent}
                />
                Active Workspace
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', cursor: importPermanent ? 'pointer' : 'not-allowed', color: 'var(--text-color)' }}>
                <input 
                  type="radio" 
                  name="importDest" 
                  checked={importDestination === 'user'} 
                  onChange={() => importPermanent && setImportDestination('user')}
                  disabled={!importPermanent}
                />
                Local User Directory (~/.comfylab)
              </label>
            </div>
          </div>

          {/* Import Options Checkboxes */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer', fontWeight: 500, color: 'var(--text-color)' }}>
              <input 
                type="checkbox" 
                checked={trustAndSign} 
                onChange={(e) => setTrustAndSign(e.target.checked)}
                style={{ width: '16px', height: '16px' }}
              />
              <span>🛡️ Trust & Sign code locally (authorizes untrusted items)</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: importPermanent ? 'pointer' : 'not-allowed', fontWeight: 500, color: 'var(--text-color)', opacity: importPermanent ? 1 : 0.5 }}>
              <input 
                type="checkbox" 
                checked={deletePackageAfterImport} 
                onChange={(e) => importPermanent && setDeletePackageAfterImport(e.target.checked)}
                disabled={!importPermanent}
                style={{ width: '16px', height: '16px' }}
              />
              <span>🧹 Delete package file after importing</span>
            </label>
          </div>

        </div>
        <div className="modal-footer" style={{ display: 'flex', gap: '10px', padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <button className="button-secondary" onClick={onClose} style={{ flex: 1 }}>
            Cancel
          </button>
          <button 
            className="button-primary" 
            onClick={onImport}
            style={{ flex: 1.5, background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', fontWeight: 'bold' }}
          >
            {importPermanent ? '📥 Import Package' : '📂 Open Package (Temporary)'}
          </button>
        </div>
      </div>
    </div>
  );
};
