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

interface HeatmapPlotWidgetProps {
  z: any[] | undefined;
  x?: any[] | undefined;
  y?: any[] | undefined;
  xLabel?: string;
  yLabel?: string;
  plotType?: 'heatmap' | 'contour';
  colormap?: string;
}

export const HeatmapPlotWidget = ({
  z,
  x,
  y,
  xLabel = 'X',
  yLabel = 'Y',
  plotType = 'heatmap',
  colormap = 'Viridis',
}: HeatmapPlotWidgetProps) => {
  if (!z || !Array.isArray(z) || z.length === 0 || !Array.isArray(z[0])) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.75rem', background: 'var(--input-bg)', border: '1px solid var(--node-border)', marginTop: '6px', borderRadius: '6px', flex: 1, minHeight: '150px' }}>
        Waiting for 2D Z data...
      </div>
    );
  }

  // Pre-process inputs
  const { zVals, xVals, yVals } = useMemo(() => {
    const zVals = z.map((row: any) => (Array.isArray(row) ? row.map((v) => Number(v) || 0) : []));
    const xVals = Array.isArray(x) && x.length > 0 ? x.map((v) => Number(v) || 0) : undefined;
    const yVals = Array.isArray(y) && y.length > 0 ? y.map((v) => Number(v) || 0) : undefined;
    return { zVals, xVals, yVals };
  }, [z, x, y]);

  return (
    <ResizablePlotContainer 
      minHeight="150px" 
      background="var(--input-bg)" 
      padding="6px" 
      borderRadius="6px"
      border="1px solid var(--node-border)"
    >
      {(_width, _height) => (
        <PlotlyHeatmapRenderer
          zVals={zVals}
          xVals={xVals}
          yVals={yVals}
          xLabel={xLabel}
          yLabel={yLabel}
          plotType={plotType}
          colormap={colormap}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface PlotlyHeatmapRendererProps {
  zVals: number[][];
  xVals?: number[];
  yVals?: number[];
  xLabel: string;
  yLabel: string;
  plotType: 'heatmap' | 'contour';
  colormap: string;
}

const PlotlyHeatmapRenderer = ({
  zVals,
  xVals,
  yVals,
  xLabel,
  yLabel,
  plotType,
  colormap,
}: PlotlyHeatmapRendererProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const lastUpdateRef = useRef<number>(0);
  const throttleTimeoutRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const runUpdate = () => {
      if (!containerRef.current) return;
      const isLight = document.documentElement.classList.contains('light-theme');
      const textColor = isLight ? '#475569' : '#94a3b8';
      const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';

      // Define colorscale helper
      let colorscale: any = colormap;
      if (colormap.toLowerCase() === 'wave') {
        colorscale = [
          [0.0, '#3b82f6'], // blue
          [0.5, '#f1f5f9'], // white/gray
          [1.0, '#ef4444'], // red
        ];
      }

      const trace: Partial<Plotly.PlotData> = {
        z: zVals,
        x: xVals,
        y: yVals,
        type: plotType as any,
        colorscale: colorscale,
        showscale: true,
        colorbar: {
          thickness: 10,
          len: 0.9,
          tickfont: { size: 7, color: textColor },
        },
      };

      const layout: Partial<Plotly.Layout> = {
        autosize: true,
        margin: { l: 40, r: 45, t: 15, b: 35 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: {
          title: { text: xLabel, font: { size: 9, color: textColor } },
          tickfont: { size: 8, color: textColor },
          gridcolor: gridColor,
        },
        yaxis: {
          title: { text: yLabel, font: { size: 9, color: textColor } },
          tickfont: { size: 8, color: textColor },
          gridcolor: gridColor,
        },
      };

      const config = {
        responsive: true,
        displayModeBar: 'hover' as const,
        displaylogo: false,
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

    if (elapsed >= 100) {
      runUpdate();
    } else {
      throttleTimeoutRef.current = setTimeout(runUpdate, 100 - elapsed);
    }

    return () => {
      if (throttleTimeoutRef.current) {
        clearTimeout(throttleTimeoutRef.current);
        throttleTimeoutRef.current = null;
      }
    };
  }, [zVals, xVals, yVals, xLabel, yLabel, plotType, colormap]);

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
