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

interface PolarPlotWidgetProps {
  blockId: string;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

export const PolarPlotWidget = ({ blockId, onChange, savedLayout }: PolarPlotWidgetProps) => {
  return (
    <ResizablePlotContainer
      minHeight="150px"
      background="var(--input-bg)"
      padding="6px"
      borderRadius="6px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => (
        <PlotlyPolarRenderer
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

interface PlotlyPolarRendererProps {
  blockId: string;
  width: number;
  height: number;
  onChange?: (name: string, value: any) => void;
  savedLayout?: any;
}

const PlotlyPolarRenderer = ({ blockId, width, height }: PlotlyPolarRendererProps) => {
  const { getNode } = useReactFlow();

  const [plotData, setPlotData] = useState<{
    r: any[];
    theta: any[];
    angle_unit?: string;
    plot_mode?: string;
    direction?: string;
    labels?: string[];
    r_label?: string;
    r_min?: number;
    r_max?: number;
  }>({ r: [], theta: [] });

  useEffect(() => {
    const updateChart = (eventResults?: any) => {
      const block = getNode(blockId);
      if (!block && !eventResults) return;

      const results = eventResults || block?.data?.results;
      const r = results?.r || block?.data?.R || [];
      const theta = results?.theta || block?.data?.Theta || [];

      setPlotData({
        r,
        theta,
        angle_unit: (results?.angle_unit || block?.data?.AngleUnit || 'degrees').toLowerCase(),
        plot_mode: (results?.plot_mode || block?.data?.PlotMode || 'lines').toLowerCase(),
        direction: (results?.direction || block?.data?.Direction || 'counterclockwise').toLowerCase(),
        labels: results?.labels || block?.data?.Labels,
        r_label: results?.r_label || block?.data?.RLabel || 'Radius',
        r_min: results?.r_min ?? block?.data?.RMin,
        r_max: results?.r_max ?? block?.data?.RMax
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
  const colors = ['#60a5fa', '#f87171', '#34d399', '#fbbf24', '#a78bfa', '#2dd4bf'];

  let traces: any[] = [];
  if (plotData.r && plotData.r.length > 0) {
    const isMultiSeries = Array.isArray(plotData.r[0]);
    const rList: any[][] = isMultiSeries ? plotData.r : [plotData.r];
    const thetaList: any[][] = (Array.isArray(plotData.theta[0])) ? plotData.theta : [plotData.theta];

    const mode = plotData.plot_mode?.includes('marker') && plotData.plot_mode?.includes('line')
      ? 'lines+markers'
      : (plotData.plot_mode?.includes('marker') ? 'markers' : 'lines');

    traces = rList.map((rArr, i) => {
      const thArr = thetaList[i] || thetaList[0] || [];
      const traceName = plotData.labels?.[i] || (rList.length > 1 ? `Trace ${i + 1}` : 'Polar');
      return {
        r: rArr,
        theta: thArr,
        thetaunit: plotData.angle_unit === 'radians' ? 'radians' : 'degrees',
        type: 'scatterpolar',
        mode,
        name: traceName,
        line: { color: colors[i % colors.length], width: 2 },
        marker: { size: 5, color: colors[i % colors.length] }
      };
    });
  }

  const layout: any = {
    width: width || 280,
    height: height || 250,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { l: 25, r: 25, t: 25, b: 25 },
    showlegend: traces.length > 1,
    legend: {
      x: 1,
      xanchor: 'right',
      y: 1,
      font: { size: 10, color: textColor },
      bgcolor: 'transparent'
    },
    polar: {
      radialaxis: {
        visible: true,
        tickfont: { size: 10, color: textColor },
        gridcolor: gridColor,
        exponentformat: 'SI',
        ...(plotData.r_min != null && plotData.r_max != null ? { range: [plotData.r_min, plotData.r_max] } : { autorange: true })
      },
      angularaxis: {
        direction: plotData.direction === 'clockwise' ? 'clockwise' : 'counterclockwise',
        rotation: 0,
        thetaunit: plotData.angle_unit === 'radians' ? 'radians' : 'degrees',
        tickfont: { size: 10, color: textColor },
        gridcolor: gridColor
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
          displaylogo: false,
          modeBarButtonsToRemove: ['lasso2d', 'select2d']
        }}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};
