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

import React, { useState } from 'react';
import { AboutModal } from './modals/AboutModal';
import { QuickStartModal } from './modals/QuickStartModal';
import { useTranslation, SUPPORTED_LANGUAGES, type Language } from '../i18n';

interface TopBarProps {
  menuOpen: boolean;
  setMenuOpen: (open: boolean) => void;
  currentBlueprintName: string;
  isDirty: boolean;
  workspacePath: string;
  workspaceInput: string;
  setWorkspaceInput: (path: string) => void;
  editingWorkspace: boolean;
  setEditingWorkspace: (editing: boolean) => void;
  handleSetWorkspace: () => void;
  isRunning: boolean;
  isPaused: boolean;
  runningTabName: string;
  blocksCount: number;
  selectedBlocksCount: number;
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
  liteMode?: boolean;
  onToggleLiteMode?: () => void;
  menuContainerRef: React.RefObject<HTMLDivElement | null>;

  // Callbacks
  onNewBlueprint: () => void;
  onSaveBlueprint: () => void;
  onOverwriteBlueprint?: () => void;
  onLoadBlueprint: () => void;
  onLoadExample?: () => void;
  onClearTemporaryFiles: () => void;
  onClearPersistentStates: () => void;
  onDownloadBlueprint: () => void;
  onUploadBlueprintClick: () => void;
  onUploadFileClick: () => void;
  onOpenSettings: () => void;
  onOpenSplash?: () => void;
  onOpenAbout?: () => void;
  onOpenQuickStart?: () => void;
  onGroupCluster: () => void;
  onRun: () => void;
  onPause: () => void;
  onResume: () => void;
  onAbort: () => void;
  onImportPackage: () => void;
}

