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

interface BoxPlotWidgetProps {
  blockId: string;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

export const BoxPlotWidget = ({ blockId, onChange, savedLayout }: BoxPlotWidgetProps) => {
  return (
    <ResizablePlotContainer
      minHeight="150px"
      background="var(--input-bg)"
      padding="6px"
      borderRadius="6px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => (
        <PlotlyBoxRenderer
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

interface PlotlyBoxRendererProps {
  blockId: string;
  width: number;
  height: number;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

const PlotlyBoxRenderer = ({ blockId, width, height }: PlotlyBoxRendererProps) => {
  const { getNode } = useReactFlow();

  const [plotData, setPlotData] = useState<{
    data: any[];
    plot_type?: string;
    points?: string;
    labels?: string[];
    y_label?: string;
  }>({ data: [] });

  useEffect(() => {
    const updateChart = (eventResults?: any) => {
      const block = getNode(blockId);
      if (!block && !eventResults) return;

      const results = eventResults || block?.data?.results;
      const rawData = results?.data || block?.data?.Data || [];

      setPlotData({
        data: rawData,
        plot_type: (results?.plot_type || block?.data?.PlotType || 'box').toLowerCase(),
        points: (results?.points || block?.data?.Points || 'outliers').toLowerCase(),
        labels: results?.labels || block?.data?.Labels,
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

  const isViolin = plotData.plot_type === 'violin';
  const boxPoints = plotData.points === 'all' ? 'all' : (plotData.points === 'none' ? false : 'outliers');

  let traces: any[] = [];
  if (plotData.data && plotData.data.length > 0) {
    const isMultiSeries = Array.isArray(plotData.data[0]);
    const seriesList: any[][] = isMultiSeries ? plotData.data : [plotData.data];

    traces = seriesList.map((series, i) => {
      const traceName = plotData.labels?.[i] || (seriesList.length > 1 ? `Group ${i + 1}` : 'Distribution');
      const traceColor = colors[i % colors.length];

      if (isViolin) {
        return {
          y: series,
          type: 'violin',
          name: traceName,
          points: boxPoints,
          box: { visible: true },
          meanline: { visible: true },
          line: { color: traceColor },
          marker: { color: traceColor, size: 4 }
        };
      }

      return {
        y: series,
        type: 'box',
        name: traceName,
        boxpoints: boxPoints,
        boxmean: true,
        marker: { color: traceColor, size: 4 },
        line: { color: traceColor, width: 1.5 }
      };
    });
  }

  const layout: any = {
    width: width || 280,
    height: height || 250,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { l: 45, r: 25, t: 25, b: 35 },
    yaxis: {
      title: { text: plotData.y_label || 'Value', font: { size: 13, color: textColor } },
      tickfont: { size: 11, color: textColor },
      gridcolor: gridColor,
      zerolinecolor: gridColor,
      exponentformat: 'SI',
      autorange: true
    },
    xaxis: {
      tickfont: { size: 11, color: textColor },
      gridcolor: gridColor
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
