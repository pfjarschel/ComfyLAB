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

import { FormattedDisplay } from '../common/FormattedDisplay';

interface DisplayScreenWidgetProps {
  displayValue: any;
}

export const DisplayScreenWidget = ({ displayValue }: DisplayScreenWidgetProps) => {
  return (
    <div
      className="display-screen nodrag"
      title={displayValue !== undefined && displayValue !== null ? String(displayValue) : undefined}
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
      }}
    >
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
      }}>
        <div style={{
          minHeight: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
        }}>
          {displayValue !== undefined && displayValue !== null ? (
            <FormattedDisplay value={displayValue} />
          ) : '---'}
        </div>
      </div>
    </div>
  );
};
