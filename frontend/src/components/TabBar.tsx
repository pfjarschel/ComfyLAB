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

import React from 'react';

interface Tab {
  id: string;
  name: string;
  isDirty: boolean;
}

interface TabBarProps {
  tabs: Tab[];
  activeTabId: string;
  runningTabId: string | null;
  isDirty: boolean;
  switchTab: (id: string) => void;
  closeTab: (id: string, e: React.MouseEvent) => void;
  addTab: () => void;
}

export const TabBar = ({
  tabs,
  activeTabId,
  runningTabId,
  isDirty,
  switchTab,
  closeTab,
  addTab,
}: TabBarProps) => {
  return (
    <div className="tab-bar glass-panel">
      <div className="tabs-container">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTabId;
          const isTabRunning = tab.id === runningTabId;
          const displayDirty = tab.id === activeTabId ? isDirty : tab.isDirty;
          return (
            <div
              key={tab.id}
              className={`tab-item ${isActive ? 'active' : ''} ${isTabRunning ? 'running' : ''}`}
              onClick={() => switchTab(tab.id)}
            >
              {isTabRunning && (
                <span className="tab-running-dot" title="Running blueprint" />
              )}
              <span className="tab-title">
                {tab.name}
                {displayDirty && <span className="tab-dirty-star">*</span>}
              </span>
              {displayDirty && (
                <span className="tab-dirty-dot" title="Unsaved changes" />
              )}
              <button
                className="tab-close-btn"
                onClick={(e) => closeTab(tab.id, e)}
                title="Close Tab"
              >
                ✕
              </button>
            </div>
          );
        })}
        <button
          className="add-tab-btn"
          onClick={addTab}
          title="Add New Tab"
        >
          ＋
        </button>
      </div>
    </div>
  );
};
