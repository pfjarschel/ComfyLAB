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

import { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import { ResizablePlotContainer } from '../common/ResizablePlotContainer';

interface XYPlotWidgetProps {
  x: any[] | undefined;
  y: any[] | undefined;
  xLabel?: string;
  yLabel?: string;
}

export const XYPlotWidget = ({ x, y, xLabel = 'X', yLabel = 'Y' }: XYPlotWidgetProps) => {
  if (!x || !y || !Array.isArray(x) || !Array.isArray(y) || x.length === 0 || y.length === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.75rem', background: 'var(--input-bg)', border: '1px solid var(--node-border)', marginTop: '6px', borderRadius: '6px', flex: 1, minHeight: '150px' }}>
        Waiting for X/Y data...
      </div>
    );
  }

  const len = Math.min(x.length, y.length);
  const xVals = x.slice(0, len).map((v: any) => Number(v) || 0);
  const yVals = y.slice(0, len).map((v: any) => Number(v) || 0);

  return (
    <ResizablePlotContainer 
      minHeight="150px" 
      background="var(--input-bg)" 
      padding="6px" 
      borderRadius="6px"
      border="1px solid var(--node-border)"
    >
      {(width, height) => (
        <PlotlyXYRenderer
          xVals={xVals}
          yVals={yVals}
          xLabel={xLabel}
          yLabel={yLabel}
          width={width}
          height={height}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface PlotlyXYRendererProps {
  xVals: number[];
  yVals: number[];
  xLabel: string;
  yLabel: string;
  width: number;
  height: number;
}

const PlotlyXYRenderer = ({ xVals, yVals, xLabel, yLabel, width, height }: PlotlyXYRendererProps) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const isLight = document.documentElement.classList.contains('light-theme');
    const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';
    const textColor = isLight ? '#475569' : '#94a3b8';
    const zeroLineColor = isLight ? 'rgba(0, 0, 0, 0.2)' : 'rgba(255, 255, 255, 0.2)';

    const trace: Partial<Plotly.PlotData> = {
      x: xVals,
      y: yVals,
      type: 'scatter',
      mode: 'lines',
      line: { color: '#10b981', width: 1.5 }
    };

    const layout: Partial<Plotly.Layout> = {
      autosize: true,
      width,
      height,
      margin: { l: 40, r: 15, t: 15, b: 35 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      xaxis: {
        title: { text: xLabel, font: { size: 10, color: textColor } },
        tickfont: { size: 8, color: textColor },
        gridcolor: gridColor,
        zerolinecolor: zeroLineColor,
        exponentformat: 'SI',
        showexponent: 'all',
        tickformat: '.3~s'
      },
      yaxis: {
        title: { text: yLabel, font: { size: 10, color: textColor } },
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
  }, [xVals, yVals, xLabel, yLabel, width, height]);

  useEffect(() => {
    return () => {
      if (containerRef.current) {
        Plotly.purge(containerRef.current);
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
