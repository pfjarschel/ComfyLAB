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

interface TimePlotWidgetProps {
  blockId: string;
  strokeColor?: string;
  dataKey?: string;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

export const TimePlotWidget = ({ blockId, strokeColor = '#34d399', dataKey = 'waveform', onChange, savedLayout }: TimePlotWidgetProps) => {
  return (
    <ResizablePlotContainer 
      minHeight="120px"
      background="var(--input-bg)" 
      padding="6px" 
      borderRadius="6px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => (
        <PlotlyTimeRenderer
          blockId={blockId}
          strokeColor={strokeColor}
          dataKey={dataKey}
          width={width}
          height={height}
          onChange={onChange}
          savedLayout={savedLayout}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface PlotlyTimeRendererProps {
  blockId: string;
  strokeColor: string;
  dataKey: string;
  width: number;
  height: number;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

const PlotlyTimeRenderer = ({ blockId, strokeColor, dataKey, width, height, onChange, savedLayout }: PlotlyTimeRendererProps) => {
  const { getNode } = useReactFlow();
  const [plotData, setPlotData] = useState<any[]>([]);
  const [limits, setLimits] = useState<{x_min?: number, x_max?: number, y_min?: number, y_max?: number}>({});

  // Initialize and listen to high-frequency telemetry events directly to bypass full block render cycle
  useEffect(() => {
    const updateChart = (eventResults?: any) => {
      const block = getNode(blockId);
      if (!block && !eventResults) return;
      
      const results = eventResults || block?.data?.results;
      const points = results?.[dataKey];
      
      if (points && Array.isArray(points)) {
        setPlotData(points);
      }
      
      if (results) {
        setLimits({
          x_min: results.x_min,
          x_max: results.x_max,
          y_min: results.y_min,
          y_max: results.y_max
        });
      }
    };

    // Initial update
    updateChart();

    const eventName = `telemetry-${blockId}`;
    const handleTelemetry = (e: any) => {
      updateChart(e.detail?.results);
    };
    
    window.addEventListener(eventName, handleTelemetry);
    
    return () => {
      window.removeEventListener(eventName, handleTelemetry);
    };
  }, [blockId, dataKey, getNode]);

  const isLight = document.documentElement.classList.contains('light-theme');
  const textColor = isLight ? '#475569' : '#94a3b8';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';

  const xaxis: any = {
    title: 'Time Index',
    titlefont: { size: 14, color: textColor },
    tickfont: { size: 12, color: textColor },
    gridcolor: gridColor,
    zerolinecolor: gridColor,
    exponentformat: 'SI',
    minexponent: 3
  };

  if (limits.x_min != null && limits.x_max != null) {
    xaxis.range = [limits.x_min, limits.x_max];
  } else if (savedLayout && savedLayout['xaxis.autorange']) {
    xaxis.autorange = true;
  } else if (savedLayout && savedLayout['xaxis.range[0]'] != null && savedLayout['xaxis.range[1]'] != null) {
    xaxis.range = [savedLayout['xaxis.range[0]'], savedLayout['xaxis.range[1]']];
  }

  const yaxis: any = {
    title: 'Value',
    titlefont: { size: 14, color: textColor },
    tickfont: { size: 12, color: textColor },
    gridcolor: gridColor,
    zerolinecolor: gridColor,
    exponentformat: 'SI',
    minexponent: 3
  };

  if (limits.y_min != null && limits.y_max != null) {
    yaxis.range = [limits.y_min, limits.y_max];
  } else if (savedLayout && savedLayout['yaxis.autorange']) {
    yaxis.autorange = true;
  } else if (savedLayout && savedLayout['yaxis.range[0]'] != null && savedLayout['yaxis.range[1]'] != null) {
    yaxis.range = [savedLayout['yaxis.range[0]'], savedLayout['yaxis.range[1]']];
  }

  return (
    <div className="nodrag" style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      <Plot
        data={[
          {
            y: plotData,
            type: 'scattergl', // Use scattergl for high performance rendering of large datasets
            mode: 'lines',
            line: { color: strokeColor, width: 1.5 },
            hoverinfo: 'y'
          }
        ]}
        layout={{
          width: Math.max(10, width - 12),
          height: Math.max(10, height - 12),
          margin: { l: 55, r: 15, t: 15, b: 40 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          uirevision: true,
          xaxis,
          yaxis
        }}
        config={{
          displayModeBar: 'hover',
          displaylogo: false,
          responsive: true
        }}
        onRelayout={(e: any) => {
          if (onChange) {
            const newLayout = { ...(savedLayout || {}), ...e };
            if (e['xaxis.autorange']) {
              delete newLayout['xaxis.range[0]'];
              delete newLayout['xaxis.range[1]'];
            }
            if (e['xaxis.range[0]'] !== undefined) {
              delete newLayout['xaxis.autorange'];
            }
            if (e['yaxis.autorange']) {
              delete newLayout['yaxis.range[0]'];
              delete newLayout['yaxis.range[1]'];
            }
            if (e['yaxis.range[0]'] !== undefined) {
              delete newLayout['yaxis.autorange'];
            }
            onChange('plot_layout', newLayout);
          }
        }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={false}
      />
    </div>
  );
};
