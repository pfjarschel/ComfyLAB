import React, { useEffect, useRef } from 'react';
import { useTranslation } from '../../i18n';

interface AlertModalProps {
  title?: string;
  message: string;
  onClose: () => void;
}

export const AlertModal: React.FC<AlertModalProps> = ({
  title,
  message,
  onClose,
}) => {
  const { t } = useTranslation();
  const modalRef = useRef<HTMLDivElement>(null);

  // Close on escape or enter key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || e.key === 'Enter') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="modal-overlay"
      style={{
        zIndex: 10000, // Ensure it's above everything else
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div 
        className="modal-content glass-panel" 
        ref={modalRef}
        style={{
          maxWidth: '450px',
          width: '100%',
        }}
      >
        <div className="modal-header">
          <h3>{title || t('modals.alertTitle', 'Notification')}</h3>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body" style={{ padding: '24px 20px', lineHeight: '1.5' }}>
          <p style={{ margin: 0, color: 'var(--text-color)' }}>{message}</p>
        </div>
        <div className="modal-footer" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'flex-end' }}>
          <button 
            className="button-primary" 
            onClick={onClose} 
            style={{ width: '100px' }}
            autoFocus
          >
            {t('common.ok', 'OK')}
          </button>
        </div>
      </div>
    </div>
  );
};
