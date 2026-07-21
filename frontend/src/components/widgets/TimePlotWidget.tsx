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
}

export const TimePlotWidget = ({ blockId, strokeColor = '#34d399', dataKey = 'waveform' }: TimePlotWidgetProps) => {
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
}

const PlotlyTimeRenderer = ({ blockId, strokeColor, dataKey, width, height }: PlotlyTimeRendererProps) => {
  const { getNode } = useReactFlow();
  const [plotData, setPlotData] = useState<any[]>([]);

  // Initialize and listen to high-frequency telemetry events directly to bypass full block render cycle
  useEffect(() => {
    const updateChart = (eventResults?: any) => {
      const block = getNode(blockId);
      if (!block && !eventResults) return;
      
      const points = eventResults?.[dataKey] || (block?.data?.results as any)?.[dataKey];
      if (points && Array.isArray(points)) {
        setPlotData(points);
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
          xaxis: {
            title: 'Time Index',
            titlefont: { size: 14, color: textColor },
            tickfont: { size: 12, color: textColor },
            gridcolor: gridColor,
            zerolinecolor: gridColor,
            exponentformat: 'SI',
            minexponent: 3
          },
          yaxis: {
            title: 'Value',
            titlefont: { size: 14, color: textColor },
            tickfont: { size: 12, color: textColor },
            gridcolor: gridColor,
            zerolinecolor: gridColor,
            exponentformat: 'SI',
            minexponent: 3
          }
        }}
        config={{
          displayModeBar: 'hover',
          displaylogo: false,
          responsive: true
        }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={false}
      />
    </div>
  );
};
