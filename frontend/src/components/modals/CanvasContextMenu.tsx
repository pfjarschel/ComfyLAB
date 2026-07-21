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

import { useRef, useEffect, useState } from 'react';
interface CanvasContextMenuProps {
  contextMenu: {
    show: boolean;
    x: number;
    y: number;
    clientX: number;
    clientY: number;
    type: 'pane' | 'block' | 'edge' | 'selection';
    targetId?: string | null;
  } | null;
  contextMenuSearch: string;
  setContextMenuSearch: (value: string) => void;
  blockRegistry: any;
  isLocked: boolean;
  snapToGrid: boolean;
  showAnnotations: boolean;
  selectedBlockIds: Set<string>;
  clipboardBlocksCount: number;
  blocks: any[];
  edges: any[];
  onClose: () => void;
  onAddNodeAtClientPosition: (type: string, clientX: number, clientY: number) => void;
  onPaste: (coords?: { x: number; y: number }) => void;
  onResetZoom: () => void;
  onFitView: () => void;
  onLayout: () => void;
  onToggleLocked: () => void;
  onToggleSnap: () => void;
  onToggleAnnotations: () => void;
  onClearCanvas: () => void;
  onInspectBlock: (id: string) => void;
  onCopyBlock: () => void;
  onDuplicateBlock: () => void;
  onDeleteBlock: (id: string) => void;
  onDeleteEdge: (id: string) => void;
  onEditScript: (id: string, code: string, action: string) => void;
  onGroupIntoCluster: () => void;
  onClearBlockData: (id: string) => void;
  onClearAllBlocksData: () => void;
  onReplaceBlock: (blockId: string, replacementAction: string) => void;
  onBlockDataChange: (id: string, key: string, value: any) => void;
}



