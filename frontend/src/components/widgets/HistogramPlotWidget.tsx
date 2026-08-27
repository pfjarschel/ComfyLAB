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

import { useEffect, useState } from 'react';
import _Plot from 'react-plotly.js';
const Plot: any = (_Plot as any).default ?? _Plot;
import { ResizablePlotContainer } from '../common/ResizablePlotContainer';
import { useReactFlow } from '@xyflow/react';

interface HistogramPlotWidgetProps {
  blockId: string;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

export const HistogramPlotWidget = ({ blockId, onChange, savedLayout }: HistogramPlotWidgetProps) => {
  return (
    <ResizablePlotContainer
      minHeight="150px"
      background="var(--input-bg)"
      padding="6px"
      borderRadius="6px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => (
        <PlotlyHistogramRenderer
          blockId={blockId}
          width={width}
          height={height}
          onChange={onChange}
          savedLayout={savedLayout}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface PlotlyHistogramRendererProps {
  blockId: string;
  width: number;
  height: number;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

const PlotlyHistogramRenderer = ({ blockId, width, height, onChange, savedLayout }: PlotlyHistogramRendererProps) => {
  const { getNode } = useReactFlow();

  const [plotData, setPlotData] = useState<{
    data: any[];
    bins?: number | null;
    bin_size?: number | null;
    bin_min?: number | null;
    bin_max?: number | null;
    normalization?: string;
    cumulative?: boolean;
    barmode?: string;
    labels?: string[];
    x_label?: string;
    y_label?: string;
    show_stats?: boolean;
  }>({ data: [] });

  const [dragMode, setDragMode] = useState<string>(savedLayout?.dragmode || 'zoom');

  useEffect(() => {
    if (savedLayout?.dragmode && savedLayout.dragmode !== dragMode) {
      setDragMode(savedLayout.dragmode);
    }
  }, [savedLayout?.dragmode]);

  useEffect(() => {
    const updateChart = (eventResults?: any) => {
      const block = getNode(blockId);
      if (!block && !eventResults) return;

      const results = eventResults || block?.data?.results;
      const rawData = results?.data || block?.data?.Data || [];

      setPlotData({
        data: rawData,
        bins: results?.bins ?? block?.data?.Bins,
        bin_size: results?.bin_size ?? block?.data?.BinSize,
        bin_min: results?.bin_min ?? block?.data?.BinMin,
        bin_max: results?.bin_max ?? block?.data?.BinMax,
        normalization: results?.normalization ?? block?.data?.Normalization ?? 'Count',
        cumulative: results?.cumulative ?? block?.data?.Cumulative ?? false,
        barmode: results?.barmode ?? block?.data?.BarMode ?? 'overlay',
        labels: results?.labels ?? block?.data?.Labels,
        x_label: results?.x_label ?? block?.data?.XLabel ?? 'Value',
        y_label: results?.y_label ?? block?.data?.YLabel ?? 'Count',
        show_stats: results?.show_stats ?? block?.data?.ShowStats ?? false
      });
    };

    updateChart();

    const eventName = `telemetry-${blockId}`;
    const handleTelemetry = (e: any) => {
      updateChart(e.detail?.results);
    };

    window.addEventListener(eventName, handleTelemetry);
    return () => {
      window.removeEventListener(eventName, handleTelemetry);
    };
  }, [blockId, getNode]);

  const isLight = document.documentElement.classList.contains('light-theme');
  const textColor = isLight ? '#475569' : '#94a3b8';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';
  const colors = ['#60a5fa', '#f87171', '#34d399', '#fbbf24', '#a78bfa', '#2dd4bf'];

  const normMap: Record<string, string> = {
    'Count': '',
    'Percent': 'percent',
    'Probability': 'probability',
    'Density': 'density',
    'Probability Density': 'probability density'
  };

  const plotlyHistnorm = normMap[plotData.normalization || 'Count'] ?? '';

  let traces: any[] = [];
  const shapes: any[] = [];
  const annotations: any[] = [];

  if (plotData.data && plotData.data.length > 0) {
    const isMultiSeries = Array.isArray(plotData.data[0]);
    const seriesList: any[][] = isMultiSeries ? plotData.data : [plotData.data];

    traces = seriesList.map((series, i) => {
      const traceName = plotData.labels?.[i] || (seriesList.length > 1 ? `Series ${i + 1}` : 'Distribution');
      const traceColor = colors[i % colors.length];

      const xbins: any = {};
      if (plotData.bin_size && plotData.bin_size > 0) xbins.size = plotData.bin_size;
      if (plotData.bin_min != null) xbins.start = plotData.bin_min;
      if (plotData.bin_max != null) xbins.end = plotData.bin_max;

      return {
        x: series,
        type: 'histogram',
        name: traceName,
        histnorm: plotlyHistnorm,
        cumulative: { enabled: Boolean(plotData.cumulative) },
        opacity: plotData.barmode === 'overlay' && seriesList.length > 1 ? 0.7 : 0.85,
        marker: { color: traceColor },
        nbinsx: plotData.bins && plotData.bins > 0 ? plotData.bins : undefined,
        ...(Object.keys(xbins).length > 0 ? { xbins } : {})
      };
    });

    if (plotData.show_stats && seriesList.length > 0) {
      const primary = seriesList[0].filter((v: any) => typeof v === 'number' && !isNaN(v));
      if (primary.length > 0) {
        const mean = primary.reduce((acc: number, val: number) => acc + val, 0) / primary.length;
        const variance = primary.reduce((acc: number, val: number) => acc + Math.pow(val - mean, 2), 0) / primary.length;
        const std = Math.sqrt(variance);

        shapes.push({
          type: 'line',
          x0: mean,
          x1: mean,
          y0: 0,
          y1: 1,
          yref: 'paper',
          line: { color: '#ef4444', width: 2, dash: 'dash' }
        });

        annotations.push({
          x: mean,
          y: 1,
          yref: 'paper',
          text: `μ=${mean.toFixed(2)} σ=${std.toFixed(2)}`,
          showarrow: false,
          font: { size: 10, color: '#ef4444' },
          bgcolor: isLight ? 'rgba(255, 255, 255, 0.8)' : 'rgba(0, 0, 0, 0.6)'
        });
      }
    }
  }

  const layout: any = {
    width: width || 280,
    height: height || 250,
    barmode: (plotData.barmode || 'overlay').toLowerCase(),
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { l: 45, r: 25, t: 25, b: 35 },
    dragmode: dragMode,
    xaxis: {
      title: { text: plotData.x_label || 'Value', font: { size: 13, color: textColor } },
      tickfont: { size: 11, color: textColor },
      gridcolor: gridColor,
      zerolinecolor: gridColor,
      exponentformat: 'SI',
      autorange: true
    },
    yaxis: {
      title: { text: plotData.y_label || 'Count', font: { size: 13, color: textColor } },
      tickfont: { size: 11, color: textColor },
      gridcolor: gridColor,
      zerolinecolor: gridColor,
      exponentformat: 'SI',
      autorange: true
    },
    shapes,
    annotations,
    showlegend: traces.length > 1,
    legend: {
      x: 1,
      xanchor: 'right',
      y: 1,
      font: { size: 10, color: textColor },
      bgcolor: 'transparent'
    }
  };

  return (
    <div className="nodrag nopan nowheel" style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      <Plot
        data={traces}
        layout={layout}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['lasso2d', 'select2d']
        }}
        onRelayout={(event: any) => {
          if (event?.dragmode && onChange) {
            setDragMode(event.dragmode);
            onChange('plot_layout', { ...(savedLayout || {}), dragmode: event.dragmode });
          }
        }}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};
