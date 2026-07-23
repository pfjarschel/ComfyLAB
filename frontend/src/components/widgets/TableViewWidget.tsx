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

import React, { useState, useEffect } from 'react';
import { useReactFlow } from '@xyflow/react';
import { ResizablePlotContainer } from '../common/ResizablePlotContainer';

interface TableViewWidgetProps {
  blockId: string;
}

interface TableTelemetryPayload {
  headers?: string[];
  rows?: any[][];
  total_rows?: number;
  total_cols?: number;
  truncated?: boolean;
}

export const TableViewWidget: React.FC<TableViewWidgetProps> = ({ blockId }) => {
  const [tableData, setTableData] = useState<TableTelemetryPayload | null>(null);
  const { getNode } = useReactFlow();

  useEffect(() => {
    const handleTelemetry = (e: Event) => {
      const customEvent = e as CustomEvent;
      const detail = customEvent.detail;
      
      if (detail && (detail.headers !== undefined || detail.rows !== undefined)) {
        setTableData({
          headers: detail.headers || [],
          rows: detail.rows || [],
          total_rows: detail.total_rows ?? (detail.rows ? detail.rows.length : 0),
          total_cols: detail.total_cols ?? (detail.headers ? detail.headers.length : 0),
          truncated: detail.truncated ?? false,
        });
      } else {
        const block = getNode(blockId);
        const results = block?.data?.results as any;
        if (results && (results.headers !== undefined || results.rows !== undefined)) {
          setTableData({
            headers: results.headers || [],
            rows: results.rows || [],
            total_rows: results.total_rows ?? (results.rows ? results.rows.length : 0),
            total_cols: results.total_cols ?? (results.headers ? results.headers.length : 0),
            truncated: results.truncated ?? false,
          });
        }
      }
    };

    const eventName = `telemetry-${blockId}`;
    window.addEventListener(eventName, handleTelemetry);
    return () => window.removeEventListener(eventName, handleTelemetry);
  }, [blockId, getNode]);

  return (
    <ResizablePlotContainer 
      minHeight="140px" 
      background="rgba(15, 23, 42, 0.95)" 
      padding="4px" 
      borderRadius="6px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => {
        if (!tableData || (!tableData.rows?.length && !tableData.headers?.length)) {
          return (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              width: `${width}px`,
              height: `${height}px`,
              color: 'var(--text-muted, #94a3b8)',
              fontSize: '0.8rem',
              gap: '6px',
              userSelect: 'none'
            }}>
              <span style={{ fontSize: '1.4rem' }}>📋</span>
              <span>No Table Data</span>
            </div>
          );
        }

        const headers = tableData.headers || [];
        const rows = tableData.rows || [];
        const totalRows = tableData.total_rows ?? rows.length;
        const totalCols = tableData.total_cols ?? headers.length;

        return (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            width: `${width}px`,
            height: `${height}px`,
            overflow: 'hidden',
            fontFamily: 'Consolas, Monaco, "Courier New", monospace',
            fontSize: '0.75rem',
            color: '#e2e8f0'
          }}>
            {/* Table Header Info Toolbar */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '2px 6px 4px 6px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              fontSize: '0.7rem',
              color: '#94a3b8',
              userSelect: 'none',
              lineHeight: 1.2
            }}>
              <span>
                {totalRows} {totalRows === 1 ? 'row' : 'rows'} × {totalCols} {totalCols === 1 ? 'col' : 'cols'}
              </span>
              {tableData.truncated && (
                <span 
                  style={{
                    color: '#f59e0b',
                    background: 'rgba(245, 158, 11, 0.15)',
                    padding: '1px 5px',
                    borderRadius: '3px',
                    fontWeight: 600,
                    fontSize: '0.65rem'
                  }}
                  title="Dataset exceeds max row/col view limits (1000 x 1000)"
                >
                  ⚠️ Max 1000 limit
                </span>
              )}
            </div>

            {/* Scrollable Table Area */}
            <div 
              className="nodrag"
              style={{
                flex: 1,
                overflow: 'auto',
                position: 'relative',
                background: 'rgba(2, 6, 23, 0.5)'
              }}
            >
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                textAlign: 'left',
                whiteSpace: 'nowrap'
              }}>
                <thead>
                  <tr style={{
                    position: 'sticky',
                    top: 0,
                    background: '#0f172a',
                    zIndex: 2,
                    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.5)'
                  }}>
                    <th style={{
                      position: 'sticky',
                      left: 0,
                      background: '#0f172a',
                      zIndex: 3,
                      padding: '4px 6px',
                      color: '#64748b',
                      fontWeight: 600,
                      borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
                      textAlign: 'center',
                      minWidth: '28px'
                    }}>
                      #
                    </th>
                    {headers.map((head, cIdx) => (
                      <th 
                        key={cIdx}
                        style={{
                          padding: '4px 8px',
                          color: '#38bdf8',
                          fontWeight: 600,
                          borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
                          borderLeft: '1px solid rgba(255, 255, 255, 0.05)'
                        }}
                      >
                        {String(head)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, rIdx) => (
                    <tr 
                      key={rIdx}
                      style={{
                        background: rIdx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.02)',
                        transition: 'background 0.15s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(56, 189, 248, 0.08)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = rIdx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.02)';
                      }}
                    >
                      <td style={{
                        position: 'sticky',
                        left: 0,
                        background: '#0f172a',
                        zIndex: 1,
                        padding: '3px 6px',
                        color: '#64748b',
                        fontSize: '0.68rem',
                        borderRight: '1px solid rgba(255, 255, 255, 0.08)',
                        textAlign: 'center',
                        userSelect: 'none'
                      }}>
                        {rIdx}
                      </td>
                      {row.map((cell, cIdx) => {
                        let cellContent: React.ReactNode = String(cell);
                        let cellColor = '#e2e8f0';

                        if (cell === null || cell === undefined) {
                          cellContent = <span style={{ color: '#64748b', fontStyle: 'italic' }}>null</span>;
                        } else if (typeof cell === 'boolean') {
                          cellColor = cell ? '#4ade80' : '#f87171';
                          cellContent = cell ? 'True' : 'False';
                        } else if (typeof cell === 'number') {
                          cellColor = '#f97316';
                        }

                        return (
                          <td 
                            key={cIdx}
                            style={{
                              padding: '3px 8px',
                              color: cellColor,
                              borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                              borderLeft: '1px solid rgba(255, 255, 255, 0.03)'
                            }}
                          >
                            {cellContent}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      }}
    </ResizablePlotContainer>
  );
};