export const TopBar = ({
  menuOpen,
  setMenuOpen,
  currentBlueprintName,
  isDirty,
  workspacePath,
  workspaceInput,
  setWorkspaceInput,
  editingWorkspace,
  setEditingWorkspace,
  handleSetWorkspace,
  isRunning,
  isPaused,
  runningTabName,
  blocksCount,
   
  theme,
  setTheme,
  liteMode,
  onToggleLiteMode,
  menuContainerRef,

  onNewBlueprint,
  onSaveBlueprint,
  onOverwriteBlueprint,
  onLoadBlueprint,
  onLoadExample,
  onClearTemporaryFiles,
  onClearPersistentStates,
  onDownloadBlueprint,
  onUploadBlueprintClick,
  onUploadFileClick,
  onOpenSettings,
  onOpenSplash,
  onOpenAbout,
  onOpenQuickStart,
   
  onRun,
  onPause,
  onResume,
  onAbort,
  onImportPackage,
}: TopBarProps) => {
  const [showAboutModal, setShowAboutModal] = useState(false);
  const [showQuickStartModal, setShowQuickStartModal] = useState(false);
  const { t, i18n } = useTranslation();

  return (
    <>
      {showAboutModal && <AboutModal onClose={() => setShowAboutModal(false)} />}
      {showQuickStartModal && <QuickStartModal onClose={() => setShowQuickStartModal(false)} />}
      <div className="top-bar">
      {/* Left section: Hamburger, Settings, Sidebar toggle, Workspace */}
      <div className="top-bar-left">
        <div className="hamburger-menu-container" ref={menuContainerRef as any}>
          <button 
            className="button-secondary"
            onClick={() => setMenuOpen(!menuOpen)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minWidth: '38px',
              height: '38px',
              borderRadius: '8px',
              fontSize: '1.2rem'
            }}
            title={t('topbar.fileMenu', 'File Menu')}
          >
            ☰
          </button>
          {menuOpen && (
            <div className="hamburger-dropdown glass-panel">
              <button onClick={onNewBlueprint}>
                <span>📄</span> {t('topbar.newBlueprint', 'New Blueprint')}
              </button>
              <button onClick={onSaveBlueprint} disabled={blocksCount === 0}>
                <span>💾</span> {t('topbar.saveBlueprint', 'Save Blueprint')}
              </button>
              {currentBlueprintName && onOverwriteBlueprint && (
                <button onClick={onOverwriteBlueprint} disabled={blocksCount === 0}>
                  <span>💾</span> {t('topbar.overwriteBlueprint', 'Overwrite Blueprint')}
                </button>
              )}
              <button onClick={onLoadBlueprint}>
                <span>📂</span> {t('topbar.loadBlueprint', 'Load Blueprint')}
              </button>
              {onLoadExample && (
                <button onClick={() => { setMenuOpen(false); onLoadExample(); }}>
                  <span>🧪</span> {t('topbar.loadExample', 'Load Example')}
                </button>
              )}
              <button onClick={onClearTemporaryFiles}>
                <span>🧹</span> {t('topbar.clearTempFiles', 'Clear Temporary Files')}
              </button>
              <button onClick={onClearPersistentStates}>
                <span>🧹</span> {t('topbar.clearPersistentStates', 'Clear Persistent States')}
              </button>
              <button onClick={onDownloadBlueprint} disabled={blocksCount === 0}>
                <span>📥</span> {t('topbar.downloadBlueprint', 'Download Blueprint')}
              </button>
              <button onClick={onUploadBlueprintClick}>
                <span>📤</span> {t('topbar.uploadBlueprint', 'Upload Blueprint')}
              </button>
              <button onClick={onUploadFileClick}>
                <span>📁</span> {t('topbar.uploadFile', 'Upload File')}
              </button>
              <button onClick={() => { setMenuOpen(false); onOpenQuickStart ? onOpenQuickStart() : setShowQuickStartModal(true); }}>
                <span>📖</span> {t('topbar.quickStart', 'Quick Start Guide')}
              </button>
              {onOpenSplash && (
                <button onClick={() => { setMenuOpen(false); onOpenSplash(); }}>
                  <span>⚡</span> {t('topbar.welcomeSplash', 'Welcome Splash Screen')}
                </button>
              )}
            </div>
          )}
        </div>

        <button
          className="button-secondary"
          onClick={onOpenSettings}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '8px',
            fontSize: '1.1rem',
            minWidth: '38px',
            height: '38px',
            borderRadius: '8px'
          }}
          title={t('topbar.globalSettings', 'Global Settings')}
        >
          ⚙️
        </button>

        <div className="filename-indicator-container">
          <span className="filename-label">{t('topbar.blueprint', 'Blueprint:')}</span>
          <span className="filename-value">
            {(!currentBlueprintName || currentBlueprintName === 'Untitled') ? t('topbar.untitled', 'Untitled') : currentBlueprintName}
            {isDirty && <span className="filename-dirty-star">*</span>}
          </span>
        </div>

        <div className="workspace-indicator-container">
          <span className="workspace-label">{t('topbar.workspace', 'Workspace:')}</span>
          <div className="workspace-indicator" style={{ height: '38px' }}>
            {editingWorkspace ? (
              <>
                <input
                  type="text"
                  value={workspaceInput}
                  onChange={(e) => setWorkspaceInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSetWorkspace();
                    if (e.key === 'Escape') setEditingWorkspace(false);
                  }}
                  placeholder={t('topbar.workspacePlaceholder', '/path/to/workspace')}
                  className="workspace-input"
                  autoFocus
                />
                <button className="button-secondary" onClick={handleSetWorkspace} style={{ padding: '4px 8px', fontSize: '0.75rem' }}>
                  ✓
                </button>
                <button className="button-secondary" onClick={() => setEditingWorkspace(false)} style={{ padding: '4px 8px', fontSize: '0.75rem' }}>
                  ✕
                </button>
              </>
            ) : (
              <span
                className="workspace-path"
                onClick={() => { setWorkspaceInput(workspacePath); setEditingWorkspace(true); }}
                title={t('topbar.clickToChangeWorkspace', 'Click to change workspace')}
              >
                📁 {workspacePath || 'Loading...'}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Middle section: Run/Abort + Group into Cluster */}
      <div className="top-bar-middle" style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
        {isRunning ? (
          <>
            <span className="running-tab-indicator" style={{ marginRight: '10px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {t('topbar.running', 'Running:')} <strong>{(!runningTabName || runningTabName === 'Untitled') ? t('topbar.untitled', 'Untitled') : runningTabName}</strong>
            </span>
            {isPaused ? (
              <button 
                className="button-primary run-btn paused" 
                onClick={onResume} 
                style={{ height: '38px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="#ffffff" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
                  <path d="M8 5v14l11-7z" />
                </svg>
                {t('topbar.paused', 'Paused')}
              </button>
            ) : (
              <button 
                className="button-primary run-btn" 
                onClick={onPause} 
                style={{ height: '38px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="#ffffff" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
                  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                </svg>
                {t('topbar.pause', 'Pause')}
              </button>
            )}
            <button 
              className="button-primary run-btn abort" 
              onClick={onAbort} 
              style={{ height: '38px', borderRadius: '8px' }}
            >
              {t('topbar.stop', '🛑 Stop')}
            </button>
          </>
        ) : (
          <button 
            className="button-primary run-btn" 
            onClick={onRun} 
            disabled={blocksCount === 0}
            style={{ height: '38px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="#10b981" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
              <path d="M8 5v14l11-7z" />
            </svg>
            {t('topbar.runBlueprint', 'Run Blueprint')}
          </button>
        )}


      </div>

      {/* Right section: Theme and Title */}
      <div className="top-bar-right" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {(currentBlueprintName.startsWith('.temp/') || currentBlueprintName.includes('.temp/')) && (
          <button
            className="button-secondary"
            onClick={onImportPackage}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '38px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              padding: '0 12px',
              border: '1px solid var(--button-secondary-border)',
              background: 'var(--button-secondary-bg)',
              fontWeight: 600
            }}
            title={t('topbar.importPackageTitle', 'Import package zip permanently to workspace')}
          >
            {t('topbar.importPackage', '📦 Import Package')}
          </button>
        )}
        <div className="language-selector-container">
          <select
            value={i18n.language}
            onChange={(e) => i18n.changeLanguage(e.target.value as Language)}
            className="button-secondary"
            style={{
              height: '38px',
              borderRadius: '8px',
              padding: '0 8px',
              fontSize: '0.85rem',
              fontWeight: 500,
              cursor: 'pointer',
              border: '1px solid var(--button-secondary-border)',
              background: 'var(--button-secondary-bg)',
              color: 'var(--text-primary)'
            }}
            title={t('topbar.language', 'Language')}
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code} style={{ background: 'var(--bg-panel)', color: 'var(--text-primary)' }}>
                {lang.flag} {lang.label}
              </option>
            ))}
          </select>
        </div>
        {onToggleLiteMode && (
          <button
            className={`button-secondary ${liteMode ? 'control-btn-active' : ''}`}
            onClick={onToggleLiteMode}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minWidth: '38px',
              height: '38px',
              borderRadius: '8px',
              fontSize: '1.1rem',
              padding: '0',
              border: liteMode ? '1px solid #3b82f6' : '1px solid var(--button-secondary-border)',
              background: liteMode ? 'rgba(59, 130, 246, 0.2)' : 'var(--button-secondary-bg)',
              color: liteMode ? '#60a5fa' : 'inherit'
            }}
            title={liteMode ? t('topbar.liteModeOn', 'Lite Mode: ON — Click to disable') : t('topbar.liteModeOff', 'Lite Mode: OFF — Click to enable (reduces visual effects for low-power devices)')}
          >
            ⚡
          </button>
        )}
        <button
          className="button-secondary"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minWidth: '38px',
            height: '38px',
            borderRadius: '8px',
            fontSize: '1.1rem',
            padding: '0',
            border: '1px solid var(--button-secondary-border)',
            background: 'var(--button-secondary-bg)'
          }}
          title={theme === 'dark' ? t('topbar.switchToLight', 'Switch to Light Mode') : t('topbar.switchToDark', 'Switch to Dark Mode')}
        >
          {theme === 'dark' ? '🌙' : '☀️'}
        </button>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <h1 className="logo-title" style={{ margin: 0 }}>
            <a href="https://github.com/pfjarschel/ComfyLAB" target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'none' }} title="Visit ComfyLAB on GitHub">
              ComfyLAB
            </a> <span style={{ fontSize: '0.8em', opacity: 0.8 }}>v{import.meta.env.VITE_APP_VERSION}</span>
          </h1>
          <button
            onClick={() => onOpenQuickStart ? onOpenQuickStart() : setShowQuickStartModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              padding: '0',
              border: 'none',
              background: 'transparent',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              opacity: 0.8
            }}
            title={t('topbar.quickStart', 'Quick Start Guide')}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </button>
          <button
            onClick={() => onOpenAbout ? onOpenAbout() : setShowAboutModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              padding: '0',
              border: 'none',
              background: 'transparent',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              opacity: 0.8
            }}
            title={t('topbar.about', 'About ComfyLAB')}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </button>
        </div>
      </div>
    </div>
    </>
  );
};
