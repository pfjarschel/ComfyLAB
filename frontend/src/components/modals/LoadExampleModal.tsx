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
import axios from 'axios';

interface ExampleItem {
  filename: string;
  path: string;
  size: number;
  modified: number;
}

interface LoadExampleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoadExampleByName: (filename: string) => void;
  BACKEND_URL: string;
}

export const LoadExampleModal: React.FC<LoadExampleModalProps> = ({
  isOpen,
  onClose,
  onLoadExampleByName,
  BACKEND_URL,
}) => {
  const [examples, setExamples] = useState<ExampleItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchExamples();
    }
  }, [isOpen]);

  const fetchExamples = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${BACKEND_URL}/workspace/examples`);
      setExamples(res.data.examples || []);
    } catch (err: any) {
      setError('Failed to fetch built-in example blueprints.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" style={{ zIndex: 1000 }} onClick={onClose}>
      <div className="modal-content glass-panel" style={{ width: '480px', maxWidth: '90%' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-color)' }}>
            <span>🧪</span> Built-in Example Blueprints
          </h3>
          <button className="modal-close-btn" onClick={onClose} title="Close">✕</button>
        </div>

        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '20px', maxHeight: '380px', overflowY: 'auto' }}>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
            Explore pre-configured example blueprints. Loading an example allows you to run, inspect, and modify the workflow. Saving will prompt you to save a copy into your active workspace.
          </p>

          {loading ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '20px' }}>
              Loading examples...
            </div>
          ) : error ? (
            <div style={{ color: '#ef4444', fontSize: '0.85rem', textAlign: 'center', padding: '16px' }}>
              {error}
            </div>
          ) : examples.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '20px', fontStyle: 'italic' }}>
              No example blueprints found in the examples folder.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {examples.map((ex) => {
                const displayName = ex.filename.replace(/\.json$/, '').replace(/_/g, ' ');
                return (
                  <div
                    key={ex.filename}
                    className="blueprint-list-item"
                    onClick={() => {
                      onLoadExampleByName(ex.filename);
                      onClose();
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 14px',
                      background: 'var(--dnd-bg)',
                      border: '1px solid var(--block-border)',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'var(--accent-color)';
                      e.currentTarget.style.transform = 'translateY(-1px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--block-border)';
                      e.currentTarget.style.transform = 'none';
                    }}
                  >
                    <span style={{ fontSize: '1.4rem' }}>🧪</span>
                    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                      <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-color)', textTransform: 'capitalize' }}>
                        {displayName}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {ex.filename}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.8rem', color: 'var(--accent-color)', fontWeight: 600 }}>
                      Open →
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ padding: '12px 20px', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="button-secondary" onClick={onClose} style={{ width: '100px' }}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