export const CanvasContextMenu = ({
  contextMenu,
  contextMenuSearch,
  setContextMenuSearch,
  blockRegistry,
  isLocked,
  snapToGrid,
  showAnnotations,
  selectedBlockIds,
  clipboardBlocksCount,
  blocks,
  edges,
  onClose,
  onAddNodeAtClientPosition,
  onPaste,
  onResetZoom,
  onFitView,
  onLayout,
  onToggleLocked,
  onToggleSnap,
  onToggleAnnotations,
  onClearCanvas,
  onInspectBlock,
  onCopyBlock,
  onDuplicateBlock,
  onDeleteBlock,
  onDeleteEdge,
  onEditScript,
  onGroupIntoCluster,
  onClearBlockData,
  onClearAllBlocksData,
  onReplaceBlock,
  onBlockDataChange,
}: CanvasContextMenuProps) => {
  const menuRef = useRef<HTMLDivElement>(null);
  const hasClamped = useRef(false);
  const [pos, setPos] = useState({ x: contextMenu?.x ?? 0, y: contextMenu?.y ?? 0 });
  const [submenuDirs, setSubmenuDirs] = useState({ left: false, addTop: false, replaceTop: false });

  // Reset clamp flag and initial position whenever the menu context changes
  useEffect(() => {
    if (!contextMenu) return;
    hasClamped.current = false;
    setPos({ x: contextMenu.x, y: contextMenu.y });
  }, [contextMenu?.clientX, contextMenu?.clientY]);

  // After menu mounts/updates, measure the real rendered size and clamp to viewport
  useEffect(() => {
    if (!contextMenu || !menuRef.current || hasClamped.current) return;
    hasClamped.current = true;
    const el = menuRef.current;
    const rect = el.getBoundingClientRect();
    const margin = 8;
    let x = contextMenu.x;
    let y = contextMenu.y;

    // Flip left if it overflows the right edge
    if (contextMenu.clientX + rect.width + margin > window.innerWidth) {
      x = contextMenu.x - rect.width;
    }
    // Flip up if it overflows the bottom edge
    if (contextMenu.clientY + rect.height + margin > window.innerHeight) {
      y = contextMenu.y - rect.height;
    }
    // Guard: don't let it scroll above the top of the canvas wrapper
    const minY = contextMenu.y - contextMenu.clientY + margin;
    const minX = contextMenu.x - contextMenu.clientX + margin;
    if (y < minY) y = minY;
    if (x < minX) x = minX;

    setPos({ x, y });

    // Calculate smart submenu directions
    const finalScreenY = contextMenu.clientY + (y - contextMenu.y);
    const finalScreenX = contextMenu.clientX + (x - contextMenu.x);

    // Estimate button screen Y positions (Add is top, Replace is bottom)
    const addMenuTopScreenY = finalScreenY;
    const replaceMenuTopScreenY = finalScreenY + rect.height - 40;

    // Submenu max height ~350px, width ~300px
    const addTop = addMenuTopScreenY + 350 > window.innerHeight;
    const replaceTop = replaceMenuTopScreenY + 350 > window.innerHeight;
    const left = finalScreenX + rect.width + 300 > window.innerWidth;

    setSubmenuDirs({ left, addTop, replaceTop });
  });

  if (!contextMenu || !contextMenu.show) return null;

  // Context Menu flat filtered blocks
  const menuSearchQuery = contextMenuSearch.toLowerCase().trim();
  const menuFilteredNodes = Object.entries(blockRegistry || {}).map(([type, nodeSchema]: [string, any]) => ({
    type,
    name: nodeSchema.name || '',
    description: nodeSchema.description || '',
    category: nodeSchema.category || 'Other',
    icon: nodeSchema.icon || '⚙️'
  })).filter(block => {
    return !menuSearchQuery || 
           block.name.toLowerCase().includes(menuSearchQuery) || 
           block.description.toLowerCase().includes(menuSearchQuery) ||
           block.category.toLowerCase().includes(menuSearchQuery);
  }).sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div
      ref={menuRef}
      className="context-menu glass-panel"
      style={{
        position: 'absolute',
        top: pos.y,
        left: pos.x,
        zIndex: 10000,
        visibility: hasClamped.current ? 'visible' : 'hidden',
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {contextMenu.type === 'pane' && (
        <>
          <div className="context-menu-submenu-parent">
            <button className="context-menu-item">
              <span>➕</span> Add Block <span className="submenu-arrow">▶</span>
            </button>
            <div className={`context-menu-submenu glass-panel ${submenuDirs.left ? 'submenu-left' : ''} ${submenuDirs.addTop ? 'submenu-top' : ''}`}>
              <input
                type="text"
                placeholder="Search blocks..."
                autoFocus
                value={contextMenuSearch}
                className="context-menu-search-input"
                onChange={(e) => setContextMenuSearch(e.target.value)}
              />
              <div className="context-menu-block-list">
                {menuFilteredNodes.length === 0 ? (
                  <div className="context-menu-no-results">No blocks found</div>
                ) : (
                  menuFilteredNodes.map((block) => (
                    <button
                      key={block.type}
                      className="context-menu-block-item"
                      onClick={() => {
                        onAddNodeAtClientPosition(block.type, contextMenu.clientX, contextMenu.clientY);
                        onClose();
                      }}
                      title={block.description}
                    >
                      <span className="block-icon">{block.icon}</span>
                      <div className="block-details">
                        <span className="block-name">{block.name}</span>
                        <span className="block-category">{block.category}</span>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
          {clipboardBlocksCount > 0 && !isLocked && (
            <button
              className="context-menu-item"
              onClick={() => {
                onPaste({ x: contextMenu.clientX, y: contextMenu.clientY });
                onClose();
              }}
            >
              <span>📋</span> Paste Block
            </button>
          )}
          <div className="context-menu-divider" />
          <button className="context-menu-item" onClick={() => { onResetZoom(); onClose(); }}>
            <span>🔍</span> Reset Zoom
          </button>
          <button className="context-menu-item" onClick={() => { onFitView(); onClose(); }}>
            <span>🔍</span> Fit View
          </button>
          <button className="context-menu-item" onClick={() => { onLayout(); onClose(); }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '1.25rem', height: '1.25rem' }}>
              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" strokeWidth="2.0" fill="none" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'block' }}>
                <rect x="2" y="9.5" width="6" height="5" rx="1" />
                <rect x="16" y="3" width="6" height="5" rx="1" />
                <rect x="16" y="16" width="6" height="5" rx="1" />
                <path d="M8 12h4M12 5.5h4M12 18.5h4M12 5.5v13" />
              </svg>
            </span>
            Auto-Organize Blocks
          </button>
          <button className="context-menu-item" onClick={() => { onToggleLocked(); onClose(); }}>
            <span>{isLocked ? '🔓' : '🔒'}</span> {isLocked ? 'Unlock Interactivity' : 'Lock Interactivity'}
          </button>
          <button className="context-menu-item" onClick={() => { onToggleSnap(); onClose(); }}>
            <span>🧲</span> {snapToGrid ? 'Disable Grid Snapping' : 'Enable Grid Snapping'}
          </button>
          <button className="context-menu-item" onClick={() => { onToggleAnnotations(); onClose(); }}>
            <span>👁️</span> {showAnnotations ? 'Hide Annotations' : 'Show Annotations'}
          </button>
          <div className="context-menu-divider" />
          <button className="context-menu-item" disabled={isLocked} onClick={() => {
            onClearAllBlocksData();
            onClose();
          }}>
            <span>🧹</span> Clear All Blocks Data
          </button>
          <button className="context-menu-item danger" disabled={isLocked} onClick={() => {
            onClearCanvas();
            onClose();
          }}>
            <span>🗑️</span> Clear Canvas
          </button>
        </>
      )}

      {contextMenu.type === 'block' && (
        <>
          <button className="context-menu-item" onClick={() => { onInspectBlock(contextMenu.targetId!); onClose(); }}>
            <span>ℹ️</span> Inspect Block
          </button>
          <button
            className="context-menu-item"
            onClick={() => {
              const block = blocks.find(n => n.id === contextMenu.targetId);
              const isDisabled = !block?.data?.disabled;
              onBlockDataChange(contextMenu.targetId!, 'disabled', isDisabled);
              onClose();
            }}
          >
            <span>{blocks.find(n => n.id === contextMenu.targetId)?.data?.disabled ? '✅' : '🚫'}</span>{' '}
            {blocks.find(n => n.id === contextMenu.targetId)?.data?.disabled ? 'Enable Block' : 'Disable Block'}
          </button>
          <button 
            className="context-menu-item" 
            onClick={() => {
              const block = blocks.find(n => n.id === contextMenu.targetId);
              const isPersistent = !block?.data?.isPersistent;
              onBlockDataChange(contextMenu.targetId!, 'isPersistent', isPersistent);
              if (isPersistent) {
                onBlockDataChange(contextMenu.targetId!, 'autoClearPersistent', true);
              }
              onClose();
            }}
          >
            <span>{blocks.find(n => n.id === contextMenu.targetId)?.data?.isPersistent ? '🔓' : '🔒'}</span>{' '}
            {blocks.find(n => n.id === contextMenu.targetId)?.data?.isPersistent ? 'Make Transient' : 'Make Persistent'}
          </button>
          <button className="context-menu-item" onClick={() => { onClearBlockData(contextMenu.targetId!); onClose(); }}>
            <span>🧹</span> Clear Block Data
          </button>
          <button className="context-menu-item" onClick={() => { onCopyBlock(); onClose(); }}>
            <span>📄</span> Copy Block
          </button>

          <button className="context-menu-item" onClick={() => { onDuplicateBlock(); onClose(); }}>
            <span>👯</span> Duplicate Block
          </button>
          <button
            className="context-menu-item danger"
            onClick={() => {
              onDeleteBlock(contextMenu.targetId!);
              onClose();
            }}
          >
            <span>🗑️</span> Delete Block
          </button>
          {(() => {
            const block = blocks.find(n => n.id === contextMenu.targetId);
            if (block && block.data?.action && block.data.action.startsWith('script/')) {
              return (
                <>
                  <div className="context-menu-divider" />
                  <button className="context-menu-item" onClick={() => {
                    onEditScript(block.id, block.data.code, block.data.action);
                    onClose();
                  }}>
                    <span>📝</span> Edit Script
                  </button>
                </>
              );
            }
            return null;
          })()}
          {selectedBlockIds.size >= 2 && (
            <>
              <div className="context-menu-divider" />
              <button className="context-menu-item" onClick={() => { onGroupIntoCluster(); onClose(); }}>
                <span>📦</span> Group into Cluster
              </button>
            </>
          )}
          {(() => {
            const block = blocks.find(n => n.id === contextMenu.targetId);
            if (!block || !block.data?.action) return null;

            // 1. Identify Connected Pins
            const targetHandles = Array.from(new Set(edges.filter(e => e.target === block.id).map(e => e.targetHandle).filter(Boolean))) as string[];
            const sourceHandles = Array.from(new Set(edges.filter(e => e.source === block.id).map(e => e.sourceHandle).filter(Boolean))) as string[];
            const totalConnected = targetHandles.length + sourceHandles.length;

            // 2. Score candidates
            const oldAction = block.data?.action || '';
            const oldBaseName = oldAction.split('/').pop()?.toLowerCase() || '';

            const oldSchema = blockRegistry?.[oldAction];
            const oldCategory = oldSchema?.category || '';
            const oldActionParts = oldAction.split('/');
            const oldCategoryFromPath = oldActionParts.slice(0, -1).join('/').toLowerCase();

            // Try filtering strictly by category first
            let candidatesList = Object.entries(blockRegistry || {}).filter(([type, schema]: [string, any]) => {
              if (type === oldAction) return false;
              const candidateCategory = schema.category || '';
              const candidateCategoryFromPath = type.split('/').slice(0, -1).join('/').toLowerCase();
              const isExactCategoryMatch = oldCategory && candidateCategory && oldCategory.toLowerCase() === candidateCategory.toLowerCase();
              const isPathCategoryMatch = oldCategoryFromPath && candidateCategoryFromPath && oldCategoryFromPath === candidateCategoryFromPath;
              return !!(isExactCategoryMatch || isPathCategoryMatch);
            });

            // Fallback if no matching category blocks are found
            if (candidatesList.length === 0) {
              candidatesList = Object.entries(blockRegistry || {}).filter(([type]) => type !== oldAction);
            }

            const candidates = candidatesList.map(([type, schema]: [string, any]) => {
              let score = 0;
              const newBaseName = type.split('/').pop()?.toLowerCase() || '';

              // A. Base Name Match (weight: 10)
              const baseNameMatch = oldBaseName && newBaseName && oldBaseName === newBaseName;
              if (baseNameMatch) {
                score += 10;
              }

              // B. Display Name Match (weight: 5)
              const displayNameMatch = schema.name?.toLowerCase() === oldBaseName;
              if (displayNameMatch) {
                score += 5;
              }

              // C. Category Match (weight: 5)
              const candidateCategory = schema.category || '';
              const candidateCategoryFromPath = type.split('/').slice(0, -1).join('/').toLowerCase();
              const isExactCategoryMatch = oldCategory && candidateCategory && oldCategory.toLowerCase() === candidateCategory.toLowerCase();
              const isPathCategoryMatch = oldCategoryFromPath && candidateCategoryFromPath && oldCategoryFromPath === candidateCategoryFromPath;
              if (isExactCategoryMatch || isPathCategoryMatch) {
                score += 5;
              }

              // D. Pin Signature Match (weight: up to 10)
              let matchedPinsCount = 0;
              let compatibilityText = '';
              let isPerfectMatch = false;

              const regTargetHandles = [...(schema.execIns || []), ...(schema.dataIns || []).map((p: any) => p.name)];
              const regSourceHandles = [...(schema.execOuts || []), ...(schema.dataOuts || []).map((p: any) => p.name)];

              const matchedTargets = targetHandles.filter(h => regTargetHandles.includes(h));
              const matchedSources = sourceHandles.filter(h => regSourceHandles.includes(h));

              matchedPinsCount = matchedTargets.length + matchedSources.length;
              const missingPinsCount = totalConnected - matchedPinsCount;

              if (totalConnected > 0) {
                score += (matchedPinsCount / totalConnected) * 10;
                if (missingPinsCount === 0) {
                  compatibilityText = '100% pin match';
                  isPerfectMatch = true;
                } else {
                  compatibilityText = `prunes ${missingPinsCount} wire${missingPinsCount > 1 ? 's' : ''}`;
                }
              } else {
                compatibilityText = 'no active wires';
                isPerfectMatch = true;
              }

              return {
                type,
                name: schema.name || '',
                description: schema.description || '',
                category: schema.category || 'Other',
                icon: schema.icon || '⚙️',
                score,
                compatibilityText,
                isPerfectMatch,
                baseNameMatch
              };
            });

            // Filter to relevant suggestions, sort by score desc, limit to top 3
            const suggestions = candidates
              .filter(c => c.score >= 5 || (totalConnected > 0 && c.score > 0))
              .sort((a, b) => b.score - a.score)
              .slice(0, 3);

            return (
              <>
                <div className="context-menu-divider" />
                <div className="context-menu-submenu-parent">
                  <button className="context-menu-item">
                    <span>🔄</span> Replace Block <span className="submenu-arrow">▶</span>
                  </button>
                  <div className={`context-menu-submenu glass-panel ${submenuDirs.left ? 'submenu-left' : ''} ${submenuDirs.replaceTop ? 'submenu-top' : ''}`}>
                    <input
                      type="text"
                      placeholder="Search replacement..."
                      autoFocus
                      value={contextMenuSearch}
                      className="context-menu-search-input"
                      onChange={(e) => setContextMenuSearch(e.target.value)}
                    />
                    <div className="context-menu-block-list">
                      {/* Suggestions list */}
                      {suggestions.length > 0 && !contextMenuSearch.trim() && (
                        <>
                          <div className="context-menu-submenu-section-header" style={{
                            padding: '6px 12px 4px 12px',
                            fontSize: '0.7rem',
                            fontWeight: 'bold',
                            color: '#60a5fa',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px',
                            borderBottom: '1px solid rgba(148, 163, 184, 0.08)'
                          }}>
                            💡 Smart Suggestions
                          </div>
                          {suggestions.map((sug) => (
                            <button
                              key={`sug-${sug.type}`}
                              className="context-menu-block-item"
                              onClick={() => {
                                onReplaceBlock(contextMenu.targetId!, sug.type);
                                onClose();
                              }}
                              title={sug.description}
                              style={{ background: 'rgba(96, 165, 250, 0.05)', display: 'flex', alignItems: 'center', gap: '8px', width: '100%', textAlign: 'left' }}
                            >
                              <span className="block-icon">{sug.icon}</span>
                              <div className="block-details" style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
                                <span className="block-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{sug.name}</span>
                                <span className="block-category" style={{ fontSize: '0.7rem', opacity: 0.6 }}>{sug.category}</span>
                              </div>
                              <span style={{
                                fontSize: '0.65rem',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                fontWeight: '600',
                                whiteSpace: 'nowrap',
                                background: sug.isPerfectMatch ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                                color: sug.isPerfectMatch ? '#10b981' : '#f87171',
                                border: sug.isPerfectMatch ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)'
                              }}>
                                {sug.compatibilityText}
                              </span>
                            </button>
                          ))}
                          <div className="context-menu-divider" style={{ margin: '6px 0' }} />
                        </>
                      )}

                      {/* Main filtered library list */}
                      {menuFilteredNodes.filter(n => n.type !== oldAction).length === 0 ? (
                        <div className="context-menu-no-results">No blocks found</div>
                      ) : (
                        menuFilteredNodes.filter(n => n.type !== oldAction).map((regNode) => (
                          <button
                            key={regNode.type}
                            className="context-menu-block-item"
                            onClick={() => {
                              onReplaceBlock(contextMenu.targetId!, regNode.type);
                              onClose();
                            }}
                            title={regNode.description}
                          >
                            <span className="block-icon">{regNode.icon}</span>
                            <div className="block-details">
                              <span className="block-name">{regNode.name}</span>
                              <span className="block-category">{regNode.category}</span>
                            </div>
                          </button>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </>
            );
          })()}
        </>
      )}

      {contextMenu.type === 'selection' && (
        <>
          <button className="context-menu-item" onClick={() => { onCopyBlock(); onClose(); }}>
            <span>📄</span> Copy Blocks
          </button>
          <button className="context-menu-item" onClick={() => { onDuplicateBlock(); onClose(); }}>
            <span>👯</span> Duplicate Blocks
          </button>
          <button
            className="context-menu-item"
            onClick={() => {
              selectedBlockIds.forEach(id => {
                onBlockDataChange(id, 'disabled', true);
              });
              onClose();
            }}
          >
            <span>🚫</span> Disable Blocks
          </button>
          <button
            className="context-menu-item"
            onClick={() => {
              selectedBlockIds.forEach(id => {
                onBlockDataChange(id, 'disabled', false);
              });
              onClose();
            }}
          >
            <span>✅</span> Enable Blocks
          </button>
          <button
            className="context-menu-item danger"
            onClick={() => {
              // Delete all selected blocks
              onDeleteBlock('');
              onClose();
            }}
          >
            <span>🗑️</span> Delete Blocks
          </button>
          {selectedBlockIds.size >= 2 && (
            <>
              <div className="context-menu-divider" />
              <button className="context-menu-item" onClick={() => { onGroupIntoCluster(); onClose(); }}>
                <span>📦</span> Group into Cluster
              </button>
            </>
          )}
        </>
      )}

      {contextMenu.type === 'edge' && (
        <>
          <button
            className="context-menu-item danger"
            onClick={() => {
              onDeleteEdge(contextMenu.targetId!);
              onClose();
            }}
          >
            <span>🗑️</span> Delete Connection
          </button>
        </>
      )}
    </div>
  );
};
