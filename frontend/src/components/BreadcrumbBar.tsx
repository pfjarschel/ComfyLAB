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

import { useContext } from 'react';
import { RegistryContext } from '../context/RegistryContext';

interface BreadcrumbLevel {
  breadcrumbLabel: string;
  type: string;
}

interface BreadcrumbBarProps {
  levels: BreadcrumbLevel[];
  currentIndex: number;
  onNavigate: (index: number) => void;
}

export const BreadcrumbBar = ({ levels, currentIndex, onNavigate }: BreadcrumbBarProps) => {
  const nodeRegistry = useContext(RegistryContext) as Record<string, any> | null;

  if (levels.length <= 1) return null;

  return (
    <div className="breadcrumb-bar nodrag nowheel">
      {levels.map((level, i) => {
        const isLast = i === levels.length - 1;
        const layout = nodeRegistry?.[level.type];
        const icon = layout?.icon || '🏠';
        const name = level.breadcrumbLabel || layout?.name || level.type;

        return (
          <span key={i} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {i > 0 && (
              <span className="breadcrumb-separator" style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                ›
              </span>
            )}
            <span
              className={`breadcrumb-segment ${i === currentIndex ? 'active' : ''} ${isLast ? 'last' : ''}`}
              onClick={() => onNavigate(i)}
              style={{
                cursor: i < currentIndex ? 'pointer' : 'default',
                fontWeight: i === currentIndex ? 600 : 400,
                color: i === currentIndex ? 'var(--accent-color)' : 'var(--text-muted)',
                padding: '4px 8px',
                borderRadius: '4px',
                fontSize: '0.8rem',
                transition: 'all 0.15s ease',
                userSelect: 'none',
              }}
              onMouseEnter={(e) => {
                if (i < currentIndex) {
                  e.currentTarget.style.background = 'var(--dnd-hover-bg)';
                  e.currentTarget.style.color = 'var(--accent-color)';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.color = i === currentIndex ? 'var(--accent-color)' : 'var(--text-muted)';
              }}
            >
              {icon && <span style={{ fontSize: '0.85rem' }}>{icon}</span>}
              {name}
            </span>
          </span>
        );
      })}
    </div>
  );
};
