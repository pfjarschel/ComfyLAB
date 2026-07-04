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

import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { ResizablePlotContainer } from '../common/ResizablePlotContainer';
import { useReactFlow } from '@xyflow/react';

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
      {(_width, _height) => (
        <EChartsHeatmapRenderer
          nodeId={nodeId}
          xLabel={xLabel}
          yLabel={yLabel}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface EChartsHeatmapRendererProps {
  nodeId: string;
  xLabel: string;
  yLabel: string;
}

const EChartsHeatmapRenderer = ({ nodeId, xLabel, yLabel }: EChartsHeatmapRendererProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  const { getNode } = useReactFlow();

  // Initialize and update ECharts
  useEffect(() => {
    if (!containerRef.current) return;

    if (!chartRef.current) {
      chartRef.current = echarts.init(containerRef.current, null, { renderer: 'canvas' });
    }

    const isLight = document.documentElement.classList.contains('light-theme');
    const textColor = isLight ? '#475569' : '#94a3b8';

    // A modern dark-mode compatible viridis-like heatmap colormap
    const inRangeColors = [
      '#440154', '#482878', '#3e4989', '#31688e', 
      '#26828e', '#1f9e89', '#35b779', '#6ece58', 
      '#b5de2b', '#fde725'
    ];
    
    if (isLight) {
      inRangeColors.reverse();
    }

    const baseOption = {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        position: 'top',
        formatter: (params: any) => {
          return `${xLabel}: ${params.name}<br/>${yLabel}: ${params.value[1]}<br/>Value: ${params.value[2].toFixed(3)}`;
        }
      },
      toolbox: {
        feature: {
          dataZoom: { yAxisIndex: 'none' },
          restore: {},
          saveAsImage: {}
        },
        iconStyle: { borderColor: textColor }
      },
      grid: {
        left: 55,
        right: 65, // Room for visualMap
        top: 35,
        bottom: 45
      }
    };

    const updateChart = () => {
      const node = getNode(nodeId);
      if (!node) return;
      const results = node.data?.results as any;
      const zData = results?.z;
      const xLabels = results?.x;
      const yLabels = results?.y;
      
      if (!zData || !Array.isArray(zData) || zData.length === 0 || !Array.isArray(zData[0])) return;

      const numRows = zData.length;
      const numCols = zData[0].length;

      const xCategories = xLabels && xLabels.length === numCols 
        ? xLabels.map(String) 
        : Array.from({ length: numCols }, (_, i) => String(i));
        
      const yCategories = yLabels && yLabels.length === numRows 
        ? yLabels.map(String) 
        : Array.from({ length: numRows }, (_, i) => String(i));

      let minZ = Infinity;
      let maxZ = -Infinity;
      
      // We must pre-process zData into [xIndex, yIndex, value] format for ECharts Heatmap series
      const chartData = new Array(numRows * numCols);
      let idx = 0;
      
      for (let y = 0; y < numRows; y++) {
        for (let x = 0; x < numCols; x++) {
          const val = Number(zData[y][x]) || 0;
          chartData[idx++] = [x, y, val];
          if (val < minZ) minZ = val;
          if (val > maxZ) maxZ = val;
        }
      }

      if (minZ === Infinity || maxZ === -Infinity) {
        minZ = 0; maxZ = 1;
      }

      const option: echarts.EChartsOption = {
        ...baseOption as any,
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

      if (chartRef.current) {
        chartRef.current.setOption(option, true); // true = notMerge
      }
    };

    // Initial update
    updateChart();

    // Listen to high-frequency telemetry events directly to bypass React render cycle
    const eventName = `telemetry-${nodeId}`;
    const handleTelemetry = () => {
      updateChart();
    };
    
    window.addEventListener(eventName, handleTelemetry);
    
    return () => {
      window.removeEventListener(eventName, handleTelemetry);
    };
  }, [nodeId, xLabel, yLabel, getNode]);

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
