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
const COLORMAPS: Record<string, string[]> = {
  Plotly3: ["#0508b8", "#1910d8", "#3c19f0", "#6b1cfb", "#981cfd", "#bf1cfd", "#dd2bfd", "#f246fe", "#fc67fd", "#fe88fc", "#fea5fd", "#febefe", "#fec3fe"],
  Inferno: ["#000004", "#1b0c41", "#4a0c6b", "#781c6d", "#a52c60", "#cf4446", "#ed6925", "#fb9b06", "#f7d13d", "#fcffa4"],
  Turbo: ["#30123b", "#4145ab", "#4675ed", "#39a2fc", "#1bcfd4", "#24eca6", "#61fc6c", "#a4fc3b", "#d1e834", "#f3c63a", "#fe9b2d", "#f36315", "#d93806", "#b11901", "#7a0402"],
  Agsunset: ["rgb(75, 41, 145)", "rgb(135, 44, 162)", "rgb(192, 54, 157)", "rgb(234, 79, 136)", "rgb(250, 120, 118)", "rgb(246, 169, 122)", "rgb(237, 217, 163)"],
  Phase: ["rgb(167, 119, 12)", "rgb(197, 96, 51)", "rgb(217, 67, 96)", "rgb(221, 38, 163)", "rgb(196, 59, 224)", "rgb(153, 97, 244)", "rgb(95, 127, 228)", "rgb(40, 144, 183)", "rgb(15, 151, 136)", "rgb(39, 153, 79)", "rgb(119, 141, 17)", "rgb(167, 119, 12)"]
};

const getPlotlyColorscale = (colormapName: string) => {
  if (COLORMAPS[colormapName]) {
    const colors = COLORMAPS[colormapName];
    return colors.map((c, i) => [i / (colors.length - 1), c]);
  }
  return colormapName; // Pass natively to plotly if not in dict
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
              tickfont: { size: 12, color: textColor },
              exponentformat: 'SI',
              minexponent: 3
            }
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
            title: labels.x,
            titlefont: { size: 14, color: textColor },
            tickfont: { size: 12, color: textColor },
            gridcolor: gridColor,
            zerolinecolor: gridColor,
            exponentformat: 'SI',
            minexponent: 3
          },
          yaxis: {
            title: labels.y,
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
