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

import { useEffect, useRef, useMemo } from 'react';
import * as echarts from 'echarts';
import { ResizablePlotContainer } from '../common/ResizablePlotContainer';

interface HeatmapPlotWidgetProps {
  z: any[] | undefined;
  x?: any[] | undefined;
  y?: any[] | undefined;
  xLabel?: string;
  yLabel?: string;
  plotType?: 'heatmap' | 'contour';
  colormap?: string;
}

export const HeatmapPlotWidget = ({
  z,
  x,
  y,
  xLabel = 'X',
  yLabel = 'Y',
  plotType = 'heatmap',
  colormap = 'Viridis',
}: HeatmapPlotWidgetProps) => {
  if (!z || !Array.isArray(z) || z.length === 0 || !Array.isArray(z[0])) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.75rem', background: 'var(--input-bg)', border: '1px solid var(--node-border)', marginTop: '6px', borderRadius: '6px', flex: 1, minHeight: '150px' }}>
        Waiting for 2D Z data...
      </div>
    );
  }

  // Pre-process inputs
  const { zVals, xVals, yVals } = useMemo(() => {
    const zVals = z.map((row: any) => (Array.isArray(row) ? row.map((v) => Number(v) || 0) : []));
    const xVals = Array.isArray(x) && x.length > 0 ? x.map((v) => Number(v) || 0) : undefined;
    const yVals = Array.isArray(y) && y.length > 0 ? y.map((v) => Number(v) || 0) : undefined;
    return { zVals, xVals, yVals };
  }, [z, x, y]);

  // ECharts requires data as [xIndex, yIndex, value]
  const { chartData, xCategories, yCategories, minZ, maxZ } = useMemo(() => {
    const data = [];
    let minZ = Infinity;
    let maxZ = -Infinity;

    const numRows = zVals.length;
    const numCols = zVals[0]?.length || 0;

    const xCat = xVals ? xVals.map(String) : Array.from({ length: numCols }, (_, i) => String(i));
    const yCat = yVals ? yVals.map(String) : Array.from({ length: numRows }, (_, i) => String(i));

    for (let i = 0; i < numRows; i++) {
      const row = zVals[i];
      for (let j = 0; j < numCols; j++) {
        const val = row[j] || 0;
        if (val < minZ) minZ = val;
        if (val > maxZ) maxZ = val;
        data.push([j, i, val]);
      }
    }
    
    if (minZ === Infinity) {
      minZ = 0;
      maxZ = 1;
    }

    return { chartData: data, xCategories: xCat, yCategories: yCat, minZ, maxZ };
  }, [zVals, xVals, yVals]);

  return (
    <ResizablePlotContainer 
      minHeight="150px" 
      background="var(--input-bg)" 
      padding="6px" 
      borderRadius="6px"
      border="1px solid var(--node-border)"
    >
      {(_width, _height) => (
        <EChartsHeatmapRenderer
          chartData={chartData}
          xCategories={xCategories}
          yCategories={yCategories}
          minZ={minZ}
          maxZ={maxZ}
          xLabel={xLabel}
          yLabel={yLabel}
          colormap={colormap}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface EChartsHeatmapRendererProps {
  chartData: any[];
  xCategories: string[];
  yCategories: string[];
  minZ: number;
  maxZ: number;
  xLabel: string;
  yLabel: string;
  colormap: string;
}

const EChartsHeatmapRenderer = ({
  chartData,
  xCategories,
  yCategories,
  minZ,
  maxZ,
  xLabel,
  yLabel,
  colormap,
}: EChartsHeatmapRendererProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    if (!chartRef.current) {
      chartRef.current = echarts.init(containerRef.current, null, { renderer: 'canvas' });
    }

    const isLight = document.documentElement.classList.contains('light-theme');
    const textColor = isLight ? '#475569' : '#94a3b8';
    const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';

    // Define colorscale colors based on colormap
    let inRangeColors = ['#440154', '#31688e', '#35b779', '#fde725']; // Default Viridis approximation
    if (colormap.toLowerCase() === 'wave') {
      inRangeColors = ['#3b82f6', '#f1f5f9', '#ef4444'];
    }

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        position: 'top',
        formatter: function (params: any) {
          return `${xLabel}: ${params.value[0]}<br/>${yLabel}: ${params.value[1]}<br/>Value: ${params.value[2]}`;
        }
      },
      toolbox: {
        feature: {
          dataZoom: { yAxisIndex: 'none' },
          restore: {},
          saveAsImage: {},
          dataView: { readOnly: true }
        },
        iconStyle: { borderColor: textColor }
      },
      grid: {
        left: 55,
        right: 75,
        top: 35,
        bottom: 45
      },
      xAxis: {
        type: 'category',
        data: xCategories,
        name: xLabel,
        nameLocation: 'middle',
        nameGap: 30,
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLabel: { color: textColor, fontSize: 8 },
        splitArea: { show: true, areaStyle: { color: ['rgba(255,255,255,0.02)', 'rgba(0,0,0,0.02)'] } },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'category',
        data: yCategories,
        name: yLabel,
        nameLocation: 'middle',
        nameGap: 40,
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLabel: { color: textColor, fontSize: 8 },
        splitArea: { show: true, areaStyle: { color: ['rgba(255,255,255,0.02)', 'rgba(0,0,0,0.02)'] } },
        splitLine: { show: false }
      },
      visualMap: {
        min: minZ,
        max: maxZ,
        calculable: true,
        realtime: false,
        inRange: { color: inRangeColors },
        textStyle: { color: textColor, fontSize: 9 },
        right: 0,
        top: 'center',
        itemHeight: 120,
        itemWidth: 12
      },
      series: [{
        name: 'Heatmap',
        type: 'heatmap',
        data: chartData,
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' }
        }
      }]
    };

    chartRef.current.setOption(option);
  }, [chartData, xCategories, yCategories, minZ, maxZ, xLabel, yLabel, colormap]);

  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;

    const observer = new ResizeObserver(() => {
      if (chartRef.current) {
        chartRef.current.resize();
      }
    });
    observer.observe(node);

    return () => {
      observer.disconnect();
      if (chartRef.current) {
        chartRef.current.dispose();
        chartRef.current = null;
      }
    };
  }, []);

  return (
    <div className="nodrag" style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};


