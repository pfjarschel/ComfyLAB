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

import React, { useEffect, useState } from 'react';

interface SplashScreenModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNewBlueprint: () => void;
  onLoadBlueprint: () => void;
  onLoadExample?: () => void;
  onOpenSettings: () => void;
  onOpenAbout: () => void;
}

export const SplashScreenModal: React.FC<SplashScreenModalProps> = ({
  isOpen,
  onClose,
  onNewBlueprint,
  onLoadBlueprint,
  onLoadExample,
  onOpenSettings,
  onOpenAbout,
}) => {
  const [dontShowAgain, setDontShowAgain] = useState(() => {
    return localStorage.getItem('comfylab_hide_splash') === 'true';
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleToggleDontShow = (checked: boolean) => {
    setDontShowAgain(checked);
    if (checked) {
      localStorage.setItem('comfylab_hide_splash', 'true');
    } else {
      localStorage.removeItem('comfylab_hide_splash');
    }
  };

  return (
    <div
      className="modal-overlay"
      style={{ zIndex: 9999 }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        className="modal-content glass-panel"
        style={{
          maxWidth: '540px',
          width: '90%',
          animation: 'scaleUp 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header" style={{ padding: '18px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.4rem' }}>⚡</span>
            <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-color)' }}>
              Welcome to ComfyLAB
            </h3>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close splash screen">
            ✕
          </button>
        </div>

        <div className="modal-body" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Hero Banner */}
          <div
            style={{
              textAlign: 'center',
              padding: '18px 16px',
              borderRadius: '10px',
              background: 'var(--input-bg)',
              border: '1px solid var(--block-border)',
            }}
          >
            <h1
              style={{
                margin: '0 0 4px 0',
                fontSize: '2.2rem',
                fontWeight: 800,
                background: 'var(--logo-gradient)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                letterSpacing: '-0.5px',
              }}
            >
              ComfyLAB
            </h1>
            <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
              <strong>Comf</strong>ortable <strong>L</strong>ab <strong>A</strong>utomation <strong>B</strong>locks
              <span style={{ marginLeft: '8px', opacity: 0.8, fontSize: '0.85rem' }}>v{import.meta.env.VITE_APP_VERSION}</span>
            </div>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-color)', lineHeight: 1.5 }}>
              Visual block-based environment for automating laboratory instruments, data acquisition, and scientific analysis pipelines.
            </p>
          </div>

          {/* Quick Action Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div
              className="splash-card"
              onClick={() => {
                onNewBlueprint();
                onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '14px',
                borderRadius: '8px',
                background: 'var(--dnd-bg)',
                border: '1px solid var(--block-border)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-color)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--block-border)';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <span style={{ fontSize: '1.6rem' }}>📄</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-color)' }}>New Blueprint</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Start a fresh canvas</div>
              </div>
            </div>

            <div
              className="splash-card"
              onClick={() => {
                onLoadBlueprint();
                onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '14px',
                borderRadius: '8px',
                background: 'var(--dnd-bg)',
                border: '1px solid var(--block-border)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-color)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--block-border)';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <span style={{ fontSize: '1.6rem' }}>📂</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-color)' }}>Open Blueprint</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Browse workspace files</div>
              </div>
            </div>

            <div
              className="splash-card"
              onClick={() => {
                if (onLoadExample) onLoadExample();
                onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '14px',
                borderRadius: '8px',
                background: 'var(--dnd-bg)',
                border: '1px solid var(--block-border)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-color)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--block-border)';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <span style={{ fontSize: '1.6rem' }}>🧪</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-color)' }}>Load Example</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Pre-configured workflows</div>
              </div>
            </div>

            <div
              className="splash-card"
              onClick={() => {
                onOpenSettings();
                onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '14px',
                borderRadius: '8px',
                background: 'var(--dnd-bg)',
                border: '1px solid var(--block-border)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-color)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--block-border)';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <span style={{ fontSize: '1.6rem' }}>⚙️</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-color)' }}>Settings</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>VISA & Scripting options</div>
              </div>
            </div>

            <div
              className="splash-card"
              onClick={() => {
                onOpenAbout();
                onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '14px',
                borderRadius: '8px',
                background: 'var(--dnd-bg)',
                border: '1px solid var(--block-border)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-color)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--block-border)';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <span style={{ fontSize: '1.6rem' }}>ℹ️</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-color)' }}>About & License</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>System details & GPLv3</div>
              </div>
            </div>
          </div>
        </div>

        <div
          className="modal-footer"
          style={{
            padding: '14px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
            <input
              type="checkbox"
              checked={dontShowAgain}
              onChange={(e) => handleToggleDontShow(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            Don't show on startup
          </label>
          <button className="button-primary" onClick={onClose} style={{ padding: '8px 20px' }}>
            Get Started 🚀
          </button>
        </div>
      </div>
    </div>
  );
};
