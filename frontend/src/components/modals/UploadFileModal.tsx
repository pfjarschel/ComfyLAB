import React, { useState, useRef } from 'react';
import axios from 'axios';

interface UploadFileModalProps {
  isOpen: boolean;
  onClose: () => void;
  BACKEND_URL: string;
}

export const UploadFileModal = ({ isOpen, onClose, BACKEND_URL }: UploadFileModalProps) => {
  const [file, setFile] = useState<File | null>(null);
  const [subdir, setSubdir] = useState('');
  const [filename, setFilename] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selected = e.target.files[0];
      setFile(selected);
      setFilename(selected.name);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file first.");
      return;
    }

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('subdir', subdir);
    formData.append('filename', filename);

    try {
      const res = await axios.post(`${BACKEND_URL}/workspace/uploads`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log('Uploaded successfully', res.data);
      onClose();
      // Optionally reset state here
      setFile(null);
      setSubdir('');
      setFilename('');
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err: any) {
      console.error('Upload failed', err);
      setError(err.response?.data?.detail || 'Failed to upload file.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="modal-overlay" style={{ zIndex: 1000 }} onClick={onClose}>
      <div className="modal-content glass-panel" style={{ width: '450px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>📤</span> Upload File to Workspace
          </h3>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>
        
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '16px 20px' }}>
          {error && (
            <div style={{ color: '#ef4444', fontSize: '0.9rem', padding: '8px', background: '#ef44441a', borderRadius: '4px' }}>
              {error}
            </div>
          )}
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>File</label>
            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleFileChange} 
              style={{ fontSize: '0.9rem' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>Subdirectory (optional)</label>
            <input 
              type="text" 
              value={subdir}
              onChange={(e) => setSubdir(e.target.value)}
              placeholder="e.g. images/raw"
              className="nodrag"
              style={{ 
                padding: '8px', 
                borderRadius: '4px', 
                border: '1px solid var(--block-border)',
                background: 'var(--dnd-bg)',
                color: 'var(--text-color)',
                fontSize: '0.9rem'
              }}
            />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Folders will be created if they do not exist.
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>File Name</label>
            <input 
              type="text" 
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              placeholder="e.g. my_image.png"
              className="nodrag"
              disabled={!file}
              style={{ 
                padding: '8px', 
                borderRadius: '4px', 
                border: '1px solid var(--block-border)',
                background: file ? 'var(--dnd-bg)' : 'transparent',
                color: 'var(--text-color)',
                fontSize: '0.9rem',
                opacity: file ? 1 : 0.6
              }}
            />
          </div>
        </div>

        <div className="modal-footer" style={{ padding: '12px 20px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button className="button-secondary" onClick={onClose} disabled={isUploading}>
            Cancel
          </button>
          <button 
            className="button-primary" 
            onClick={handleUpload} 
            disabled={!file || isUploading}
            style={{ minWidth: '80px' }}
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      </div>
    </div>
  );
};
