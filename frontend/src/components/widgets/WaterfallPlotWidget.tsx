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

import { useEffect, useState, useRef } from 'react';
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

interface WaterfallPlotWidgetProps {
  blockId: string;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

export const WaterfallPlotWidget = ({ blockId, onChange, savedLayout }: WaterfallPlotWidgetProps) => {
  return (
    <ResizablePlotContainer
      minHeight="180px"
      background="var(--input-bg)"
      padding="6px"
      borderRadius="6px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => (
        <PlotlyWaterfallRenderer
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

interface PlotlyWaterfallRendererProps {
  blockId: string;
  width: number;
  height: number;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

const PlotlyWaterfallRenderer = ({ blockId, width, height, onChange, savedLayout }: PlotlyWaterfallRendererProps) => {
  const { getNode } = useReactFlow();

  const historyRef = useRef<any[][]>([]);
  const [plotData, setPlotData] = useState<{
    z: any[][];
    x?: any[];
    colormap?: string;
    x_label?: string;
    y_label?: string;
    z_label?: string;
    z_min?: number;
    z_max?: number;
  }>({ z: [] });

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
      const rawSpec = results?.spectrum || block?.data?.Spectrum || [];
      const xCoords = results?.x_coords || block?.data?.XCoords;
      const maxHistory = results?.max_history ?? block?.data?.MaxHistory ?? 50;

      let currentMatrix: any[][];

      // If rawSpec is 2D, display directly as a matrix
      if (Array.isArray(rawSpec) && rawSpec.length > 0 && Array.isArray(rawSpec[0])) {
        currentMatrix = rawSpec;
        historyRef.current = rawSpec.slice(-maxHistory);
      } else if (Array.isArray(rawSpec) && rawSpec.length > 0) {
        // 1D spectrum sweep: append to rolling buffer
        const newHist = [...historyRef.current, rawSpec];
        if (newHist.length > maxHistory) {
          newHist.splice(0, newHist.length - maxHistory);
        }
        historyRef.current = newHist;
        currentMatrix = newHist;
      } else {
        currentMatrix = historyRef.current;
      }

      setPlotData({
        z: currentMatrix,
        x: xCoords,
        colormap: results?.colormap || block?.data?.Colormap || 'Viridis',
        x_label: results?.x_label || block?.data?.XLabel || 'Frequency / Wavelength',
        y_label: results?.y_label || block?.data?.YLabel || 'Sweep / Time',
        z_label: results?.z_label || block?.data?.ZLabel || 'Intensity',
        z_min: results?.z_min ?? block?.data?.ZMin,
        z_max: results?.z_max ?? block?.data?.ZMax
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

  let traces: any[] = [];
  if (plotData.z && plotData.z.length > 0) {
    const colorscale = getPlotlyColorscale(plotData.colormap || 'Viridis');
    traces = [{
      z: plotData.z,
      x: plotData.x && plotData.x.length > 0 ? plotData.x : undefined,
      type: 'heatmap',
      colorscale,
      zmin: plotData.z_min ?? undefined,
      zmax: plotData.z_max ?? undefined,
      colorbar: {
        title: { text: plotData.z_label || 'Intensity', side: 'right', font: { size: 10, color: textColor } },
        len: 0.8,
        thickness: 12,
        tickfont: { size: 9, color: textColor }
      }
    }];
  }

  const layout: any = {
    width: width || 320,
    height: height || 280,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { l: 45, r: 40, t: 25, b: 35 },
    dragmode: dragMode,
    xaxis: {
      title: { text: plotData.x_label || 'Frequency / Wavelength', font: { size: 13, color: textColor } },
      tickfont: { size: 11, color: textColor },
      gridcolor: gridColor,
      zerolinecolor: gridColor,
      exponentformat: 'SI',
      autorange: true
    },
    yaxis: {
      title: { text: plotData.y_label || 'Sweep / Time', font: { size: 13, color: textColor } },
      tickfont: { size: 11, color: textColor },
      gridcolor: gridColor,
      zerolinecolor: gridColor,
      autorange: 'reversed' // newest on top or bottom
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
