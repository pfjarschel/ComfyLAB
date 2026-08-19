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
  blockId: string;
  xLabel?: string;
  yLabel?: string;
  xLog?: boolean;
  yLog?: boolean;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

export const XYPlotWidget = ({ blockId, xLabel = 'X', yLabel = 'Y', xLog = false, yLog = false, onChange, savedLayout }: XYPlotWidgetProps) => {

  return (
    <ResizablePlotContainer 
      minHeight="150px" 
      background="var(--input-bg)" 
      padding="6px" 
      borderRadius="6px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => (
        <PlotlyXYRenderer
          blockId={blockId}
          xLabel={xLabel}
          yLabel={yLabel}
          xLog={xLog}
          yLog={yLog}
          width={width}
          height={height}
          onChange={onChange}
          savedLayout={savedLayout}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface PlotlyXYRendererProps {
  blockId: string;
  xLabel: string;
  yLabel: string;
  xLog?: boolean;
  yLog?: boolean;
  width: number;
  height: number;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

const PlotlyXYRenderer = ({ blockId, xLabel, yLabel, xLog = false, yLog = false, width, height, onChange, savedLayout }: PlotlyXYRendererProps) => {
  const { getNode } = useReactFlow();
  const [plotData, setPlotData] = useState<{x: any[], y: any[], labels?: any[]}>({ x: [], y: [] });
  const [labels, setLabels] = useState({ x: xLabel, y: yLabel });
  const [limits, setLimits] = useState<{x_min?: number, x_max?: number, y_min?: number, y_max?: number}>({});
  const [dragMode, setDragMode] = useState<string>(savedLayout?.dragmode || 'zoom');
  const [isXLog, setIsXLog] = useState<boolean>(Boolean(xLog));
  const [isYLog, setIsYLog] = useState<boolean>(Boolean(yLog));

  useEffect(() => {
    if (xLog !== undefined) {
      setIsXLog(Boolean(xLog));
    }
  }, [xLog]);

  useEffect(() => {
    if (yLog !== undefined) {
      setIsYLog(Boolean(yLog));
    }
  }, [yLog]);

  useEffect(() => {
    if (savedLayout?.dragmode && savedLayout.dragmode !== dragMode) {
      setDragMode(savedLayout.dragmode);
    }
  }, [savedLayout?.dragmode]);

  // Initialize and listen to high-frequency telemetry events directly
  useEffect(() => {
    const updateChart = (eventResults?: any) => {
      const block = getNode(blockId);
      if (!block && !eventResults) return;
      
      const results = eventResults || block?.data?.results;
      const x = results?.x || block?.data?.x || [];
      const y = results?.y || block?.data?.y || [];
      const traceLabels = results?.labels || [];
      
      if (y.length > 0) {
        const finalX = x.length > 0 ? x : Array.from({ length: y.length }, (_, i) => i);
        setPlotData({ x: finalX, y, labels: traceLabels });
      }

      setLabels({
        x: results?.x_label || xLabel,
        y: results?.y_label || yLabel
      });

      setLimits({
        x_min: results?.x_min,
        x_max: results?.x_max,
        y_min: results?.y_min,
        y_max: results?.y_max
      });

      if (results?.x_log !== undefined) {
        setIsXLog(Boolean(results.x_log));
      } else if (block?.data?.XLog !== undefined) {
        setIsXLog(Boolean(block.data.XLog));
      }
      if (results?.y_log !== undefined) {
        setIsYLog(Boolean(results.y_log));
      } else if (block?.data?.YLog !== undefined) {
        setIsYLog(Boolean(block.data.YLog));
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
  }, [blockId, getNode, xLabel, yLabel]);

  const isLight = document.documentElement.classList.contains('light-theme');
  const textColor = isLight ? '#475569' : '#94a3b8';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';

  const xaxis: any = {
    title: { text: labels.x || 'X', font: { size: 14, color: textColor } },
    type: isXLog ? 'log' : 'linear',
    tickfont: { size: 12, color: textColor },
    gridcolor: gridColor,
    zerolinecolor: gridColor,
    exponentformat: 'SI',
    minexponent: 3
  };

  if (limits.x_min != null && limits.x_max != null) {
    if (isXLog) {
      if (limits.x_min > 0 && limits.x_max > 0) {
        xaxis.range = [Math.log10(limits.x_min), Math.log10(limits.x_max)];
      }
    } else {
      xaxis.range = [limits.x_min, limits.x_max];
    }
  } else if (savedLayout && !savedLayout['xaxis.autorange'] && savedLayout['xaxis.range[0]'] != null && savedLayout['xaxis.range[1]'] != null) {
    xaxis.range = [savedLayout['xaxis.range[0]'], savedLayout['xaxis.range[1]']];
  } else if (savedLayout && !savedLayout['xaxis.autorange'] && Array.isArray(savedLayout['xaxis.range']) && savedLayout['xaxis.range'].length === 2) {
    xaxis.range = savedLayout['xaxis.range'];
  } else {
    xaxis.autorange = true;
  }

  const yaxis: any = {
    title: { text: labels.y || 'Y', font: { size: 14, color: textColor } },
    type: isYLog ? 'log' : 'linear',
    tickfont: { size: 12, color: textColor },
    gridcolor: gridColor,
    zerolinecolor: gridColor,
    exponentformat: 'SI',
    minexponent: 3
  };

  if (limits.y_min != null && limits.y_max != null) {
    if (isYLog) {
      if (limits.y_min > 0 && limits.y_max > 0) {
        yaxis.range = [Math.log10(limits.y_min), Math.log10(limits.y_max)];
      }
    } else {
      yaxis.range = [limits.y_min, limits.y_max];
    }
  } else if (savedLayout && !savedLayout['yaxis.autorange'] && savedLayout['yaxis.range[0]'] != null && savedLayout['yaxis.range[1]'] != null) {
    yaxis.range = [savedLayout['yaxis.range[0]'], savedLayout['yaxis.range[1]']];
  } else if (savedLayout && !savedLayout['yaxis.autorange'] && Array.isArray(savedLayout['yaxis.range']) && savedLayout['yaxis.range'].length === 2) {
    yaxis.range = savedLayout['yaxis.range'];
  } else {
    yaxis.autorange = true;
  }

  const colors = ['#60a5fa', '#f87171', '#34d399', '#fbbf24', '#a78bfa', '#2dd4bf'];
  
  let plotTraces: any[] = [];
  if (plotData.y && plotData.y.length > 0) {
    const pointCount = Array.isArray(plotData.y[0]) ? plotData.y[0].length : plotData.y.length;
    const traceType = pointCount > 5000 ? 'scattergl' : 'scatter';
    const traceMode = pointCount <= 300 ? 'lines+markers' : 'lines';
    const markerConfig = pointCount <= 300 ? { size: 4 } : undefined;

    if (Array.isArray(plotData.y[0])) {
      plotTraces = plotData.y.map((yArray: any[], i: number) => ({
        x: (plotData.x && Array.isArray(plotData.x[0])) ? plotData.x[i] : plotData.x,
        y: yArray,
        type: traceType,
        mode: traceMode,
        marker: markerConfig,
        line: { color: colors[i % colors.length], width: 2 },
        hoverinfo: 'x+y',
        name: plotData.labels?.[i] || `Trace ${i + 1}`
      }));
    } else {
      plotTraces = [{
        x: plotData.x,
        y: plotData.y,
        type: traceType,
        mode: traceMode,
        marker: markerConfig,
        line: { color: colors[0], width: 2 },
        hoverinfo: 'x+y',
        name: plotData.labels?.[0] || 'Trace 1'
      }];
    }
  }

  return (
    <div className="nodrag nopan nowheel" style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      <Plot
        data={plotTraces}
        layout={{
          width: Math.max(10, width - 12),
          height: Math.max(10, height - 12),
          margin: { l: 65, r: 15, t: 15, b: 55 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          uirevision: true,
          dragmode: dragMode,
          xaxis,
          yaxis,
          legend: { font: { color: textColor } }
        }}
        config={{
          displayModeBar: 'hover',
          displaylogo: false,
          responsive: true
        }}
        onRelayout={(e: any) => {
          if (e.dragmode) {
            setDragMode(e.dragmode);
          }
          if (onChange) {
            const newLayout = { ...(savedLayout || {}), ...e };
            
            if (e['xaxis.autorange']) {
              delete newLayout['xaxis.range[0]'];
              delete newLayout['xaxis.range[1]'];
              delete newLayout['xaxis.range'];
              newLayout['xaxis.autorange'] = true;
              setLimits(prev => ({ ...prev, x_min: undefined, x_max: undefined }));
            }
            if (e['xaxis.range[0]'] !== undefined) {
              delete newLayout['xaxis.autorange'];
            }
            if (Array.isArray(e['xaxis.range'])) {
              delete newLayout['xaxis.autorange'];
              newLayout['xaxis.range[0]'] = e['xaxis.range'][0];
              newLayout['xaxis.range[1]'] = e['xaxis.range'][1];
              delete newLayout['xaxis.range'];
            }

            if (e['yaxis.autorange']) {
              delete newLayout['yaxis.range[0]'];
              delete newLayout['yaxis.range[1]'];
              delete newLayout['yaxis.range'];
              newLayout['yaxis.autorange'] = true;
              setLimits(prev => ({ ...prev, y_min: undefined, y_max: undefined }));
            }
            if (e['yaxis.range[0]'] !== undefined) {
              delete newLayout['yaxis.autorange'];
            }
            if (Array.isArray(e['yaxis.range'])) {
              delete newLayout['yaxis.autorange'];
              newLayout['yaxis.range[0]'] = e['yaxis.range'][0];
              newLayout['yaxis.range[1]'] = e['yaxis.range'][1];
              delete newLayout['yaxis.range'];
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
