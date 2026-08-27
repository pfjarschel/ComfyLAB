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

import { useEffect, useState, useContext } from 'react';
import _Plot from 'react-plotly.js';
const Plot: any = (_Plot as any).default ?? _Plot;
import { ResizablePlotContainer } from '../common/ResizablePlotContainer';
import { useReactFlow } from '@xyflow/react';
import { SettingsContext } from '../../context/SettingsContext';
import { downsampleLTTB } from '../../utils/downsample';

interface DualYPlotWidgetProps {
  blockId: string;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

export const DualYPlotWidget = ({ blockId, onChange, savedLayout }: DualYPlotWidgetProps) => {
  return (
    <ResizablePlotContainer
      minHeight="150px"
      background="var(--input-bg)"
      padding="6px"
      borderRadius="6px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => (
        <PlotlyDualYRenderer
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

interface PlotlyDualYRendererProps {
  blockId: string;
  width: number;
  height: number;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

const PlotlyDualYRenderer = ({ blockId, width, height, onChange, savedLayout }: PlotlyDualYRendererProps) => {
  const { getNode } = useReactFlow();

  const [plotData, setPlotData] = useState<{
    x: any[];
    y1: any[];
    y2: any[];
    x_label?: string;
    y1_label?: string;
    y2_label?: string;
    y1_name?: string;
    y2_name?: string;
    x_min?: number;
    x_max?: number;
    y1_min?: number;
    y1_max?: number;
    y2_min?: number;
    y2_max?: number;
    x_log?: boolean;
    y1_log?: boolean;
    y2_log?: boolean;
  }>({ x: [], y1: [], y2: [] });

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
      const x = results?.x || block?.data?.X || [];
      const y1 = results?.y1 || block?.data?.Y1 || [];
      const y2 = results?.y2 || block?.data?.Y2 || [];

      const pointLen = Math.max(y1.length, y2.length);
      const finalX = (x && x.length > 0) ? x : Array.from({ length: pointLen }, (_, i) => i);

      setPlotData({
        x: finalX,
        y1,
        y2,
        x_label: results?.x_label || block?.data?.XLabel || 'X',
        y1_label: results?.y1_label || block?.data?.Y1Label || 'Y1',
        y2_label: results?.y2_label || block?.data?.Y2Label || 'Y2',
        y1_name: results?.y1_name || block?.data?.Y1TraceName || 'Signal 1',
        y2_name: results?.y2_name || block?.data?.Y2TraceName || 'Signal 2',
        x_min: results?.x_min ?? block?.data?.XMin,
        x_max: results?.x_max ?? block?.data?.XMax,
        y1_min: results?.y1_min ?? block?.data?.Y1Min,
        y1_max: results?.y1_max ?? block?.data?.Y1Max,
        y2_min: results?.y2_min ?? block?.data?.Y2Min,
        y2_max: results?.y2_max ?? block?.data?.Y2Max,
        x_log: results?.x_log ?? block?.data?.XLog ?? false,
        y1_log: results?.y1_log ?? block?.data?.Y1Log ?? false,
        y2_log: results?.y2_log ?? block?.data?.Y2Log ?? false
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

  const colorY1 = '#3b82f6'; // Blue
  const colorY2 = '#f97316'; // Orange

  const settings = useContext(SettingsContext);
  const downsampleThreshold = settings?.plot_downsample_threshold ?? 10000;
  const downsampleTarget = settings?.plot_downsample_target ?? 2000;

  const traces: any[] = [];

  if (plotData.y1 && plotData.y1.length > 0) {
    let traceX = plotData.x;
    let traceY1 = plotData.y1;
    if (downsampleThreshold > 0 && traceY1.length > downsampleThreshold) {
      const downsampled = downsampleLTTB(traceX, traceY1, downsampleTarget);
      traceX = downsampled.x;
      traceY1 = downsampled.y;
    }
    const pointCount = traceY1.length;
    traces.push({
      x: traceX,
      y: traceY1,
      name: plotData.y1_name || 'Signal 1',
      type: pointCount > 5000 ? 'scattergl' : 'scatter',
      mode: pointCount <= 300 ? 'lines+markers' : 'lines',
      marker: pointCount <= 300 ? { size: 4, color: colorY1 } : undefined,
      line: { color: colorY1, width: 2 },
      yaxis: 'y'
    });
  }

  if (plotData.y2 && plotData.y2.length > 0) {
    let traceX = plotData.x;
    let traceY2 = plotData.y2;
    if (downsampleThreshold > 0 && traceY2.length > downsampleThreshold) {
      const downsampled = downsampleLTTB(traceX, traceY2, downsampleTarget);
      traceX = downsampled.x;
      traceY2 = downsampled.y;
    }
    const pointCount = traceY2.length;
    traces.push({
      x: traceX,
      y: traceY2,
      name: plotData.y2_name || 'Signal 2',
      type: pointCount > 5000 ? 'scattergl' : 'scatter',
      mode: pointCount <= 300 ? 'lines+markers' : 'lines',
      marker: pointCount <= 300 ? { size: 4, color: colorY2 } : undefined,
      line: { color: colorY2, width: 2, dash: 'solid' },
      yaxis: 'y2'
    });
  }

  const xaxis: any = {
    title: { text: plotData.x_label || 'X', font: { size: 13, color: textColor } },
    type: plotData.x_log ? 'log' : 'linear',
    tickfont: { size: 11, color: textColor },
    gridcolor: gridColor,
    zerolinecolor: gridColor,
    exponentformat: 'SI'
  };
  if (plotData.x_min != null && plotData.x_max != null) {
    xaxis.range = plotData.x_log ? [Math.log10(plotData.x_min), Math.log10(plotData.x_max)] : [plotData.x_min, plotData.x_max];
  } else {
    xaxis.autorange = true;
  }

  const yaxis: any = {
    title: { text: plotData.y1_label || 'Y1', font: { size: 13, color: colorY1 } },
    tickfont: { size: 11, color: colorY1 },
    type: plotData.y1_log ? 'log' : 'linear',
    gridcolor: gridColor,
    zerolinecolor: gridColor,
    exponentformat: 'SI'
  };
  if (plotData.y1_min != null && plotData.y1_max != null) {
    yaxis.range = plotData.y1_log ? [Math.log10(plotData.y1_min), Math.log10(plotData.y1_max)] : [plotData.y1_min, plotData.y1_max];
  } else {
    yaxis.autorange = true;
  }

  const yaxis2: any = {
    title: { text: plotData.y2_label || 'Y2', font: { size: 13, color: colorY2 } },
    tickfont: { size: 11, color: colorY2 },
    type: plotData.y2_log ? 'log' : 'linear',
    overlaying: 'y',
    side: 'right',
    showgrid: false,
    zeroline: false,
    exponentformat: 'SI'
  };
  if (plotData.y2_min != null && plotData.y2_max != null) {
    yaxis2.range = plotData.y2_log ? [Math.log10(plotData.y2_min), Math.log10(plotData.y2_max)] : [plotData.y2_min, plotData.y2_max];
  } else {
    yaxis2.autorange = true;
  }

  const layout: any = {
    width: width || 300,
    height: height || 250,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { l: 45, r: 45, t: 25, b: 35 },
    dragmode: dragMode,
    xaxis,
    yaxis,
    yaxis2,
    showlegend: true,
    legend: {
      x: 0.5,
      xanchor: 'center',
      y: 1.15,
      orientation: 'h',
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
