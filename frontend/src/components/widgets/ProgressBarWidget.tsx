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

interface ProgressBarWidgetProps {
  blockId: string;
  initialPercentage?: number;
  initialLabel?: string;
}

export const ProgressBarWidget: React.FC<ProgressBarWidgetProps> = ({
  blockId,
  initialPercentage = 0,
  initialLabel = '',
}) => {
  const { t } = useTranslation();
  const { getNode } = useReactFlow();
  const [percentage, setPercentage] = useState<number>(initialPercentage);
  const [label, setLabel] = useState<string>(initialLabel);

  useEffect(() => {
    const handleTelemetry = (e: Event) => {
      const customEvent = e as CustomEvent;
      const detail = customEvent.detail;
      const results = detail?.results;

      if (results?.percentage !== undefined) {
        setPercentage(Number(results.percentage));
      } else if (results?.displayValue !== undefined) {
        const parsed = parseFloat(String(results.displayValue).replace('%', ''));
        if (!isNaN(parsed)) setPercentage(parsed);
      }

      if (results?.label !== undefined && results.label !== '') {
        setLabel(String(results.label));
      }
    };

    // Check existing node state on mount
    const block = getNode(blockId);
    if (block?.data?.results) {
      const res = block.data.results as any;
      if (res.percentage !== undefined) setPercentage(Number(res.percentage));
      if (res.label) setLabel(String(res.label));
    }

    const eventName = `telemetry-${blockId}`;
    window.addEventListener(eventName, handleTelemetry);
    return () => window.removeEventListener(eventName, handleTelemetry);
  }, [blockId, getNode]);

  const clampedPct = Math.max(0, Math.min(100, percentage));

  return (
    <div
      className="progress-bar-widget nodrag"
      style={{
        width: '100%',
        padding: '8px 10px',
        boxSizing: 'border-box',
        background: 'rgba(10, 15, 29, 0.85)',
        border: '1px solid rgba(51, 65, 85, 0.4)',
        borderRadius: '8px',
        marginTop: '6px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
      }}
    >
      {/* Top Header: Label + Percentage */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.85rem',
          lineHeight: '1.2',
        }}
      >
        <span
          style={{
            fontWeight: 500,
            color: '#94a3b8',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            maxWidth: '65%',
          }}
          title={label || t('dashboard.progress', 'Progress')}
        >
          {label || t('dashboard.progress', 'Progress')}
        </span>

        <span
          style={{
            fontFamily: 'monospace',
            fontWeight: 700,
            fontSize: '0.9rem',
            color: clampedPct >= 100 ? '#10b981' : '#38bdf8',
          }}
        >
          {clampedPct.toFixed(1)}%
        </span>
      </div>

      {/* Progress Track */}
      <div
        style={{
          width: '100%',
          height: '16px',
          background: 'rgba(2, 6, 23, 0.9)',
          borderRadius: '8px',
          border: '1px solid rgba(71, 85, 105, 0.4)',
          overflow: 'hidden',
          position: 'relative',
          boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5)',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${clampedPct}%`,
            background:
              clampedPct >= 100
                ? 'linear-gradient(90deg, #10b981 0%, #34d399 100%)'
                : 'linear-gradient(90deg, #0284c7 0%, #38bdf8 60%, #10b981 100%)',
            borderRadius: '8px',
            transition: 'width 0.12s ease-out',
            boxShadow:
              clampedPct > 0
                ? '0 0 10px rgba(56, 189, 248, 0.5)'
                : 'none',
          }}
        />
      </div>
    </div>
  );
};
