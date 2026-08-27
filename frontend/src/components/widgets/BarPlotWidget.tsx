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

interface BarPlotWidgetProps {
  blockId: string;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

export const BarPlotWidget = ({ blockId, onChange, savedLayout }: BarPlotWidgetProps) => {
  return (
    <ResizablePlotContainer
      minHeight="150px"
      background="var(--input-bg)"
      padding="6px"
      borderRadius="6px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => (
        <PlotlyBarRenderer
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

interface PlotlyBarRendererProps {
  blockId: string;
  width: number;
  height: number;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

const PlotlyBarRenderer = ({ blockId, width, height }: PlotlyBarRendererProps) => {
  const { getNode } = useReactFlow();

  const [plotData, setPlotData] = useState<{
    values: any[];
    categories?: string[];
    labels?: string[];
    orientation?: string;
    barmode?: string;
    x_label?: string;
    y_label?: string;
  }>({ values: [] });

  useEffect(() => {
    const updateChart = (eventResults?: any) => {
      const block = getNode(blockId);
      if (!block && !eventResults) return;

      const results = eventResults || block?.data?.results;
      const rawVals = results?.values || block?.data?.Values || [];

      setPlotData({
        values: rawVals,
        categories: results?.categories || block?.data?.Categories,
        labels: results?.labels || block?.data?.Labels,
        orientation: results?.orientation || (block?.data?.Orientation?.toLowerCase().startsWith('h') ? 'h' : 'v'),
        barmode: (results?.barmode || block?.data?.BarMode || 'group').toLowerCase(),
        x_label: results?.x_label || block?.data?.XLabel || 'Category',
        y_label: results?.y_label || block?.data?.YLabel || 'Value'
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

  const isHorizontal = plotData.orientation === 'h';

  let traces: any[] = [];
  if (plotData.values && plotData.values.length > 0) {
    const isMultiSeries = Array.isArray(plotData.values[0]);
    const seriesList: any[][] = isMultiSeries ? plotData.values : [plotData.values];

    traces = seriesList.map((series, i) => {
      const pointCount = series.length;
      const cats = plotData.categories && plotData.categories.length === pointCount
        ? plotData.categories
        : Array.from({ length: pointCount }, (_, idx) => `Item ${idx + 1}`);

      const traceName = plotData.labels?.[i] || (seriesList.length > 1 ? `Series ${i + 1}` : 'Values');

      return {
        x: isHorizontal ? series : cats,
        y: isHorizontal ? cats : series,
        type: 'bar',
        orientation: isHorizontal ? 'h' : 'v',
        name: traceName,
        marker: { color: colors[i % colors.length] }
      };
    });
  }

  const layout: any = {
    width: width || 280,
    height: height || 250,
    barmode: plotData.barmode || 'group',
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { l: isHorizontal ? 65 : 45, r: 25, t: 25, b: isHorizontal ? 35 : 45 },
    xaxis: {
      title: { text: isHorizontal ? (plotData.y_label || 'Value') : (plotData.x_label || 'Category'), font: { size: 13, color: textColor } },
      tickfont: { size: 11, color: textColor },
      gridcolor: gridColor,
      zerolinecolor: gridColor,
      exponentformat: 'SI',
      autorange: true
    },
    yaxis: {
      title: { text: isHorizontal ? (plotData.x_label || 'Category') : (plotData.y_label || 'Value'), font: { size: 13, color: textColor } },
      tickfont: { size: 11, color: textColor },
      gridcolor: gridColor,
      zerolinecolor: gridColor,
      exponentformat: 'SI',
      autorange: true
    },
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
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};
