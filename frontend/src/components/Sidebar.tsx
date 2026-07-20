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

import { useState } from 'react';

interface SidebarNode {
  type: string;
  name: string;
  icon: string;
  description: string;
}

interface SidebarCategory {
  directNodes: SidebarNode[];
  subcategories: Record<string, SidebarNode[]>;
}

interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  filteredGrouped: Record<string, SidebarCategory>;
  onReloadRegistry: () => void;
}

export const Sidebar = ({
  sidebarOpen,
  setSidebarOpen,
  searchQuery,
  setSearchQuery,
  filteredGrouped,
  onReloadRegistry,
}: SidebarProps) => {
  const [expandedCats, setExpandedCats] = useState<Record<string, boolean>>({});
  const [expandedSubcats, setExpandedSubcats] = useState<Record<string, boolean>>({});

  const toggleCat = (catName: string) => {
    setExpandedCats((prev) => ({ ...prev, [catName]: !prev[catName] }));
  };

  const toggleSubcat = (catName: string, subcatName: string) => {
    const key = `${catName}/${subcatName}`;
    setExpandedSubcats((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  if (!sidebarOpen) return null;

  return (
    <div className="sidebar-container glass-panel nodrag nowheel">
      <div className="sidebar-header">
        <h3>Node Library</h3>
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            className="button-secondary"
            onClick={onReloadRegistry}
            title="Refresh node library"
            style={{ height: '30px', padding: '0 8px', fontSize: '0.8rem' }}
          >
            <span>🔄</span>
          </button>
          <button 
            className="button-secondary library-toggle-btn active"
            onClick={() => setSidebarOpen(false)}
            title="Hide Node Library"
            style={{ height: '30px', padding: '0 10px', fontSize: '0.8rem', gap: '6px' }}
          >
            <span>📚</span>
            <span>Hide</span>
          </button>
        </div>
      </div>
      <div className="sidebar-search-container">
        <input
          type="text"
          placeholder="Search nodes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="sidebar-search-input"
        />
        {searchQuery && (
          <button 
            className="sidebar-search-clear"
            onClick={() => setSearchQuery('')}
            title="Clear search"
          >
            ✕
          </button>
        )}
      </div>
      <div className="sidebar-content">
        {Object.entries(filteredGrouped).length === 0 && (
          <div style={{ color: '#64748b', fontSize: '0.85rem', textAlign: 'center', marginTop: '20px' }}>
            No nodes match your search.
          </div>
        )}
        {Object.entries(filteredGrouped)
          .sort((a, b) => {
            if (a[0].toLowerCase() === 'user') return 1;
            if (b[0].toLowerCase() === 'user') return -1;
            return a[0].localeCompare(b[0]);
          })
          .map(([mainCat, catData]) => {
          const isCatExpanded = searchQuery.trim() !== '' || expandedCats[mainCat];
          return (
            <div key={mainCat}>
              {mainCat.toLowerCase() === 'user' && <div className="sidebar-category-separator" />}
              <div className="sidebar-category-group">
              <div 
                className="sidebar-category-header"
                onClick={() => toggleCat(mainCat)}
              >
                <span className="expand-icon">{isCatExpanded ? '▼' : '▶'}</span>
                <span className="category-title">{mainCat}</span>
              </div>
              
              {isCatExpanded && (
                <div className="sidebar-category-content">
                  {/* Direct Nodes */}
                  {[...catData.directNodes]
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((node) => (
                    <div 
                      key={node.type} 
                      className="dndnode" 
                      onDragStart={(e) => { e.dataTransfer.setData('application/reactflow', node.type); }} 
                      draggable
                      title={node.description}
                    >
                      <span style={{ fontSize: '0.95rem' }}>{node.icon || '⚙️'}</span> 
                      <span>{node.name}</span>
                    </div>
                  ))}

                  {/* Subcategories */}
                  {Object.entries(catData.subcategories)
                    .sort((a, b) => a[0].localeCompare(b[0]))
                    .map(([subCat, subNodes]) => {
                    const subcatKey = `${mainCat}/${subCat}`;
                    const isSubExpanded = searchQuery.trim() !== '' || expandedSubcats[subcatKey];
                    return (
                      <div key={subCat} className="sidebar-subcategory-group">
                        <div 
                          className="sidebar-subcategory-header"
                          onClick={() => toggleSubcat(mainCat, subCat)}
                        >
                          <span className="expand-icon">{isSubExpanded ? '▼' : '▶'}</span>
                          <span className="subcategory-title">{subCat}</span>
                        </div>

                        {isSubExpanded && (
                          <div className="sidebar-subcategory-content">
                            {[...subNodes]
                              .sort((a, b) => a.name.localeCompare(b.name))
                              .map((node) => (
                              <div 
                                key={node.type} 
                                className="dndnode" 
                                onDragStart={(e) => { e.dataTransfer.setData('application/reactflow', node.type); }} 
                                draggable
                                title={node.description}
                              >
                                <span style={{ fontSize: '0.95rem' }}>{node.icon || '⚙️'}</span> 
                                <span>{node.name}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
