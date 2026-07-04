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

interface XYPlotWidgetProps {
  x: any[] | undefined;
  y: any[] | undefined;
  xLabel?: string;
  yLabel?: string;
}

export const XYPlotWidget = ({ x, y, xLabel = 'X', yLabel = 'Y' }: XYPlotWidgetProps) => {
  if (!x || !y || !Array.isArray(x) || !Array.isArray(y) || x.length === 0 || y.length === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.75rem', background: 'var(--input-bg)', border: '1px solid var(--node-border)', marginTop: '6px', borderRadius: '6px', flex: 1, minHeight: '150px' }}>
        Waiting for X/Y data...
      </div>
    );
  }

  return (
    <ResizablePlotContainer 
      minHeight="150px" 
      background="var(--input-bg)" 
      padding="6px" 
      borderRadius="6px"
      border="1px solid var(--node-border)"
    >
      {(_width, _height) => (
        <EChartsXYRenderer
          xVals={x}
          yVals={y}
          xLabel={xLabel}
          yLabel={yLabel}
        />
      )}
    </ResizablePlotContainer>
  );
};

interface EChartsXYRendererProps {
  xVals: any[];
  yVals: any[];
  xLabel: string;
  yLabel: string;
}

const EChartsXYRenderer = ({ xVals, yVals, xLabel, yLabel }: EChartsXYRendererProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  // Initialize and update ECharts
  useEffect(() => {
    if (!containerRef.current) return;

    if (!chartRef.current) {
      chartRef.current = echarts.init(containerRef.current, null, { renderer: 'canvas' });
    }

    const isLight = document.documentElement.classList.contains('light-theme');
    const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';
    const textColor = isLight ? '#475569' : '#94a3b8';

    const option: echarts.EChartsOption = {
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
        bottom: 35
      },
      xAxis: {
        type: 'value',
        name: xLabel,
        nameLocation: 'middle',
        nameGap: 22,
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLabel: { color: textColor, fontSize: 8 },
        splitLine: { lineStyle: { color: gridColor } }
      },
      yAxis: {
        type: 'value',
        name: yLabel,
        nameLocation: 'middle',
        nameGap: 30,
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLabel: { color: textColor, fontSize: 8 },
        splitLine: { lineStyle: { color: gridColor } }
      },
      dataset: {
        source: {
          x: xVals,
          y: yVals
        }
      },
      series: [
        {
          type: 'line',
          encode: { x: 'x', y: 'y' },
          showSymbol: false,
          large: true,
          largeThreshold: 100,
          lineStyle: { color: '#10b981', width: 1.5 }
        }
      ]
    };

    chartRef.current.setOption(option, true); // true = notMerge
  }, [xVals, yVals, xLabel, yLabel]);

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
