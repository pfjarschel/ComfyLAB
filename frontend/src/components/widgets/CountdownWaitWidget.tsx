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

interface CountdownWaitWidgetProps {
  blockId: string;
  initialDuration?: number;
  onBlockDataChange?: (blockId: string, key: string, value: any) => void;
}

export const CountdownWaitWidget: React.FC<CountdownWaitWidgetProps> = ({
  blockId,
  initialDuration = 10,
  onBlockDataChange,
}) => {
  const { getNode, setNodes } = useReactFlow();
  const [duration, setDuration] = useState<number>(initialDuration);
  const [remaining, setRemaining] = useState<number>(initialDuration);
  const [detailedStr, setDetailedStr] = useState<string>('');
  const [percentage, setPercentage] = useState<number>(0);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  useEffect(() => {
    const handleTelemetry = (e: Event) => {
      const customEvent = e as CustomEvent;
      const detail = customEvent.detail;
      const results = detail?.results;

      if (detail?.status) {
        setIsRunning(detail.status === 'running');
      }

      if (results?.remaining !== undefined) {
        setRemaining(Number(results.remaining));
      }
      if (results?.duration !== undefined) {
        setDuration(Number(results.duration));
      }
      if (results?.percentage !== undefined) {
        setPercentage(Number(results.percentage));
      }
      if (results?.detailed_str !== undefined) {
        setDetailedStr(String(results.detailed_str));
      } else if (results?.remaining_str !== undefined) {
        setDetailedStr(String(results.remaining_str));
      }
    };

    // Check existing node state on mount
    const block = getNode(blockId);
    if (block) {
      setIsRunning(block.data?.status === 'running');
      if (block.data?.results) {
        const res = block.data.results as any;
        if (res.remaining !== undefined) setRemaining(Number(res.remaining));
        if (res.duration !== undefined) setDuration(Number(res.duration));
        if (res.percentage !== undefined) setPercentage(Number(res.percentage));
        if (res.detailed_str) setDetailedStr(String(res.detailed_str));
      }
      if (block.data?.Duration !== undefined) {
        setDuration(Number(block.data.Duration));
      }
    }

    const eventName = `telemetry-${blockId}`;
    window.addEventListener(eventName, handleTelemetry);
    return () => window.removeEventListener(eventName, handleTelemetry);
  }, [blockId, getNode]);

  const handleSkip = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isRunning) return;
    if (onBlockDataChange) {
      onBlockDataChange(blockId, 'skip', true);
    } else {
      setNodes((nodes) =>
        nodes.map((n) =>
          n.id === blockId ? { ...n, data: { ...n.data, skip: true } } : n
        )
      );
    }
  };

  const displayTime = detailedStr || `${remaining.toFixed(1)}s`;
  const drainingPercent = Math.max(0, Math.min(100, 100 - percentage));

  return (
    <div
      className="countdown-wait-widget nodrag"
      title={`Duration: ${duration}s | Remaining: ${remaining.toFixed(1)}s`}
      style={{
        width: '100%',
        padding: '10px',
        boxSizing: 'border-box',
        background: 'rgba(15, 23, 42, 0.9)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        borderRadius: '8px',
        marginTop: '6px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}
    >
      {/* Timer Digits and Skip Button */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '5px', minWidth: 0 }}>
          <span style={{ fontSize: '0.95rem' }}>⏱️</span>
          <span
            style={{
              fontFamily: 'monospace',
              fontSize: '1.25rem',
              fontWeight: 800,
              letterSpacing: '0.5px',
              color: isRunning ? '#38bdf8' : '#94a3b8',
              textShadow: isRunning ? '0 0 8px rgba(56, 189, 248, 0.5)' : 'none',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {displayTime}
          </span>
        </div>

        {isRunning && (
          <button
            onClick={handleSkip}
            title="Skip remaining delay immediately"
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              color: '#f87171',
              borderRadius: '3px',
              padding: '2px 6px',
              fontSize: '0.65rem',
              lineHeight: '1',
              fontWeight: 700,
              cursor: 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              flexShrink: 0,
              transition: 'background 0.15s, border-color 0.15s',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(239, 68, 68, 0.3)';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(239, 68, 68, 0.15)';
            }}
          >
            Skip
          </button>
        )}
      </div>

      {/* Draining Time Remaining Bar */}
      <div
        style={{
          width: '100%',
          height: '10px',
          background: 'rgba(2, 6, 23, 0.95)',
          borderRadius: '5px',
          border: '1px solid rgba(71, 85, 105, 0.3)',
          overflow: 'hidden',
          boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.6)',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${drainingPercent}%`,
            background:
              drainingPercent > 30
                ? 'linear-gradient(90deg, #38bdf8, #06b6d4)'
                : 'linear-gradient(90deg, #f59e0b, #ef4444)',
            borderRadius: '5px',
            transition: 'width 0.1s linear',
            boxShadow: '0 0 8px rgba(56, 189, 248, 0.4)',
          }}
        />
      </div>
    </div>
  );
};
