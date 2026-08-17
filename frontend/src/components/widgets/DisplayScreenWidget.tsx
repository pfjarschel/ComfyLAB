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

import { useState, useEffect } from 'react';
import { FormattedDisplay } from '../common/FormattedDisplay';
import { useReactFlow } from '@xyflow/react';

interface DisplayScreenWidgetProps {
  blockId: string;
  initialValue?: any;
}

export const DisplayScreenWidget = ({ blockId, initialValue }: DisplayScreenWidgetProps) => {
  const [displayValue, setDisplayValue] = useState<any>(initialValue);
  const [copied, setCopied] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const { getNode } = useReactFlow();

  useEffect(() => {
    const handleTelemetry = (e: Event) => {
      const customEvent = e as CustomEvent;
      const results = customEvent.detail?.results;
      if (results?.displayValue !== undefined) {
        setDisplayValue(results.displayValue);
      } else if (results?.result !== undefined) {
        setDisplayValue(results.result);
      } else {
        const block = getNode(blockId);
        if (block && (block.data?.results as any)?.displayValue !== undefined) {
          setDisplayValue((block.data.results as any).displayValue);
        }
      }
    };
    const eventName = `telemetry-${blockId}`;
    window.addEventListener(eventName, handleTelemetry);
    return () => window.removeEventListener(eventName, handleTelemetry);
  }, [blockId, getNode]);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (displayValue === undefined || displayValue === null) return;
    const textToCopy = typeof displayValue === 'object' 
      ? JSON.stringify(displayValue, null, 2) 
      : String(displayValue);
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const hasValue = displayValue !== undefined && displayValue !== null;

  return (
    <div
      className="display-screen nodrag"
      title={hasValue ? String(displayValue) : undefined}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        background: 'rgba(2, 6, 23, 0.85)',
        border: '1px solid rgba(148, 163, 184, 0.3)',
        borderRadius: '6px',
        marginTop: '8px',
        fontFamily: 'monospace',
        fontSize: '1.2rem',
        color: '#10b981',
        textShadow: '0 0 8px rgba(16, 185, 129, 0.6)',
        boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.6)',
        letterSpacing: '1px',
        minHeight: '80px',
        flex: 1,
        width: '100%',
        boxSizing: 'border-box',
        position: 'relative',
        overflow: 'hidden',
        userSelect: 'text',
        cursor: 'text',
      }}
    >
      {/* Quick Copy Button */}
      {hasValue && (
        <button
          onClick={handleCopy}
          title={copied ? "Copied!" : "Copy raw value"}
          style={{
            position: 'absolute',
            top: '4px',
            right: '4px',
            zIndex: 10,
            background: copied ? 'rgba(34, 197, 94, 0.25)' : 'rgba(15, 23, 42, 0.75)',
            border: `1px solid ${copied ? 'rgba(34, 197, 94, 0.6)' : 'rgba(148, 163, 184, 0.25)'}`,
            borderRadius: '4px',
            padding: '2px 5px',
            fontSize: '0.65rem',
            color: copied ? '#4ade80' : '#94a3b8',
            cursor: 'pointer',
            opacity: isHovered || copied ? 1 : 0,
            transition: 'opacity 0.2s ease, background 0.15s ease, color 0.15s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '3px',
            userSelect: 'none',
            lineHeight: 1,
          }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <span>{copied ? '✓' : '📋'}</span>
          {copied && <span style={{ fontSize: '0.6rem', fontWeight: 600 }}>Copied</span>}
        </button>
      )}

      <div style={{
        position: 'absolute',
        top: '8px',
        bottom: '8px',
        left: '8px',
        right: '8px',
        overflowY: 'auto',
        wordBreak: 'break-all',
        whiteSpace: 'pre-wrap',
        textAlign: 'center',
        userSelect: 'text',
        cursor: 'text',
      }}>
        <div style={{
          minHeight: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
          userSelect: 'text',
          cursor: 'text',
        }}>
          {hasValue ? (
            <FormattedDisplay value={displayValue} />
          ) : '---'}
        </div>
      </div>
    </div>
  );
};
