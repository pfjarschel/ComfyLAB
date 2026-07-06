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

import { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { ResizablePlotContainer } from '../common/ResizablePlotContainer';
import { useReactFlow } from '@xyflow/react';

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
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
          <EChartsHeatmapRenderer
            nodeId={nodeId}
            xLabel={xLabel}
            yLabel={yLabel}
          />
        </div>
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
  const [debugInfo, setDebugInfo] = useState<string>('Waiting for data...');

  // Initialize and update ECharts
  useEffect(() => {
    if (!containerRef.current) return;

    if (!chartRef.current) {
      chartRef.current = echarts.init(containerRef.current, null, { renderer: 'canvas' });
    }

    const updateChart = (eventResults?: any) => {
      const node = getNode(nodeId);
      if (!node && !eventResults) return;
      const results = eventResults || (node?.data?.results as any);
      const zData = results?.z;
      const xLabels = results?.x;
      const yLabels = results?.y;
      const colormapName = results?.colormap || 'Viridis';
      
      const isLight = document.documentElement.classList.contains('light-theme');
      const textColor = isLight ? '#475569' : '#94a3b8';

      // Load requested colormap or fallback to Viridis
      let inRangeColors = [...(COLORMAPS[colormapName] || COLORMAPS.Viridis)];
      
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
          right: 35,
          top: 35,
          bottom: 45
        }
      };

      if (!zData) {
        setDebugInfo('zData is undefined/null');
        return;
      }
      if (!Array.isArray(zData)) {
        setDebugInfo('zData is not an array');
        return;
      }
      if (zData.length === 0) {
        setDebugInfo('zData is empty array');
        return;
      }
      if (!Array.isArray(zData[0])) {
        setDebugInfo('zData[0] is not an array (not 2D)');
        return;
      }

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

      if (minZ === Infinity || maxZ === -Infinity || minZ === maxZ) {
         if (minZ === maxZ && minZ !== Infinity) {
            maxZ = minZ + 1; // prevent identical min/max
         } else {
            minZ = 0; maxZ = 1;
         }
      }
      
      setDebugInfo(`Grid: ${numCols}x${numRows} | Min: ${minZ.toFixed(3)} | Max: ${maxZ.toFixed(3)}`);

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
        chartRef.current.setOption(option); // rely on ECharts native merge instead of notMerge: true
      }
    };

    // Initial update
    updateChart();

    // Listen to high-frequency telemetry events directly to bypass React render cycle
    const eventName = `telemetry-${nodeId}`;
    const handleTelemetry = (e: any) => {
      updateChart(e.detail?.results);
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
    <div className="nodrag" style={{ width: '100%', height: '100%', overflow: 'hidden', position: 'relative' }}>
      <div 
        style={{ 
          position: 'absolute', 
          top: 0, 
          left: 0, 
          fontSize: '10px', 
          color: '#ef4444', 
          background: 'rgba(0,0,0,0.5)', 
          padding: '2px 4px',
          zIndex: 10,
          pointerEvents: 'none'
        }}
      >
        {debugInfo}
      </div>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
