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

// Custom colormaps fallback in case Plotly doesn't perfectly match our specific Python strings
const COLORMAPS: Record<string, string[]> = {
  Viridis: ['#440154', '#482878', '#3e4989', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6ece58', '#b5de2b', '#fde725'],
  Plasma: ['#0d0887', '#46039f', '#7201a8', '#9c179e', '#bd3786', '#d8576b', '#ed7953', '#fb9f3a', '#fdca26', '#f0f921'],
  Hot: ['#0b0000', '#560000', '#a10000', '#eb0000', '#ff3300', '#ff7f00', '#ffcc00', '#ffff33', '#ffff99', '#ffffff'],
  Cividis: ['#00204c', '#143160', '#2e4370', '#48577f', '#646c8e', '#82829d', '#a19aab', '#c0b4ba', '#dfcfca', '#ffead9'],
  Gray: ['#000000', '#1c1c1c', '#383838', '#555555', '#717171', '#8d8d8d', '#aaaaaa', '#c6c6c6', '#e2e2e2', '#ffffff'],
  Jet: ['#00007f', '#0000ff', '#007fff', '#00ffff', '#7fff7f', '#ffff00', '#ff7f00', '#ff0000', '#7f0000'],
  Rainbow: ['#ff0000', '#ff7f00', '#ffff00', '#00ff00', '#0000ff', '#4b0082', '#9400d3'],
  Inferno: ['#000004', '#160b39', '#420a68', '#6a176e', '#932667', '#bc3754', '#dd513a', '#f37819', '#fca50a', '#fcffa4'],
  Bone: ['#000000', '#1b1b24', '#363648', '#52526c', '#6d6d90', '#8989a3', '#a4a4b7', '#bfbfcb', '#dadadf', '#ffffff'],
  Wave: ['#00429d', '#2e59a8', '#4771b2', '#5d8abd', '#73a2c6', '#8abccf', '#a5d5d8', '#c0eee1', '#ffffe0']
};

const getPlotlyColorscale = (colormapName: string) => {
  const colors = COLORMAPS[colormapName] || COLORMAPS['Viridis'];
  return colors.map((c, i) => [i / (colors.length - 1), c]);
};

interface HeatmapPlotWidgetProps {
  nodeId: string;
  xLabel?: string;
  yLabel?: string;
}

export const HeatmapPlotWidget = ({ nodeId, xLabel = 'X', yLabel = 'Y' }: HeatmapPlotWidgetProps) => {
  return (
    <ResizablePlotContainer 
      minHeight="150px" 
      background="var(--input-bg)" 
      padding="6px" 
      borderRadius="6px"
      border="1px solid var(--node-border)"
    >
      {(width, height) => (
        <PlotlyHeatmapRenderer
          nodeId={nodeId}
          initialXLabel={xLabel}
          initialYLabel={yLabel}
          width={width}
          height={height}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface PlotlyHeatmapRendererProps {
  nodeId: string;
  initialXLabel: string;
  initialYLabel: string;
  width: number;
  height: number;
}

const PlotlyHeatmapRenderer = ({ nodeId, initialXLabel, initialYLabel, width, height }: PlotlyHeatmapRendererProps) => {
  const { getNode } = useReactFlow();
  
  const [plotData, setPlotData] = useState<{ z: any[][], x?: any[], y?: any[] }>({ z: [] });
  const [labels, setLabels] = useState({ x: initialXLabel, y: initialYLabel });
  const [plotType, setPlotType] = useState<'heatmap' | 'contour'>('heatmap');
  const [colormap, setColormap] = useState('Viridis');
  const [interpolation, setInterpolation] = useState<'fast' | 'best' | false>(false);

  useEffect(() => {
    const updateChart = (eventResults?: any) => {
      const node = getNode(nodeId);
      if (!node && !eventResults) return;
      
      const results = eventResults || node?.data?.results;
      if (!results) return;

      const z = results.z || [];
      if (z.length > 0) {
        setPlotData({
          z: z,
          x: results.x?.length ? results.x : undefined,
          y: results.y?.length ? results.y : undefined
        });
      }

      setLabels({
        x: results.x_label || initialXLabel,
        y: results.y_label || initialYLabel
      });

      setColormap(results.colormap || 'Viridis');
      
      const pType = results.plot_type?.toLowerCase() === 'contour' ? 'contour' : 'heatmap';
      setPlotType(pType);

      const interpStr = results.interpolation?.toLowerCase() || '';
      if (interpStr.includes('best')) {
        setInterpolation('best');
      } else if (interpStr.includes('fast') || interpStr.includes('good')) {
        setInterpolation('fast');
      } else {
        setInterpolation(false);
      }
    };

    updateChart();

    const eventName = `telemetry-${nodeId}`;
    const handleTelemetry = (e: any) => {
      updateChart(e.detail?.results);
    };
    
    window.addEventListener(eventName, handleTelemetry);
    
    return () => {
      window.removeEventListener(eventName, handleTelemetry);
    };
  }, [nodeId, initialXLabel, initialYLabel, getNode]);

  const isLight = document.documentElement.classList.contains('light-theme');
  const textColor = isLight ? '#475569' : '#94a3b8';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';

  return (
    <div className="nodrag" style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      <Plot
        data={[
          {
            z: plotData.z,
            x: plotData.x,
            y: plotData.y,
            type: plotType,
            colorscale: getPlotlyColorscale(colormap) as any,
            zsmooth: plotType === 'heatmap' ? interpolation : false, // Interpolation is for heatmaps
            showscale: true,
            colorbar: {
              tickfont: { size: 9, color: textColor },
              exponentformat: 'SI',
              minexponent: 3
            }
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
            zerolinecolor: gridColor,
            exponentformat: 'SI',
            minexponent: 3
          },
          yaxis: {
            title: labels.y,
            titlefont: { size: 10, color: textColor },
            tickfont: { size: 9, color: textColor },
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
