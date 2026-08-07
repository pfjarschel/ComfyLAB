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

import React, { useEffect, useState, useRef } from 'react';
import { useTranslation } from '../../i18n';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

interface QuickStartModalProps {
  onClose: () => void;
}

interface ParsedSection {
  id: string;
  title: string;
  icon: string;
  content: string;
}

export const QuickStartModal: React.FC<QuickStartModalProps> = ({ onClose }) => {
  const { t, i18n } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSection, setActiveSection] = useState('intro');
  const [introContent, setIntroContent] = useState('');
  const [sections, setSections] = useState<ParsedSection[]>([]);
  const [loading, setLoading] = useState(true);
  const bodyRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    const loadMarkdown = async () => {
      setLoading(true);
      try {
        let res = await fetch(`/docs/quick_start_${i18n.language}.md`);
        if (!res.ok) {
          // Fallback to English
          res = await fetch(`/docs/quick_start_en.md`);
        }
        if (!res.ok) {
          throw new Error("Could not load quick start guide");
        }
        const text = await res.text();
        
        // Split by Markdown H2 (## )
        const parts = text.split(/(?=^## )/gm);
        
        // The first part is the intro/title
        const intro = parts.shift() || '';
        setIntroContent(intro);
        
        // Predefined icons to maintain the "look"
        const icons = ['🚀', '⚡', '🔌', '🔄', '🔍', '🛠️', '🎨', '📌', '🚫', '📦', '🧩', '📊', '🔢', '📡', '🔬', '⚙️', '📜', '⬆️', '🎁', '💻', '⌨️'];
        
        const parsedSections: ParsedSection[] = parts.map((part, index) => {
          const lines = part.split('\n');
          const header = lines.shift() || '';
          const title = header.replace(/^##\s+/, '').trim();
          const content = lines.join('\n');
          return {
            id: `sec-${index}`,
            title,
            icon: icons[index] || '📄',
            content
          };
        });
        
        setSections(parsedSections);
      } catch (err) {
        console.error(err);
        setIntroContent("# Error\nFailed to load guide.");
      } finally {
        setLoading(false);
      }
    };
    loadMarkdown();
  }, [i18n.language]);

  const scrollToSection = (id: string) => {
    setActiveSection(id);
    const element = document.getElementById(`qs-section-${id}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const matchesSearch = (text: string) => {
    if (!searchQuery.trim()) return true;
    return text.toLowerCase().includes(searchQuery.toLowerCase());
  };

  return (
    <div
      className="modal-overlay"
      style={{ zIndex: 10000 }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <style>{`
        .qs-markdown-body .qs-card {
          background: var(--block-bg);
          border: 1px solid var(--block-border);
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 24px;
        }
        .qs-markdown-body .qs-section-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
          border-bottom: 1px solid var(--block-border);
          padding-bottom: 12px;
        }
        .qs-markdown-body .qs-icon {
          font-size: 1.5rem;
        }
        .qs-markdown-body h4 {
          margin: 0;
          font-size: 1.2rem;
          color: var(--text-color);
        }
        .qs-section-content h3 {
          color: var(--text-color);
          margin-top: 1.5em;
          margin-bottom: 0.5em;
        }
        .qs-section-content p {
          margin-top: 0;
          margin-bottom: 1em;
          color: var(--text-color);
          line-height: 1.6;
        }
        .qs-section-content ul, .qs-section-content ol {
          margin-bottom: 1em;
          padding-left: 20px;
        }
        .qs-section-content li {
          margin-bottom: 0.5em;
        }
        .qs-section-content pre {
          background: var(--dnd-bg);
          padding: 12px;
          border-radius: 6px;
          overflow-x: auto;
          border: 1px solid var(--block-border);
        }
        .qs-section-content code {
          background: var(--dnd-bg);
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 0.9em;
          border: 1px solid var(--block-border);
        }
        .qs-section-content pre code {
          padding: 0;
          border: none;
          background: transparent;
        }
        .qs-section-content table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 1em;
        }
        .qs-section-content th, .qs-section-content td {
          border: 1px solid var(--block-border);
          padding: 8px 12px;
          text-align: left;
        }
        .qs-section-content th {
          background: var(--dnd-bg);
          font-weight: 600;
        }
      `}</style>
      <div
        className="modal-content glass-panel"
        style={{
          maxWidth: '960px',
          width: '92vw',
          height: '85vh',
          display: 'flex',
          flexDirection: 'column',
          animation: 'scaleUp 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="modal-header"
          style={{
            padding: '16px 24px',
            borderBottom: '1px solid var(--block-border)',
            background: 'var(--input-bg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '1.6rem' }}>📖</span>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-color)' }}>
                {t('topbar.quickStart', 'ComfyLAB Quick Start Guide')}
              </h3>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {t('quickStart.subtitle', 'Complete reference & user manual for visual lab automation')}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Search Filter Input */}
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                placeholder={t('common.search', 'Search guide...')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  padding: '6px 12px 6px 30px',
                  borderRadius: '20px',
                  border: '1px solid var(--block-border)',
                  background: 'var(--dnd-bg)',
                  color: 'var(--text-color)',
                  fontSize: '0.85rem',
                  width: '180px',
                  outline: 'none',
                }}
              />
              <span
                style={{
                  position: 'absolute',
                  left: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  fontSize: '0.85rem',
                  opacity: 0.6,
                }}
              >
                🔍
              </span>
            </div>

            <button className="modal-close-btn" onClick={onClose} title="Close guide">
              ✕
            </button>
          </div>
        </div>

        {/* Modal Main Content (Split Layout: Nav Sidebar + Main Body) */}
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Quick Nav Sidebar */}
          <div
            style={{
              width: '240px',
              minWidth: '240px',
              borderRight: '1px solid var(--block-border)',
              background: 'var(--input-bg)',
              padding: '12px 8px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            <div
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                padding: '4px 8px 8px 8px',
              }}
            >
              Table of Contents
            </div>
            {sections.map((sec) => {
              const isActive = activeSection === sec.id;
              return (
                <button
                  key={sec.id}
                  onClick={() => scrollToSection(sec.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: 'none',
                    background: isActive ? 'var(--accent-color)' : 'transparent',
                    color: isActive ? '#ffffff' : 'var(--text-color)',
                    fontSize: '0.82rem',
                    fontWeight: isActive ? 600 : 400,
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) e.currentTarget.style.background = 'var(--dnd-bg)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <span style={{ fontSize: '0.95rem' }}>{sec.icon}</span>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {sec.title}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Guide Content Scroll Area */}
          <div
            ref={bodyRef}
            className="qs-markdown-body"
            style={{
              flex: 1,
              padding: '24px 32px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '28px',
              lineHeight: 1.6,
              color: 'var(--text-color)',
            }}
          >
            {loading ? (
              <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                {t('loadExampleModal.loading', 'Loading guide...')}
              </div>
            ) : (
              <>
                {matchesSearch(introContent) && (
                  <div className="qs-intro" style={{ marginBottom: '10px' }}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{introContent}</ReactMarkdown>
                  </div>
                )}
                
                {sections.map(sec => {
                  if (!matchesSearch(sec.title + ' ' + sec.content)) return null;
                  
                  return (
                    <section id={`qs-section-${sec.id}`} key={sec.id} className="qs-card">
                      <div className="qs-section-header">
                        <span className="qs-icon">{sec.icon}</span>
                        <h4>{sec.title}</h4>
                      </div>
                      <div className="qs-section-content markdown-styles">
                        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{sec.content}</ReactMarkdown>
                      </div>
                    </section>
                  );
                })}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
