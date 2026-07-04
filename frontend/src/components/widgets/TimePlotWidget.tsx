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

interface TimePlotWidgetProps {
  nodeId: string;
  strokeColor?: string;
  dataKey?: string;
}

export const TimePlotWidget = ({ nodeId, strokeColor = '#34d399', dataKey = 'waveform' }: TimePlotWidgetProps) => {
  return (
    <ResizablePlotContainer 
      minHeight="120px"
      background="var(--input-bg)" 
      padding="6px" 
      borderRadius="6px"
      border="1px solid var(--node-border)"
    >
      {(_width, _height) => (
        <EChartsTimeRenderer
          nodeId={nodeId}
          strokeColor={strokeColor}
          dataKey={dataKey}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface EChartsTimeRendererProps {
  nodeId: string;
  strokeColor: string;
  dataKey: string;
}

const EChartsTimeRenderer = ({ nodeId, strokeColor, dataKey }: EChartsTimeRendererProps) => {
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
    const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';
    const textColor = isLight ? '#475569' : '#94a3b8';

    const baseOption = {
      backgroundColor: 'transparent',
      animation: false, // Critical for real-time performance
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
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
        left: 45,
        right: 15,
        top: 35,
        bottom: 25
      },
      xAxis: {
        type: 'category',
        name: 'Time Index',
        nameLocation: 'middle',
        nameGap: 15,
        nameTextStyle: { color: textColor, fontSize: 9 },
        axisLabel: { color: textColor, fontSize: 8 },
        splitLine: { show: true, lineStyle: { color: gridColor } }
      },
      yAxis: {
        type: 'value',
        name: 'Value',
        nameLocation: 'middle',
        nameGap: 30,
        nameTextStyle: { color: textColor, fontSize: 9 },
        axisLabel: { color: textColor, fontSize: 8 },
        splitLine: { lineStyle: { color: gridColor } }
      }
    };

    const updateChart = () => {
      const node = getNode(nodeId);
      if (!node) return;
      const points = (node.data?.results as any)?.[dataKey];
      
      if (!points || points.length === 0) return;

      const option: echarts.EChartsOption = {
        ...baseOption as any,
        dataset: {
          source: {
            y: points
          }
        },
        series: [
          {
            type: 'line',
            encode: { y: 'y' },
            showSymbol: false,
            large: true,
            largeThreshold: 100,
            lineStyle: { color: strokeColor, width: 1.5 }
          }
        ]
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
  }, [nodeId, strokeColor, dataKey, getNode]);

  // Imperative resize observer and cleanup
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
    <div 
      className="nodrag" 
      style={{ width: '100%', height: '100%', overflow: 'hidden' }}
    >
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
