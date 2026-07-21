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

import React, { useState, useEffect, useRef } from 'react';

interface ResizablePlotContainerProps {
  children: (width: number, height: number) => React.ReactNode;
  minHeight?: string;
  background?: string;
  padding?: string;
  borderRadius?: string;
  border?: string;
}

export const ResizablePlotContainer = ({ 
  children, 
  minHeight = '70px',
  background = 'var(--input-bg)',
  padding = '4px',
  borderRadius = '4px',
  border = '1px solid var(--block-border)'
}: ResizablePlotContainerProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const width = Math.round(entry.contentRect.width);
        const height = Math.round(entry.contentRect.height);
        setDimensions((prev) => (prev.width === width && prev.height === height ? prev : { width, height }));
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div 
      ref={containerRef} 
      style={{ 
        marginTop: '6px', 
        background, 
        padding, 
        borderRadius, 
        display: 'flex', 
        flexDirection: 'column', 
        flex: 1, 
        minHeight,
        border,
        overflow: 'hidden',
        position: 'relative'
      }}
    >
      {dimensions.width > 0 && dimensions.height > 0 ? (
        <div 
          style={{ 
            position: 'absolute', 
            top: padding, 
            bottom: padding, 
            left: padding, 
            right: padding, 
            display: 'flex', 
            flexDirection: 'column',
            overflow: 'hidden' 
          }}
        >
          {children(dimensions.width, dimensions.height)}
        </div>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.65rem', flex: 1 }}>
          Initializing...
        </div>
      )}
    </div>
  );
};
