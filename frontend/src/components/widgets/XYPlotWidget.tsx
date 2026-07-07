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

interface XYPlotWidgetProps {
  nodeId: string;
  xLabel?: string;
  yLabel?: string;
}

export const XYPlotWidget = ({ nodeId, xLabel = 'X', yLabel = 'Y' }: XYPlotWidgetProps) => {

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
          nodeId={nodeId}
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
  nodeId: string;
  xLabel: string;
  yLabel: string;
  width: number;
  height: number;
}

const PlotlyXYRenderer = ({ nodeId, xLabel, yLabel, width, height }: PlotlyXYRendererProps) => {
  const { getNode } = useReactFlow();
  const [plotData, setPlotData] = useState<{x: any[], y: any[]}>({ x: [], y: [] });
  const [labels, setLabels] = useState({ x: xLabel, y: yLabel });

  // Initialize and listen to high-frequency telemetry events directly
  useEffect(() => {
    const updateChart = (eventResults?: any) => {
      const node = getNode(nodeId);
      if (!node && !eventResults) return;
      
      const results = eventResults || node?.data?.results;
      if (!results) return;

      const x = results.x || [];
      const y = results.y || [];
      
      if (x.length > 0 && y.length > 0) {
        setPlotData({ x, y });
      }

      setLabels({
        x: results.x_label || xLabel,
        y: results.y_label || yLabel
      });
    };

    // Initial update
    updateChart();

    const eventName = `telemetry-${nodeId}`;
    const handleTelemetry = (e: any) => {
      updateChart(e.detail?.results);
    };
    
    window.addEventListener(eventName, handleTelemetry);
    
    return () => {
      window.removeEventListener(eventName, handleTelemetry);
    };
  }, [nodeId, xLabel, yLabel, getNode]);

  const isLight = document.documentElement.classList.contains('light-theme');
  const textColor = isLight ? '#475569' : '#94a3b8';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';

  return (
    <div className="nodrag" style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      <Plot
        data={[
          {
            x: plotData.x,
            y: plotData.y,
            type: 'scattergl',
            mode: 'lines',
            line: { color: '#60a5fa', width: 2 },
            hoverinfo: 'x+y'
          }
        ]}
        layout={{
          width: Math.max(10, width - 12),
          height: Math.max(10, height - 12),
          margin: { l: 45, r: 15, t: 15, b: 35 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          xaxis: {
            title: labels.x,
            titlefont: { size: 10, color: textColor },
            tickfont: { size: 9, color: textColor },
            gridcolor: gridColor,
            zerolinecolor: gridColor
          },
          yaxis: {
            title: labels.y,
            titlefont: { size: 10, color: textColor },
            tickfont: { size: 9, color: textColor },
            gridcolor: gridColor,
            zerolinecolor: gridColor
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
