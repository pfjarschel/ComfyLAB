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
  blockId: string;
  xLabel?: string;
  yLabel?: string;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

export const HeatmapPlotWidget = ({ blockId, xLabel = 'X', yLabel = 'Y', onChange, savedLayout }: HeatmapPlotWidgetProps) => {
  return (
    <ResizablePlotContainer 
      minHeight="150px" 
      background="var(--input-bg)" 
      padding="6px" 
      borderRadius="6px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => (
        <PlotlyHeatmapRenderer
          blockId={blockId}
          initialXLabel={xLabel}
          initialYLabel={yLabel}
          width={width}
          height={height}
          onChange={onChange}
          savedLayout={savedLayout}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface PlotlyHeatmapRendererProps {
  blockId: string;
  initialXLabel: string;
  initialYLabel: string;
  width: number;
  height: number;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

const PlotlyHeatmapRenderer = ({ blockId, initialXLabel, initialYLabel, width, height, onChange, savedLayout }: PlotlyHeatmapRendererProps) => {
  const { getNode } = useReactFlow();
  
  const [plotData, setPlotData] = useState<{ z: any[][], x?: any[], y?: any[] }>({ z: [] });
  const [labels, setLabels] = useState({ x: initialXLabel, y: initialYLabel, z: 'Z' });
  const [plotType, setPlotType] = useState<'heatmap' | 'contour'>('heatmap');
  const [colormap, setColormap] = useState('Viridis');
  const [interpolation, setInterpolation] = useState<'fast' | 'best' | false>(false);
  const [limits, setLimits] = useState<{x_min?: number, x_max?: number, y_min?: number, y_max?: number, z_min?: number, z_max?: number}>({});

  useEffect(() => {
    const updateChart = (eventResults?: any) => {
      const block = getNode(blockId);
      if (!block && !eventResults) return;
      
      const results = eventResults || block?.data?.results;
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
        y: results.y_label || initialYLabel,
        z: results.z_label || 'Z'
      });

      setLimits({
        x_min: results.x_min,
        x_max: results.x_max,
        y_min: results.y_min,
        y_max: results.y_max,
        z_min: results.z_min,
        z_max: results.z_max
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

    const eventName = `telemetry-${blockId}`;
    const handleTelemetry = (e: any) => {
      updateChart(e.detail?.results);
    };
    
    window.addEventListener(eventName, handleTelemetry);
    
    return () => {
      window.removeEventListener(eventName, handleTelemetry);
    };
  }, [blockId, initialXLabel, initialYLabel, getNode]);

  const isLight = document.documentElement.classList.contains('light-theme');
  const textColor = isLight ? '#475569' : '#94a3b8';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';

  const xaxis: any = {
    title: labels.x,
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
    title: labels.y,
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

  const trace: any = {
    z: plotData.z,
    x: plotData.x,
    y: plotData.y,
    type: plotType,
    colorscale: getPlotlyColorscale(colormap) as any,
    zsmooth: plotType === 'heatmap' ? interpolation : false, // Interpolation is for heatmaps
    showscale: true,
    colorbar: {
      title: labels.z,
      titlefont: { size: 14, color: textColor },
      tickfont: { size: 12, color: textColor },
      exponentformat: 'SI',
      minexponent: 3
    }
  };

  if (limits.z_min != null && limits.z_max != null) {
    trace.zmin = limits.z_min;
    trace.zmax = limits.z_max;
  }

  return (
    <div className="nodrag" style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      <Plot
        data={[trace]}
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
