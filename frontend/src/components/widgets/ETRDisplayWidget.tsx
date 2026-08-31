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
import { useTranslation } from '../../i18n';
import { useReactFlow } from '@xyflow/react';

interface ETRDisplayWidgetProps {
  blockId: string;
  initialFormatted?: string;
  initialLabel?: string;
}

export const ETRDisplayWidget: React.FC<ETRDisplayWidgetProps> = ({
  blockId,
  initialFormatted = '00:00:00',
  initialLabel = 'T-',
}) => {
  const { t } = useTranslation();
  const { getNode } = useReactFlow();
  const [formatted, setFormatted] = useState<string>(initialFormatted);
  const [label, setLabel] = useState<string>(initialLabel);
  const [isActive, setIsActive] = useState<boolean>(false);

  useEffect(() => {
    const handleTelemetry = (e: Event) => {
      const customEvent = e as CustomEvent;
      const detail = customEvent.detail;
      const results = detail?.results;

      if (detail?.status) {
        setIsActive(detail.status === 'running');
      }

      if (results?.formatted !== undefined) {
        setFormatted(String(results.formatted));
      }
      if (results?.label !== undefined) {
        setLabel(String(results.label));
      }
    };

    const block = getNode(blockId);
    if (block) {
      setIsActive(block.data?.status === 'running');
      if (block.data?.results) {
        const res = block.data.results as any;
        if (res.formatted) setFormatted(String(res.formatted));
        if (res.label) setLabel(String(res.label));
      }
      if (block.data?.Label) {
        setLabel(String(block.data.Label));
      }
    }

    const eventName = `telemetry-${blockId}`;
    window.addEventListener(eventName, handleTelemetry);
    return () => window.removeEventListener(eventName, handleTelemetry);
  }, [blockId, getNode]);

  return (
    <div
      className="etr-display-widget nodrag"
      style={{
        width: '100%',
        boxSizing: 'border-box',
        background: 'radial-gradient(ellipse at top, #0f172a 0%, #020617 100%)',
        border: '1.5px solid rgba(245, 158, 11, 0.4)',
        borderRadius: '8px',
        padding: '10px 14px',
        marginTop: '6px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '4px',
        boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.8), 0 0 15px rgba(245, 158, 11, 0.12)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Top Console Bar */}
      <div
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid rgba(245, 158, 11, 0.2)',
          paddingBottom: '4px',
          marginBottom: '2px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              backgroundColor: isActive ? '#10b981' : '#f59e0b',
              boxShadow: isActive ? '0 0 8px #10b981' : '0 0 4px #f59e0b',
            }}
          />
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              fontFamily: 'monospace',
              letterSpacing: '1.5px',
              color: '#f59e0b',
              textTransform: 'uppercase',
            }}
          >
            {label || t('dashboard.tMinus', 'T- MINUS')}
          </span>
        </div>

        <span
          style={{
            fontSize: '0.65rem',
            fontFamily: 'monospace',
            letterSpacing: '1px',
            color: '#64748b',
          }}
        >
          {t('dashboard.etrClock', 'ETR CLOCK')}
        </span>
      </div>

      {/* Digital Readout Screen with Margins and Bezel */}
      <div
        style={{
          width: 'calc(100% - 12px)',
          margin: '6px 0',
          padding: '6px 10px',
          background: 'rgba(2, 6, 23, 0.85)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          borderRadius: '6px',
          boxShadow: 'inset 0 2px 6px rgba(0,0,0,0.7)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          boxSizing: 'border-box',
        }}
      >
        <span
          style={{
            fontFamily: "'Courier New', Courier, monospace",
            fontSize: '1.5rem',
            fontWeight: 800,
            letterSpacing: '2px',
            color: '#fef08a',
            textShadow:
              '0 0 10px rgba(250, 204, 21, 0.7), 0 0 20px rgba(245, 158, 11, 0.35)',
            lineHeight: '1.1',
            userSelect: 'none',
          }}
        >
          {formatted}
        </span>
      </div>
    </div>
  );
};
