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

import { useEffect, useRef, useMemo } from 'react';
import Plotly from 'plotly.js-dist-min';
import { ResizablePlotContainer } from '../common/ResizablePlotContainer';

interface TimePlotWidgetProps {
  points: number[] | undefined;
  strokeColor?: string;
}

export const TimePlotWidget = ({ points, strokeColor = '#34d399' }: TimePlotWidgetProps) => {
  if (!points || !Array.isArray(points) || points.length === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.65rem', background: 'var(--input-bg)', border: '1px solid var(--node-border)', marginTop: '6px', borderRadius: '4px', flex: 1, minHeight: '120px' }}>
        Waiting for data...
      </div>
    );
  }

  const numericPoints = useMemo(() => points.map(v => Number(v) || 0), [points]);

  return (
    <ResizablePlotContainer 
      minHeight="120px"
      background="var(--input-bg)" 
      padding="6px" 
      borderRadius="6px"
      border="1px solid var(--node-border)"
    >
      {(_width, _height) => (
        <PlotlyTimeRenderer
          points={numericPoints}
          strokeColor={strokeColor}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface PlotlyTimeRendererProps {
  points: number[];
  strokeColor: string;
}

const PlotlyTimeRenderer = ({ points, strokeColor }: PlotlyTimeRendererProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const lastUpdateRef = useRef<number>(0);
  const throttleTimeoutRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const runUpdate = () => {
      if (!containerRef.current) return;
      const isLight = document.documentElement.classList.contains('light-theme');
      const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';
      const textColor = isLight ? '#475569' : '#94a3b8';
      const zeroLineColor = isLight ? 'rgba(0, 0, 0, 0.2)' : 'rgba(255, 255, 255, 0.2)';

      const xVals = points.map((_, i) => i);

      const trace: Partial<Plotly.PlotData> = {
        x: xVals,
        y: points,
        type: 'scatter',
        mode: 'lines',
        line: { color: strokeColor, width: 1.5 }
      };

      const layout: Partial<Plotly.Layout> = {
        autosize: true,
        margin: { l: 40, r: 15, t: 15, b: 25 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: {
          title: { text: 'Time Index', font: { size: 9, color: textColor } },
          tickfont: { size: 8, color: textColor },
          gridcolor: gridColor,
          zerolinecolor: zeroLineColor,
          exponentformat: 'SI',
          showexponent: 'all',
          tickformat: '.3~s'
        },
        yaxis: {
          title: { text: 'Value', font: { size: 9, color: textColor } },
          tickfont: { size: 8, color: textColor },
          gridcolor: gridColor,
          zerolinecolor: zeroLineColor,
          exponentformat: 'SI',
          showexponent: 'all',
          tickformat: '.3~s'
        },
        showlegend: false
      };

      const config = {
        responsive: true,
        displayModeBar: 'hover' as const,
        displaylogo: false
      };

      Plotly.react(containerRef.current, [trace], layout, config);
      lastUpdateRef.current = Date.now();
    };

    if (throttleTimeoutRef.current) {
      clearTimeout(throttleTimeoutRef.current);
      throttleTimeoutRef.current = null;
    }

    const now = Date.now();
    const elapsed = now - lastUpdateRef.current;

    if (elapsed >= 60) {
      runUpdate();
    } else {
      throttleTimeoutRef.current = setTimeout(runUpdate, 60 - elapsed);
    }

    return () => {
      if (throttleTimeoutRef.current) {
        clearTimeout(throttleTimeoutRef.current);
        throttleTimeoutRef.current = null;
      }
    };
  }, [points, strokeColor]);

  // Imperative resize observer and cleanup
  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;

    const observer = new ResizeObserver(() => {
      if (node) {
        Plotly.Plots.resize(node);
      }
    });
    observer.observe(node);

    return () => {
      observer.disconnect();
      if (node) {
        Plotly.purge(node);
      }
    };
  }, []);

  return (
    <div 
      className="nodrag" 
      style={{ width: '100%', height: '100%', overflow: 'hidden' }}
    >
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
