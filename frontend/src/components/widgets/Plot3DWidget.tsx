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
  return colormapName;
};

interface Plot3DWidgetProps {
  blockId: string;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

export const Plot3DWidget = ({ blockId, onChange, savedLayout }: Plot3DWidgetProps) => {
  return (
    <ResizablePlotContainer
      minHeight="180px"
      background="var(--input-bg)"
      padding="6px"
      borderRadius="6px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => (
        <Plotly3DRenderer
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

interface Plotly3DRendererProps {
  blockId: string;
  width: number;
  height: number;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

const Plotly3DRenderer = ({ blockId, width, height }: Plotly3DRendererProps) => {
  const { getNode } = useReactFlow();

  const [plotData, setPlotData] = useState<{
    z: any;
    x?: any[];
    y?: any[];
    plot_type?: string;
    colormap?: string;
    x_label?: string;
    y_label?: string;
    z_label?: string;
  }>({ z: [] });

  useEffect(() => {
    const updateChart = (eventResults?: any) => {
      const block = getNode(blockId);
      if (!block && !eventResults) return;

      const results = eventResults || block?.data?.results;
      const z = results?.z || block?.data?.Z || [];

      setPlotData({
        z,
        x: results?.x || block?.data?.X,
        y: results?.y || block?.data?.Y,
        plot_type: (results?.plot_type || block?.data?.PlotType || 'surface').toLowerCase(),
        colormap: results?.colormap || block?.data?.Colormap || 'Viridis',
        x_label: results?.x_label || block?.data?.XLabel || 'X',
        y_label: results?.y_label || block?.data?.YLabel || 'Y',
        z_label: results?.z_label || block?.data?.ZLabel || 'Z'
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
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.12)' : 'rgba(255, 255, 255, 0.12)';

  let traces: any[] = [];
  if (plotData.z && (Array.isArray(plotData.z) ? plotData.z.length > 0 : true)) {
    const pType = plotData.plot_type;
    const colorscale = getPlotlyColorscale(plotData.colormap || 'Viridis');

    if (pType === 'scatter3d') {
      traces = [{
        type: 'scatter3d',
        mode: 'markers',
        x: plotData.x || [],
        y: plotData.y || [],
        z: plotData.z || [],
        marker: {
          size: 4,
          color: plotData.z,
          colorscale,
          colorbar: { len: 0.8, thickness: 12, tickfont: { size: 9, color: textColor } }
        }
      }];
    } else if (pType === 'mesh3d') {
      traces = [{
        type: 'mesh3d',
        x: plotData.x || [],
        y: plotData.y || [],
        z: plotData.z || [],
        colorscale,
        intensity: plotData.z
      }];
    } else {
      // Default: surface
      traces = [{
        type: 'surface',
        z: plotData.z,
        x: plotData.x && plotData.x.length > 0 ? plotData.x : undefined,
        y: plotData.y && plotData.y.length > 0 ? plotData.y : undefined,
        colorscale,
        colorbar: { len: 0.8, thickness: 12, tickfont: { size: 9, color: textColor } }
      }];
    }
  }

  const layout: any = {
    width: width || 320,
    height: height || 280,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { l: 10, r: 10, t: 10, b: 10 },
    scene: {
      xaxis: {
        title: { text: plotData.x_label || 'X', font: { size: 11, color: textColor } },
        tickfont: { size: 9, color: textColor },
        gridcolor: gridColor,
        backgroundcolor: 'transparent'
      },
      yaxis: {
        title: { text: plotData.y_label || 'Y', font: { size: 11, color: textColor } },
        tickfont: { size: 9, color: textColor },
        gridcolor: gridColor,
        backgroundcolor: 'transparent'
      },
      zaxis: {
        title: { text: plotData.z_label || 'Z', font: { size: 11, color: textColor } },
        tickfont: { size: 9, color: textColor },
        gridcolor: gridColor,
        backgroundcolor: 'transparent'
      },
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
          displaylogo: false
        }}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};
