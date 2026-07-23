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

export interface SidebarNode {
  type: string;
  name: string;
  icon: string;
  description: string;
}

export interface SidebarCategoryNode {
  directNodes: SidebarNode[];
  children: Record<string, SidebarCategoryNode>;
}

interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  filteredTree: Record<string, SidebarCategoryNode>;
  onReloadRegistry: () => void;
}

interface CategoryTreeItemProps {
  catName: string;
  path: string;
  node: SidebarCategoryNode;
  level: number;
  searchQuery: string;
  expandedMap: Record<string, boolean>;
  toggleExpand: (path: string) => void;
}

const CategoryTreeItem = ({
  catName,
  path,
  node,
  level,
  searchQuery,
  expandedMap,
  toggleExpand,
}: CategoryTreeItemProps) => {
  const isExpanded = searchQuery.trim() !== '' || expandedMap[path];
  const isTopLevel = level === 0;
  const isUserCat = isTopLevel && catName.toLowerCase() === 'user';

  const childEntries = Object.entries(node.children).sort((a, b) => a[0].localeCompare(b[0]));
  const sortedDirectNodes = [...node.directNodes].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div>
      {isUserCat && <div className="sidebar-category-separator" />}
      <div className={isTopLevel ? "sidebar-category-group" : "sidebar-subcategory-group"}>
        <div 
          className={isTopLevel ? "sidebar-category-header" : "sidebar-subcategory-header"}
          onClick={() => toggleExpand(path)}
        >
          <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
          <span className={isTopLevel ? "category-title" : "subcategory-title"}>{catName}</span>
        </div>

        {isExpanded && (
          <div className={isTopLevel ? "sidebar-category-content" : "sidebar-subcategory-content"}>
            {/* Direct Blocks at this level */}
            {sortedDirectNodes.map((block) => (
              <div 
                key={block.type} 
                className="dndblock" 
                onDragStart={(e) => { e.dataTransfer.setData('application/reactflow', block.type); }} 
                draggable
                title={block.description}
              >
                <span style={{ fontSize: '0.95rem' }}>{block.icon || '⚙️'}</span> 
                <span>{block.name}</span>
              </div>
            ))}

            {/* Child subcategories */}
            {childEntries.map(([childName, childNode]) => (
              <CategoryTreeItem
                key={childName}
                catName={childName}
                path={`${path}/${childName}`}
                node={childNode}
                level={level + 1}
                searchQuery={searchQuery}
                expandedMap={expandedMap}
                toggleExpand={toggleExpand}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export const Sidebar = ({
  sidebarOpen,
  setSidebarOpen,
  searchQuery,
  setSearchQuery,
  filteredTree,
  onReloadRegistry,
}: SidebarProps) => {
  const [expandedMap, setExpandedMap] = useState<Record<string, boolean>>({});

  const toggleExpand = (path: string) => {
    setExpandedMap((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  if (!sidebarOpen) return null;

  const topLevelEntries = Object.entries(filteredTree).sort((a, b) => {
    if (a[0].toLowerCase() === 'user') return 1;
    if (b[0].toLowerCase() === 'user') return -1;
    return a[0].localeCompare(b[0]);
  });

  return (
    <div className="sidebar-container glass-panel nodrag nowheel">
      <div className="sidebar-header">
        <h3>Block Library</h3>
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            className="button-secondary"
            onClick={onReloadRegistry}
            title="Refresh block library"
            style={{ height: '30px', padding: '0 8px', fontSize: '0.8rem' }}
          >
            <span>🔄</span>
          </button>
          <button 
            className="button-secondary library-toggle-btn active"
            onClick={() => setSidebarOpen(false)}
            title="Hide Block Library"
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
          placeholder="Search blocks..."
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
        {topLevelEntries.length === 0 && (
          <div style={{ color: '#64748b', fontSize: '0.85rem', textAlign: 'center', marginTop: '20px' }}>
            No blocks match your search.
          </div>
        )}
        {topLevelEntries.map(([catName, node]) => (
          <CategoryTreeItem
            key={catName}
            catName={catName}
            path={catName}
            node={node}
            level={0}
            searchQuery={searchQuery}
            expandedMap={expandedMap}
            toggleExpand={toggleExpand}
          />
        ))}
      </div>
    </div>
  );
};

