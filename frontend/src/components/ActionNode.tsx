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

import { useState, useEffect, useContext, useRef } from 'react';
import { Handle, Position, NodeResizer, useEdges, useUpdateNodeInternals, useReactFlow } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import { RegistryContext } from '../context/RegistryContext';
import { getPinColor } from '../constants/nodeLayouts';
import type { NodeSchema } from '../constants/nodeLayouts';
import { NumericTextInput } from './common/NumericTextInput';
import { TimePlotWidget } from './widgets/TimePlotWidget';
import { XYPlotWidget } from './widgets/XYPlotWidget';
import { HeatmapPlotWidget } from './widgets/HeatmapPlotWidget';
import { DisplayScreenWidget } from './widgets/DisplayScreenWidget';
import { RFGeneratorWidget } from './widgets/RFGeneratorWidget';

// Re-export pin color resolver for compatibility with App.tsx and NodeInspectorPanel.tsx
export { getPinColor };

export type ActionNodeData = {
  action: string;
  status?: 'idle' | 'running' | 'success' | 'error' | 'stopped';
  resultMessage?: string;
  result?: any;
  results?: Record<string, any>;
  history?: number[];
  waveform?: number[];
  

  onChange?: (id: string, key: string, value: any) => void;
  // Node properties
  value?: any;
  val1?: number;
  val2?: number;
  operator?: string;
  on?: boolean;
  power?: number;
  wavelength?: number;
  wave_type?: string;
  frequency?: number;
  amplitude?: number;
  noise?: number;
  count?: number;
};

const DISPLAY_AND_PLOT_NODES = [
  'outputs/basic/display',
  'control_flow/timing/measure_time',
  'arrays/manipulation/accumulate',
  'hardware/virtual_oscilloscope',
  'outputs/plots/plot',
  'outputs/plots/xy_plot'
];

const PLOT_NODES = [
  'hardware/virtual_oscilloscope',
  'outputs/plots/plot',
  'outputs/plots/xy_plot',
  'outputs/plots/heatmap_plot'
];

const NODES_WITH_CUSTOM_UI = [
  'constants/number',
  'constants/boolean',
  'constants/string',
  'hardware/virtual_generator',
  'math/arithmetic/calculator',
  ...DISPLAY_AND_PLOT_NODES
];

export const ActionNode = ({ id, data, selected }: NodeProps<any>) => {
  const nodeRegistry = useContext(RegistryContext);
  const registryLayout = nodeRegistry?.[data.action] as NodeSchema | undefined;
  const updateNodeInternals = useUpdateNodeInternals();
  const { setNodes, getNode } = useReactFlow();
  const edges = useEdges();

  const statusBarRef = useRef<HTMLDivElement>(null);
  const optionalToggleRef = useRef<HTMLDivElement>(null);

  const [measuredStatusHeight, setMeasuredStatusHeight] = useState(44);
  const [measuredOptionalHeight, setMeasuredOptionalHeight] = useState(0);

  const isScriptNode = data.action && data.action.startsWith('script/');
  const isMacro = data.action && (data.action.startsWith('user/macro/') || data.action.startsWith('workspace/macro/'));
  const isLibraryCallNode = !!data.action && ['ffi/call', 'library/call', 'dll/so/call'].includes(data.action.toLowerCase().replace(/\\/g, ''));

  // Helper: map a C type string to a frontend pin colour type
  const libraryCTypeToPin = (cType: string): string => {
    if (cType === 'bool') return 'boolean';
    if (cType === 'c_char_p') return 'text';
    return 'number'; // all integer and float types
  };

  let layout: NodeSchema | undefined = !registryLayout ? undefined : (isScriptNode || (data.customInputs?.length || data.customOutputs?.length))
    ? {
        ...registryLayout,
        dataIns: (data.customInputs || []).map((inp: any) => ({
          name: inp.name,
          label: inp.name,
          defaultVal: inp.default,
          type: inp.type || 'any',
          widget: inp.widget || (inp.type === 'boolean' ? 'checkbox' : inp.type === 'number' ? 'number' : inp.type === 'text' ? 'text' : 'any'),
          min: inp.min,
          max: inp.max,
          step: inp.step,
          options: inp.options,
          optional: inp.optional || false,
        })),
        dataOuts: (data.customOutputs || []).map((out: any) => ({
          name: out.name,
          label: out.name,
          type: out.type || 'any',
        })),
      }
    : registryLayout;

  if (layout && data.action === 'math/arithmetic/calculator') {
    const variables: string[] = Array.isArray(data.variables)
      ? data.variables
      : typeof data.variables === 'string'
        ? data.variables.split(',').map((v: string) => v.trim()).filter(Boolean)
        : ['a', 'b'];
    layout = {
      ...layout,
      dataIns: variables.map((v: string) => ({
        name: v,
        label: v,
        type: 'number',
        widget: 'number',
      })),
    };
  }

  // Library Call: augment static layout with dynamic pins from library_args
  if (layout && isLibraryCallNode) {
    const libraryArgs: any[] = data.library_args || data.ffi_args || [];
    const dynIns: typeof layout.dataIns = [];
    const dynOuts: typeof layout.dataOuts = [];
    libraryArgs.forEach((arg: any) => {
      const name = (arg.name || '').trim();
      if (!name) return;
      const pinType = libraryCTypeToPin(arg.c_type || '');
      if (arg.direction === 'in') {
        dynIns.push({ name, label: name, type: pinType });
      } else if (arg.direction === 'out') {
        // blank size_arg → scalar; filled → array
        const outType = arg.size_arg ? 'list' : pinType;
        dynOuts.push({ name, label: name, type: outType });
      } else if (arg.direction === 'inout') {
        dynIns.push({ name, label: name, type: 'list' });
        dynOuts.push({ name, label: name, type: 'list' });
      }
    });
    layout = {
      ...layout,
      dataIns: [...layout.dataIns, ...dynIns],
      dataOuts: [...layout.dataOuts, ...dynOuts],
    };
  }

  if (layout && data.action === 'math/signal_processing/filter') {
    const filterType = data.FilterType ?? 'Moving Average';
    layout = {
      ...layout,
      dataIns: layout.dataIns.filter((pin: any) => {
        if (pin.name === 'Signal' || pin.name === 'FilterType') return true;
        if (filterType === 'Moving Average') {
          return pin.name === 'Window';
        } else if (filterType === 'Low-pass' || filterType === 'High-pass') {
          return pin.name === 'Cutoff' || pin.name === 'Order';
        } else if (filterType === 'Band-pass') {
          return pin.name === 'LowCutoff' || pin.name === 'HighCutoff' || pin.name === 'Order';
        }
        return true;
      }),
    };
  }

  if (layout && data.action === 'macro/boundary/input') {
    const isExec = data.Type === 'exec';
    layout = {
      ...layout,
      execOuts: isExec ? ['Out'] : [],
      dataOuts: isExec ? [] : layout.dataOuts,
    };
  } else if (layout && data.action === 'macro/boundary/output') {
    const isExec = data.Type === 'exec';
    layout = {
      ...layout,
      execIns: isExec ? ['In'] : [],
      dataIns: layout.dataIns.filter(pin => isExec ? pin.name !== 'Value' : true),
    };
  }

  const isMissing = !!(nodeRegistry && !registryLayout);
  const connectedEdges = edges.filter(e => e.source === id || e.target === id);
  const connectedEdgesHash = isMissing
    ? JSON.stringify(connectedEdges.map(e => ({ id: e.id, sourceHandle: e.sourceHandle, targetHandle: e.targetHandle })))
    : '';

  const pinsHash = !layout ? '' : JSON.stringify({
    dataIns: layout.dataIns.map(p => p.name),
    dataOuts: layout.dataOuts.map(p => p.name),
    execIns: layout.execIns,
    execOuts: layout.execOuts
  });

  useEffect(() => {
    updateNodeInternals(id);
  }, [id, pinsHash, connectedEdgesHash, updateNodeInternals]);

  const [isEditingName, setIsEditingName] = useState(false);
  const [tempName, setTempName] = useState(data.customName || layout?.name || '');
  const [showOptional, setShowOptional] = useState(false);
  const [newVarVal, setNewVarVal] = useState('');

  useEffect(() => {
    setTempName(data.customName || layout?.name || '');
  }, [data.customName, layout?.name]);

  const isExecPassthrough = !!layout?.isPassthrough && !!layout.execIns?.includes('In');
  const isAnyPassthrough = !!layout?.isPassthrough;

  const isPinConnected = (pinName: string) => {
    return edges.some(edge => edge.target === id && edge.targetHandle === pinName);
  };

  const getConnectedPinValue = (pinName: string) => {
    const edge = edges.find(e => e.target === id && e.targetHandle === pinName);
    if (!edge) return undefined;
    const sourceNode = getNode(edge.source);
    const pinValues = sourceNode?.data?.pinValues as Record<string, any> | undefined;
    return pinValues?.[edge.sourceHandle || ''];
  };

  const visibleDataIns = layout
    ? layout.dataIns.filter(
        (pin: any) => !pin.optional || showOptional || isPinConnected(pin.name)
      )
    : [];

  const hasOptionalInputs = layout ? layout.dataIns.some((pin: any) => pin.optional) : false;

  const handleChange = (name: string, val: any) => {
    if (data.onChange) {
      data.onChange(id, name, val);
    }
  };

  // Calculates spatial offsets to stack left-aligned handles dynamically without overlap
  const getLeftHandleTop = (isExec: boolean, index: number) => {
    if (isExec) {
      return `${25 + index * 20}px`;
    } else {
      const execCount = layout?.execIns?.length || 0;
      return `${32 + execCount * 22 + index * 32}px`;
    }
  };

  // Calculates spatial offsets to stack right-aligned handles dynamically without overlap
  const getRightHandleTop = (isExec: boolean, index: number) => {
    if (isExec) {
      return `${25 + index * 20}px`;
    } else {
      const execCount = layout?.execOuts?.length || 0;
      return `${32 + execCount * 22 + index * 32}px`;
    }
  };

  const calculateMinHeight = () => {
    // 1. Base padding & header height (52px) + status bar which is always rendered
    let height = 52 + measuredStatusHeight;

    if (!layout) {
      if (isMissing) {
        const targetHandles = Array.from(new Set(edges.filter(e => e.target === id).map(e => e.targetHandle).filter(Boolean))) as string[];
        const sourceHandles = Array.from(new Set(edges.filter(e => e.source === id).map(e => e.sourceHandle).filter(Boolean))) as string[];
        const execIns = targetHandles.filter(h => h === 'In' || connectedEdges.some(e => e.target === id && e.targetHandle === h && e.style?.stroke === '#a78bfa'));
        const dataIns = targetHandles.filter(h => !execIns.includes(h));
        const execOuts = sourceHandles.filter(h => h === 'Out' || h === 'Then' || h === 'Else' || connectedEdges.some(e => e.source === id && e.sourceHandle === h && e.style?.stroke === '#a78bfa'));
        const dataOuts = sourceHandles.filter(h => !execOuts.includes(h));

        const maxLeft = execIns.length * 20 + dataIns.length * 32 + 32;
        const maxRight = execOuts.length * 20 + dataOuts.length * 32 + 32;
        const bodyHeight = Math.max(maxLeft, maxRight, 60);
        return Math.max(120, height + bodyHeight);
      }
      return height;
    }

    // 2. Exec handles constraint
    const maxExecInsHeight = layout.execIns.length > 0 ? 25 + layout.execIns.length * 20 + 10 : 0;
    const maxExecOutsHeight = layout.execOuts.length > 0 ? 25 + layout.execOuts.length * 20 + 10 : 0;
    const execMinHeight = Math.max(maxExecInsHeight, maxExecOutsHeight);

    // 3. Body items height
    let bodyHeight = 0;

    // Macro/Script/Library buttons
    if (isMacro || isScriptNode || isLibraryCallNode || (!isScriptNode && !isMacro && registryLayout?.original_code)) {
      bodyHeight += 44;
    }

    // Node-specific widgets
    if (data.action === 'constants/number' || data.action === 'constants/string') {
      bodyHeight += 58;
    } else if (data.action === 'constants/boolean') {
      bodyHeight += 38;
    } else if (data.action === 'hardware/virtual_generator') {
      bodyHeight += 138;
    } else if (DISPLAY_AND_PLOT_NODES.includes(data.action) && !PLOT_NODES.includes(data.action)) {
      bodyHeight += 96;
    } else if (PLOT_NODES.includes(data.action)) {
      bodyHeight += 152;
    }

    // Dynamic inputs (checks both showOptional and connected optional pins)
    if (!NODES_WITH_CUSTOM_UI.includes(data.action)) {
      const visiblePins = (layout.dataIns || []).filter((pin: any) => !pin.optional || showOptional || edges.some(e => e.target === id && e.targetHandle === pin.name));
      visiblePins.forEach((pin: any) => {
        const isConnected = edges.some(e => e.target === id && e.targetHandle === pin.name);
        if (isConnected) {
          bodyHeight += 32;
        } else {
          if (pin.widget === 'checkbox' || pin.type === 'boolean') {
            bodyHeight += 38;
          } else if (pin.widget === 'slider') {
            bodyHeight += 58;
          } else if (pin.widget === 'dropdown') {
            bodyHeight += 58;
          } else {
            bodyHeight += 40; // text/number input + gap
          }
        }
      });
    }

    // Visual Override connection label rows (checks both showOptional and connected optional pins)
    if (DISPLAY_AND_PLOT_NODES.includes(data.action)) {
      const visiblePins = (layout.dataIns || []).filter((pin: any) => !pin.optional || showOptional || edges.some(e => e.target === id && e.targetHandle === pin.name));
      bodyHeight += visiblePins.length * 32;
    }

    // Data outputs
    if (layout.dataOuts && layout.dataOuts.length > 0) {
      bodyHeight += layout.dataOuts.length * 32;
    }

    // Optional settings toggle button
    if (hasOptionalInputs) {
      bodyHeight += measuredOptionalHeight;
    }

    return Math.max(execMinHeight, height + bodyHeight);
  };

  const isXYPlot = data.action === 'outputs/plots/xy_plot';
  const calculatedMinHeight = calculateMinHeight();

  // Measure status bar height dynamically to handle multi-line error/status wrapping
  useEffect(() => {
    if (!statusBarRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const newHeight = entry.contentRect.height + 10;
        setMeasuredStatusHeight((prev) => (Math.abs(prev - newHeight) > 0.5 ? newHeight : prev));
      }
    });
    observer.observe(statusBarRef.current);
    return () => observer.disconnect();
  }, []);

  // Measure optional settings toggle button height dynamically when present
  useEffect(() => {
    if (!optionalToggleRef.current) {
      setMeasuredOptionalHeight(32);
      return;
    }
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const newHeight = entry.contentRect.height + 8;
        setMeasuredOptionalHeight((prev) => (Math.abs(prev - newHeight) > 0.5 ? newHeight : prev));
      }
    });
    observer.observe(optionalToggleRef.current);
    return () => observer.disconnect();
  }, [hasOptionalInputs, showOptional]);

  // Sync calculated minimum height back to the React Flow node's parent container style minHeight
  useEffect(() => {
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === id) {
          const currentMinHeight = `${calculatedMinHeight}px`;
          if (n.style?.minHeight !== currentMinHeight) {
            return {
              ...n,
              style: {
                ...n.style,
                minHeight: currentMinHeight,
              },
            };
          }
        }
        return n;
      })
    );
  }, [id, calculatedMinHeight, setNodes]);

  // Re-measure node layout internals whenever minimum height constraint changes
  useEffect(() => {
    updateNodeInternals(id);
  }, [id, calculatedMinHeight, updateNodeInternals]);

  // High-frequency telemetry listener for DOM bypass
  useEffect(() => {
    const handleTelemetry = (e: any) => {
      const { status, resultMessage } = e.detail;
      if (status) {
        const containerEl = document.getElementById(`node-container-${id}`);
        if (containerEl) {
          containerEl.classList.remove('idle', 'running', 'success', 'error', 'stopped');
          containerEl.classList.add(status);
        }
        const statusEl = document.getElementById(`node-status-${id}`);
        if (statusEl) {
          statusEl.classList.remove('idle', 'running', 'success', 'error', 'stopped');
          statusEl.classList.add(status);
        }
      }
      if (resultMessage !== undefined || status) {
        const msgEl = document.getElementById(`node-msg-${id}`);
        if (msgEl) {
          msgEl.innerText = status === 'running' ? '⏳ Running...' : status === 'stopped' ? '⏹️ Stopped' : (resultMessage || msgEl.innerText || 'Idle');
        }
      }

      const ledEl = document.getElementById(`led-${id}`);
      if (ledEl) {
        const node = getNode(id);
        const isStateTrue = !!(node?.data?.results as any)?.state;
        ledEl.style.background = isStateTrue ? '#10b981' : '#ef4444';
        ledEl.style.boxShadow = isStateTrue 
          ? '0 0 14px #10b981cc, 0 0 4px #10b98155, inset 0 0 8px rgba(0,0,0,0.5)' 
          : '0 0 14px #ef4444aa, 0 0 4px #ef444455, inset 0 0 8px rgba(0,0,0,0.5)';
      }
      
      // We DO NOT trigger a React re-render of this node here.
      // This is a CRITICAL memory optimization. Re-rendering a 1500-line node component
      // at 10Hz with massive arrays attached to it causes massive VDOM thrashing
      // and React Fiber memory leaks (since Fiber holds old prop closures).
      // The Plot Widgets (XY, Time, Heatmap) now listen to this event directly
      // and pull data from nodesRef (via getNode).
    };
    const eventName = `telemetry-${id}`;
    window.addEventListener(eventName, handleTelemetry);
    return () => window.removeEventListener(eventName, handleTelemetry);
  }, [id]);

  if (isMissing) {
    const targetHandles = Array.from(new Set(edges.filter(e => e.target === id).map(e => e.targetHandle).filter(Boolean))) as string[];
    const sourceHandles = Array.from(new Set(edges.filter(e => e.source === id).map(e => e.sourceHandle).filter(Boolean))) as string[];

    const execIns = targetHandles.filter(h => h === 'In' || connectedEdges.some(e => e.target === id && e.targetHandle === h && e.style?.stroke === '#a78bfa'));
    const dataIns = targetHandles.filter(h => !execIns.includes(h));

    const execOuts = sourceHandles.filter(h => h === 'Out' || h === 'Then' || h === 'Else' || connectedEdges.some(e => e.source === id && e.sourceHandle === h && e.style?.stroke === '#a78bfa'));
    const dataOuts = sourceHandles.filter(h => !execOuts.includes(h));

    const getLeftHandleTopMissing = (isExec: boolean, index: number) => {
      if (isExec) {
        return `${25 + index * 20}px`;
      } else {
        const execCount = execIns.length;
        return `${32 + execCount * 22 + index * 32}px`;
      }
    };

    const getRightHandleTopMissing = (isExec: boolean, index: number) => {
      if (isExec) {
        return `${25 + index * 20}px`;
      } else {
        const execCount = execOuts.length;
        return `${32 + execCount * 22 + index * 32}px`;
      }
    };

    return (
      <div
        className={`glass-panel action-node missing-node ${selected ? 'selected' : ''}`}
        style={{
          minHeight: `${calculatedMinHeight}px`,
        }}
      >
        <span 
          className={`node-pin-icon ${data.pinned ? 'pinned' : ''}`}
          onClick={(e) => { 
            e.stopPropagation(); 
            handleChange('pinned', !data.pinned); 
          }}
          title={data.pinned ? "Unlock node" : "Pin node in place"}
        >
          📌
        </span>

        <NodeResizer 
          minWidth={170} 
          minHeight={calculatedMinHeight} 
          isVisible={selected && !data.pinned} 
          lineStyle={{ border: '1px dashed #ef4444' }}
          handleStyle={{ width: 8, height: 8, background: '#ef4444', borderRadius: '50%' }}
          onResizeStart={data.onResizeStart}
          onResizeEnd={data.onResizeEnd}
        />

        {/* --- EXECUTION HANDLES (Purple Diamond Style) --- */}
        {execIns.map((pinName, i) => (
          <Handle
            key={`exec-in-${pinName}`}
            type="target"
            position={Position.Left}
            id={pinName}
            style={{
              top: getLeftHandleTopMissing(true, i),
              background: '#a78bfa',
              borderColor: '#ffffff',
              borderRadius: '2px',
              width: '8px',
              height: '8px'
            }}
            title={`Exec Input: ${pinName}`}
          />
        ))}
        {execOuts.map((pinName, i) => (
          <Handle
            key={`exec-out-${pinName}`}
            type="source"
            position={Position.Right}
            id={pinName}
            style={{
              top: getRightHandleTopMissing(true, i),
              background: '#a78bfa',
              borderColor: '#ffffff',
              borderRadius: '2px',
              width: '8px',
              height: '8px'
            }}
            title={`Exec Output: ${pinName}`}
          />
        ))}

        {/* --- HEADER --- */}
        <div className="action-node-header">
          <div className="node-icon">⚠️</div>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '120px', fontWeight: 'bold' }}>
            {data.customName || 'Missing Node'}
          </span>
        </div>

        {/* --- BODY --- */}
        <div className="action-node-body" style={{ color: '#fca5a5', fontSize: '0.8rem', gap: '6px' }}>
          <div style={{ wordBreak: 'break-all', fontWeight: '500', opacity: 0.9 }}>
            Type: {data.action}
          </div>
          <div style={{ fontSize: '0.75rem', opacity: 0.8, fontStyle: 'italic', marginTop: '4px', lineHeight: 1.3 }}>
            Warning: This node type is not found in the registry.
          </div>

          {/* Render target data handles */}
          {dataIns.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '10px' }}>
              {dataIns.map((pinName) => {
                const edge = connectedEdges.find(e => e.target === id && e.targetHandle === pinName);
                const pinColor = edge?.style?.stroke || '#64748b';
                return (
                  <div key={`data-in-${pinName}`} style={{ fontSize: '0.7rem', color: 'var(--text-color)', textAlign: 'left', position: 'relative', width: '100%', paddingLeft: '8px' }}>
                    <Handle
                      type="target"
                      position={Position.Left}
                      id={pinName}
                      style={{
                        position: 'absolute',
                        left: '-18px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        background: pinColor,
                        borderColor: '#ffffff',
                        width: '8px',
                        height: '8px'
                      }}
                      title={`Data Input: ${pinName}`}
                    />
                    ↳ {pinName}
                  </div>
                );
              })}
            </div>
          )}

          {/* Render source data handles */}
          {dataOuts.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '10px' }}>
              {dataOuts.map((pinName) => {
                const edge = connectedEdges.find(e => e.source === id && e.sourceHandle === pinName);
                const pinColor = edge?.style?.stroke || '#64748b';
                return (
                  <div key={`data-out-${pinName}`} style={{ fontSize: '0.7rem', color: 'var(--text-color)', textAlign: 'right', position: 'relative', width: '100%', paddingRight: '8px' }}>
                    <Handle
                      type="source"
                      position={Position.Right}
                      id={pinName}
                      style={{
                        position: 'absolute',
                        right: '-18px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        background: pinColor,
                        borderColor: '#ffffff',
                        width: '8px',
                        height: '8px'
                      }}
                      title={`Data Output: ${pinName}`}
                    />
                    {pinName} ↲
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (!registryLayout || !layout) return null;

  const isLED = data.action === 'outputs/basic/led_indicator';
  if (isLED) {
    const isStateTrue = !!data.results?.state;
    // Glowing color palette matching standard light/dark modes
    const ledColor = isStateTrue ? '#10b981' : '#ef4444';
    const ledGlow = isStateTrue ? '0 0 14px #10b981cc, 0 0 4px #10b98155' : '0 0 14px #ef4444aa, 0 0 4px #ef444455';
    const statePinColor = getPinColor('boolean');

    return (
      <div
        id={`led-${id}`}
        className={`led-indicator-node ${selected ? 'selected' : ''}`}
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: ledColor,
          border: `3px solid ${selected ? '#3b82f6' : 'var(--node-border)'}`,
          boxShadow: `${ledGlow}, inset 0 0 8px rgba(0,0,0,0.5)`,
          position: 'relative',
          cursor: 'move',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'background-color 0.25s ease, box-shadow 0.25s ease',
        }}
        title={`LED Status Indicator: ${isStateTrue ? 'ON' : 'OFF'}`}
      >
        {/* Inner lens glare */}
        <div style={{
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.3)',
          filter: 'blur(1px)',
          position: 'absolute',
          top: '6px',
          left: '6px',
          pointerEvents: 'none'
        }} />

        {/* Exec Input (top-left) */}
        <Handle
          type="target"
          position={Position.Left}
          id="In"
          style={{
            top: '12px',
            left: '-4.5px',
            background: '#a78bfa',
            borderColor: '#ffffff',
            borderRadius: '2px',
            width: '6px',
            height: '6px',
            minWidth: 0,
            minHeight: 0,
            borderWidth: '1px',
          }}
          title="Exec Input: In"
        />

        {/* State Data Input (bottom-left) */}
        <Handle
          type="target"
          position={Position.Left}
          id="State"
          style={{
            top: '28px',
            left: '-4.5px',
            background: statePinColor,
            borderColor: '#ffffff',
            borderRadius: '50%',
            width: '6px',
            height: '6px',
            minWidth: 0,
            minHeight: 0,
            borderWidth: '1px',
          }}
          title={`Data Input: State\nValue: ${getConnectedPinValue('State')}`}
        />

        {/* Exec Output (middle-right) */}
        <Handle
          type="source"
          position={Position.Right}
          id="Out"
          style={{
            top: '20px',
            right: '-4.5px',
            background: '#a78bfa',
            borderColor: '#ffffff',
            borderRadius: '2px',
            width: '6px',
            height: '6px',
            minWidth: 0,
            minHeight: 0,
            borderWidth: '1px',
          }}
          title="Exec Output: Out"
        />
      </div>
    );
  }

  if (isAnyPassthrough) {
    const isExec = isExecPassthrough;
    let pinColor = '#a78bfa'; // purple for exec
    if (!isExec) {
      const incomingEdge = edges.find(e => e.target === id && e.targetHandle === 'In');
      if (incomingEdge) {
        pinColor = incomingEdge.style?.stroke || '#64748b';
      } else {
        pinColor = '#64748b';
      }
    }

    return (
      <div
        className={`passthrough-node ${isExec ? 'exec' : 'data'} ${selected ? 'selected' : ''}`}
        style={{
          width: '14px',
          height: '14px',
          borderRadius: '50%',
          background: 'var(--controls-bg)',
          border: `2.5px solid ${selected ? '#3b82f6' : pinColor}`,
          position: 'relative',
          boxShadow: selected ? '0 0 10px #3b82f6a0' : `0 0 8px ${pinColor}30`,
          cursor: 'move',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Handle
          type="target"
          position={Position.Left}
          id="In"
          style={{
            top: '50%',
            left: '-2.5px',
            transform: 'translateY(-50%)',
            background: pinColor,
            borderColor: '#ffffff',
            borderRadius: isExec ? '2px' : '50%',
            width: '5px',
            height: '5px',
            minWidth: 0,
            minHeight: 0,
            borderWidth: '1px',
          }}
          title={isExec ? 'Exec Input: In' : `Data Input: In${getConnectedPinValue('In') !== undefined ? `\nValue: ${getConnectedPinValue('In')}` : ''}`}
        />
        <Handle
          type="source"
          position={Position.Right}
          id="Out"
          style={{
            top: '50%',
            right: '-2.5px',
            transform: 'translateY(-50%)',
            background: pinColor,
            borderColor: '#ffffff',
            borderRadius: isExec ? '2px' : '50%',
            width: '5px',
            height: '5px',
            minWidth: 0,
            minHeight: 0,
            borderWidth: '1px',
          }}
          title={isExec ? 'Exec Output: Out' : `Data Output: Out${data.pinValues?.['Out'] !== undefined ? `\nValue: ${data.pinValues?.['Out']}` : ''}`}
        />
      </div>
    );
  }

  return (
    <div
      id={`node-container-${id}`}
      className={`glass-panel action-node ${data.status || 'idle'} ${isMacro ? 'macro-node' : ''} ${data.pinned ? 'pinned-node' : ''} ${data.isPersistent ? 'persistent-node' : ''} ${selected ? 'selected' : ''}`}
      onDoubleClick={(e) => {
        // Do not open inspector when double-clicking interactive elements
        const target = e.target as HTMLElement;
        if (target.closest('input, select, textarea, button, .nodrag, .toggle-switch, .optional-toggle, .node-pin-icon, a')) {
          return;
        }
        if (data.onInspect) {
          data.onInspect(id);
        }
      }}
      title={isMacro ? 'Double-click to inspect macro' : 'Double-click to inspect node'}
      style={{
        minHeight: `${calculatedMinHeight}px`
      }}
    >
      <span 
        className={`node-pin-icon ${data.pinned ? 'pinned' : ''}`}
        onClick={(e) => { 
          e.stopPropagation(); 
          handleChange('pinned', !data.pinned); 
        }}
        title={data.pinned ? "Unlock node" : "Pin node in place"}
      >
        📌
      </span>

      <NodeResizer 
        minWidth={isXYPlot ? 250 : 170} 
        minHeight={calculatedMinHeight} 
        isVisible={selected && !data.pinned} 
        lineStyle={{ border: '1px solid #3b82f6' }}
        handleStyle={{ width: 8, height: 8, background: '#3b82f6', borderRadius: '50%' }}
        onResizeStart={data.onResizeStart}
        onResizeEnd={data.onResizeEnd}
      />

      {/* --- EXECUTION HANDLES (Purple Diamond Style) --- */}
      {layout.execIns.map((pinName, i) => (
        <Handle
          key={`exec-in-${pinName}`}
          type="target"
          position={Position.Left}
          id={pinName}
          style={{
            top: getLeftHandleTop(true, i),
            background: '#a78bfa',
            borderColor: '#ffffff',
            borderRadius: '2px',
            width: '8px',
            height: '8px'
          }}
          title={`Exec Input: ${pinName}`}
        />
      ))}
      {layout.execOuts.map((pinName, i) => (
        <Handle
          key={`exec-out-${pinName}`}
          type="source"
          position={Position.Right}
          id={pinName}
          style={{
            top: getRightHandleTop(true, i),
            background: '#a78bfa',
            borderColor: '#ffffff',
            borderRadius: '2px',
            width: '8px',
            height: '8px'
          }}
          title={`Exec Output: ${pinName}`}
        />
      ))}

      {/* Data handles are rendered inline with their respective input/output fields below */}

      {/* --- HEADER --- */}
      <div 
        className="action-node-header" 
        onDoubleClick={(e) => { 
          e.stopPropagation();
          setIsEditingName(true); 
          setTempName(data.customName || layout.name); 
        }}
      >
        <div className="node-icon">{layout.icon}</div>
        {isEditingName ? (
          <input
            type="text"
            value={tempName}
            onChange={(e) => setTempName(e.target.value)}
            onBlur={() => {
              setIsEditingName(false);
              const trimmed = tempName.trim();
              handleChange('customName', trimmed || layout.name);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                setIsEditingName(false);
                const trimmed = tempName.trim();
                handleChange('customName', trimmed || layout.name);
              } else if (e.key === 'Escape') {
                setIsEditingName(false);
                setTempName(data.customName || layout.name);
              }
            }}
            autoFocus
            onFocus={(e) => e.target.select()}
            className="nodrag node-name-input"
          />
        ) : (
          <>
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '120px' }}>
              {data.customName || layout.name}
            </span>
            {data.isPersistent && (
              <span 
                className="node-persistence-lock" 
                title="Persistent node (kept in memory between runs)"
                style={{
                  fontSize: '0.75rem',
                  marginLeft: '4px',
                  opacity: 0.9,
                  cursor: 'pointer',
                  userSelect: 'none'
                }}
              >
                🔒
              </span>
            )}
            {data.notes && (
              <span 
                className="node-comment-badge" 
                title={data.notes}
                style={{
                  fontSize: '0.75rem',
                  marginLeft: '4px',
                  opacity: 0.8,
                  cursor: 'pointer'
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  if (data.onInspect) data.onInspect(id);
                }}
              >
                💬
              </span>
            )}
            <span 
              className="node-name-edit-icon" 
              onClick={(e) => { 
                e.stopPropagation(); 
                setIsEditingName(true); 
                setTempName(data.customName || layout.name); 
              }}
              title="Click to rename"
            >
              ✏️
            </span>
          </>
        )}
      </div>

      {/* --- BODY WIDGETS --- */}
      <div className="action-node-body">
        {isMacro && (
          <button
            className="script-edit-button nodrag"
            style={{
              background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.2) 100%)',
              border: '1px solid rgba(139, 92, 246, 0.4)',
              color: '#c4b5fd',
            }}
            onClick={() => {
              if (data.onNavigateInto) {
                data.onNavigateInto(id, data.action);
              }
            }}
          >
            📦 Expand Macro
          </button>
        )}

        {isScriptNode && (
          <button
            className="script-edit-button nodrag"
            onClick={() => {
              if (data.onEditScript) {
                data.onEditScript(id, data.code || '', data.action);
              }
            }}
          >
            ✏️ Edit Script
          </button>
        )}

        {isLibraryCallNode && (
          <button
            className="script-edit-button nodrag"
            style={{
              background: 'linear-gradient(135deg, rgba(16,185,129,0.15) 0%, rgba(5,150,105,0.15) 100%)',
              border: '1px solid rgba(16,185,129,0.35)',
              color: '#34d399',
            }}
            onClick={() => {
              if (data.onEditLibrarySignature) {
                data.onEditLibrarySignature(id);
              }
            }}
          >
            ⚙️ Edit Signature
          </button>
        )}

        {data.action === 'math/arithmetic/calculator' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%', padding: '4px' }}>
            {/* Expression Input */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Formula:</span>
              <input
                type="text"
                className="nodrag"
                value={data.expression ?? 'a + b'}
                onChange={(e) => handleChange('expression', e.target.value)}
                placeholder="a + b"
                style={{
                  background: 'var(--input-bg)',
                  border: '1px solid var(--node-border)',
                  color: 'var(--text-color)',
                  borderRadius: '4px',
                  padding: '4px 6px',
                  fontSize: '0.75rem',
                  width: '100%',
                  fontFamily: 'monospace',
                }}
              />
            </div>
            
            {/* Variables List & Add/Remove */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '2px' }}>
              <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Variables:</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', alignItems: 'center' }}>
                {(Array.isArray(data.variables)
                  ? data.variables
                  : typeof data.variables === 'string'
                    ? data.variables.split(',').map((v: string) => v.trim()).filter(Boolean)
                    : ['a', 'b']
                ).map((v: string, index: number) => (
                  <div
                    key={index}
                    style={{
                      background: 'rgba(59, 130, 246, 0.12)',
                      border: '1px solid rgba(59, 130, 246, 0.35)',
                      borderRadius: '3px',
                      padding: '2px 6px',
                      fontSize: '0.7rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      color: '#60a5fa',
                    }}
                  >
                    <span>{v}</span>
                    <button
                      className="nodrag"
                      onClick={() => {
                        const currentVars = Array.isArray(data.variables)
                          ? [...data.variables]
                          : typeof data.variables === 'string'
                            ? data.variables.split(',').map((x: string) => x.trim()).filter(Boolean)
                            : ['a', 'b'];
                        const updatedVars = currentVars.filter((x: string) => x !== v);
                        handleChange('variables', updatedVars);
                      }}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#ef4444',
                        cursor: 'pointer',
                        padding: 0,
                        fontSize: '0.75rem',
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        marginLeft: '2px',
                      }}
                      title={`Remove ${v}`}
                    >
                      ×
                    </button>
                  </div>
                ))}
                {(Array.isArray(data.variables)
                  ? data.variables
                  : typeof data.variables === 'string'
                    ? data.variables.split(',').map((v: string) => v.trim()).filter(Boolean)
                    : ['a', 'b']
                ).length === 0 && (
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    No variables. Add one below!
                  </span>
                )}
              </div>

              {/* Add Variable input and button */}
              <div style={{ display: 'flex', gap: '4px', marginTop: '4px', width: '100%' }}>
                <input
                  type="text"
                  placeholder="name"
                  value={newVarVal}
                  onChange={(e) => setNewVarVal(e.target.value)}
                  className="nodrag"
                  style={{
                    background: 'var(--input-bg)',
                    border: '1px solid var(--node-border)',
                    color: 'var(--text-color)',
                    borderRadius: '4px',
                    padding: '2px 4px',
                    fontSize: '0.68rem',
                    width: '65px',
                    minWidth: 0,
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      const val = newVarVal.trim().toLowerCase();
                      if (val && /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(val)) {
                        const currentVars = Array.isArray(data.variables)
                          ? [...data.variables]
                          : typeof data.variables === 'string'
                            ? data.variables.split(',').map((x: string) => x.trim()).filter(Boolean)
                            : ['a', 'b'];
                        if (!currentVars.includes(val)) {
                          handleChange('variables', [...currentVars, val]);
                        }
                        setNewVarVal('');
                      }
                    }
                  }}
                />
                <button
                  className="nodrag"
                  onClick={() => {
                    const val = newVarVal.trim().toLowerCase();
                    if (val && /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(val)) {
                      const currentVars = Array.isArray(data.variables)
                        ? [...data.variables]
                        : typeof data.variables === 'string'
                          ? data.variables.split(',').map((x: string) => x.trim()).filter(Boolean)
                          : ['a', 'b'];
                      if (!currentVars.includes(val)) {
                        handleChange('variables', [...currentVars, val]);
                      }
                      setNewVarVal('');
                    }
                  }}
                  style={{
                    background: 'var(--controls-bg)',
                    border: '1px solid var(--node-border)',
                    color: 'var(--text-color)',
                    borderRadius: '4px',
                    padding: '2px 6px',
                    fontSize: '0.68rem',
                    cursor: 'pointer',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                  }}
                >
                  + Add
                </button>
              </div>
            </div>
          </div>
        )}

        {data.action === 'script/rust' && (
          <div className="input-row" style={{ justifyContent: 'space-between', padding: '4px 0' }}>
            <span className="input-row-label" style={{ fontSize: '0.8rem' }}>Persist Cache: {data.persist_cache !== false ? 'ON' : 'OFF'}</span>
            <div 
              className={`toggle-switch ${data.persist_cache !== false ? 'active' : ''} nodrag`} 
              onClick={() => handleChange('persist_cache', data.persist_cache === false)}
              style={{
                width: '40px',
                height: '22px',
                borderRadius: '11px',
                background: data.persist_cache !== false ? '#10b981' : '#334155',
                position: 'relative',
                cursor: 'pointer',
                transition: 'background 0.2s',
                boxShadow: data.persist_cache !== false ? '0 0 8px rgba(16, 185, 129, 0.4)' : 'none'
              }}
            >
              <div 
                style={{
                  width: '16px',
                  height: '16px',
                  borderRadius: '50%',
                  background: '#ffffff',
                  position: 'absolute',
                  top: '3px',
                  left: data.persist_cache !== false ? '21px' : '3px',
                  transition: 'left 0.2s ease',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.4)'
                }}
              />
            </div>
          </div>
        )}

        {!isScriptNode && !isMacro && registryLayout?.original_code && (
          <button
            className="script-edit-button nodrag"
            onClick={() => {
              if (data.onEditScript) {
                data.onEditScript(id, data.code || registryLayout.original_code, data.action);
              }
            }}
          >
            ✏️ Modify Code
          </button>
        )}

        {data.action === 'constants/number' && (
          <div className="input-group">
            <label>Value</label>
            <NumericTextInput
              value={data.value ?? 0}
              onChange={(v) => handleChange('value', v)}
              className="nodrag"
            />
          </div>
        )}

        {data.action === 'constants/string' && (
          <div className="input-group">
            <label>Value</label>
            <input
              type="text"
              value={data.value ?? ''}
              onChange={(e) => handleChange('value', e.target.value)}
              className="nodrag"
            />
          </div>
        )}

        {data.action === 'constants/boolean' && (
          <div className="input-row" style={{ justifyContent: 'space-between', padding: '4px 0' }}>
            <span className="input-row-label" style={{ fontSize: '0.85rem' }}>State: {data.value ? 'ON' : 'OFF'}</span>
            <div 
              className={`toggle-switch ${data.value ? 'active' : ''} nodrag`} 
              onClick={() => handleChange('value', !data.value)}
              style={{
                width: '40px',
                height: '22px',
                borderRadius: '11px',
                background: data.value ? '#10b981' : '#334155',
                position: 'relative',
                cursor: 'pointer',
                transition: 'background 0.2s',
                boxShadow: data.value ? '0 0 8px rgba(16, 185, 129, 0.4)' : 'none'
              }}
            >
              <div 
                style={{
                  width: '16px',
                  height: '16px',
                  borderRadius: '50%',
                  background: '#ffffff',
                  position: 'absolute',
                  top: '3px',
                  left: data.value ? '21px' : '3px',
                  transition: 'left 0.2s ease',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.4)'
                }}
              />
            </div>
          </div>
        )}

        {data.action === 'hardware/virtual_generator' && (
          <RFGeneratorWidget
            waveType={data.wave_type}
            frequency={data.frequency}
            amplitude={data.amplitude}
            onChange={handleChange}
          />
        )}

        {(data.action === 'outputs/basic/display' || data.action === 'control_flow/timing/measure_time' || data.action === 'arrays/manipulation/accumulate') && (
          <DisplayScreenWidget 
            nodeId={id} 
            initialValue={data.results?.displayValue ?? data.results?.result} 
          />
        )}

        {/* Outputs / Live Plots */}
        {data.action === 'hardware/virtual_oscilloscope' && (
          <TimePlotWidget nodeId={id} strokeColor="#60a5fa" />
        )}

        {data.action === 'outputs/plots/plot' && (
          <TimePlotWidget nodeId={id} strokeColor="#34d399" dataKey="history" />
        )}

        {data.action === 'outputs/plots/xy_plot' && (
          <XYPlotWidget nodeId={id} xLabel={data.results?.x_label} yLabel={data.results?.y_label} />
        )}

        {data.action === 'outputs/plots/heatmap_plot' && (
          <HeatmapPlotWidget 
            nodeId={id}
            xLabel={data.results?.x_label}
            yLabel={data.results?.y_label}
          />
        )}

        {/* Render dynamic input parameter widgets dynamically based on Registry schema definitions */}
        {!NODES_WITH_CUSTOM_UI.includes(data.action) && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {visibleDataIns.map((pin: any) => {
              const isConnected = isPinConnected(pin.name);
              let pinVal = data[pin.name];
              if (pinVal === undefined) {
                pinVal = pin.defaultVal !== undefined ? pin.defaultVal : (pin.type === 'boolean' || pin.widget === 'checkbox' ? false : (pin.type === 'number' || pin.widget === 'slider' || pin.widget === 'number' ? 0 : ''));
              }

              let widgetContent = null;

              if (pin.widget === 'checkbox' || pin.type === 'boolean') {
                widgetContent = (
                  <div className="input-row" style={{ justifyContent: 'space-between', padding: '4px 0', opacity: isConnected ? 0.5 : 1, transition: 'opacity 0.2s ease', width: '100%' }}>
                    <span className="input-row-label" style={{ fontSize: '0.85rem' }}>{pin.label}: {pinVal ? 'ON' : 'OFF'}</span>
                    <div 
                      className={`toggle-switch ${pinVal ? 'active' : ''} nodrag`} 
                      onClick={() => { if (!isConnected) handleChange(pin.name, !pinVal); }}
                      style={{
                        width: '40px',
                        height: '22px',
                        borderRadius: '11px',
                        background: pinVal ? '#10b981' : '#334155',
                        position: 'relative',
                        cursor: isConnected ? 'not-allowed' : 'pointer',
                        transition: 'background 0.2s',
                        boxShadow: pinVal ? '0 0 8px rgba(16, 185, 129, 0.4)' : 'none'
                      }}
                    >
                      <div 
                        style={{
                          width: '16px',
                          height: '16px',
                          borderRadius: '50%',
                          background: '#ffffff',
                          position: 'absolute',
                          top: '3px',
                          left: pinVal ? '21px' : '3px',
                          transition: 'left 0.2s ease',
                          boxShadow: '0 1px 3px rgba(0,0,0,0.4)'
                        }}
                      />
                    </div>
                  </div>
                );
              } else if (pin.widget === 'slider') {
                widgetContent = (
                  <div className="input-group" style={{ opacity: isConnected ? 0.5 : 1, transition: 'opacity 0.2s ease', width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-color)' }}>
                      <label>{pin.label}</label>
                      <span>{pinVal}</span>
                    </div>
                    <input
                      type="range"
                      min={pin.min ?? 0}
                      max={pin.max ?? 100}
                      step={pin.step ?? 1}
                      value={pinVal}
                      onChange={(e) => handleChange(pin.name, parseFloat(e.target.value))}
                      disabled={isConnected}
                      className="nodrag"
                      style={{ width: '100%' }}
                    />
                  </div>
                );
              } else if (pin.widget === 'dropdown') {
                widgetContent = (
                  <div className="input-group" style={{ opacity: isConnected ? 0.5 : 1, transition: 'opacity 0.2s ease', width: '100%' }}>
                    <label>{pin.label}</label>
                    <select
                      value={pinVal}
                      onChange={(e) => handleChange(pin.name, e.target.value)}
                      disabled={isConnected}
                      className="nodrag"
                    >
                      {(pin.options || []).map((opt: string) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  </div>
                );
              } else if (pin.widget === 'number' || pin.type === 'number') {
                widgetContent = (
                  <div className="input-row" style={{ opacity: isConnected ? 0.5 : 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '4px 0', transition: 'opacity 0.2s ease', width: '100%' }}>
                    <span className="input-row-label" style={{ fontSize: '0.75rem', color: 'var(--text-color)' }}>{pin.label}</span>
                    <NumericTextInput
                      value={pinVal}
                      onChange={(v) => handleChange(pin.name, v)}
                      readOnly={isConnected}
                      min={pin.min}
                      max={pin.max}
                      className="nodrag"
                      style={{ flex: 1, marginLeft: '12px', minWidth: '40px', padding: '2px 4px', fontSize: '0.8rem', background: 'var(--input-bg)', border: '1px solid var(--node-border)', borderRadius: '4px', color: 'var(--text-color)' }}
                    />
                  </div>
                );
              } else if (pin.widget === 'text' || pin.type === 'text') {
                widgetContent = (
                  <div className="input-row" style={{ opacity: isConnected ? 0.5 : 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '4px 0', transition: 'opacity 0.2s ease', width: '100%' }}>
                    <span className="input-row-label" style={{ fontSize: '0.75rem', color: 'var(--text-color)' }}>{pin.label}</span>
                    <input
                      type="text"
                      value={pinVal}
                      onChange={(e) => handleChange(pin.name, e.target.value)}
                      readOnly={isConnected}
                      className="nodrag"
                      style={{ flex: 1, marginLeft: '12px', minWidth: '40px', padding: '2px 4px', fontSize: '0.8rem', background: 'var(--input-bg)', border: '1px solid var(--node-border)', borderRadius: '4px', color: 'var(--text-color)' }}
                    />
                  </div>
                );
              } else {
                widgetContent = (
                  <div className="input-row" style={{ justifyContent: 'space-between', padding: '2px 0', opacity: 1, transition: 'opacity 0.2s ease', width: '100%' }}>
                    <span className="input-row-label" style={{ fontSize: '0.7rem', color: 'var(--text-color)', textAlign: 'left' }}>
                      ↳ {pin.label}
                    </span>
                  </div>
                );
              }

              return (
                <div key={pin.name} style={{ position: 'relative', width: '100%', display: 'flex', alignItems: 'center' }}>
                  <Handle
                    type="target"
                    position={Position.Left}
                    id={pin.name}
                    style={{
                      position: 'absolute',
                      left: '-18px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: getPinColor(pin.type),
                      borderColor: '#ffffff',
                      width: '8px',
                      height: '8px'
                    }}
                    title={`Data Input: ${pin.label} (${pin.type || 'any'})${getConnectedPinValue(pin.name) !== undefined ? `\nValue: ${getConnectedPinValue(pin.name)}` : ''}`}
                  />
                  {widgetContent}
                </div>
              );
            })}
          </div>
        )}

        {/* Display connection label rows for pure visual clarity (only for visual overrides that don't render standard widgets) */}
        {visibleDataIns.length > 0 && [
          'outputs/basic/display', 
          'control_flow/timing/measure_time', 
          'arrays/manipulation/accumulate', 
          'hardware/virtual_oscilloscope', 
          'outputs/plots/plot', 
          'outputs/plots/xy_plot',
          'math/arithmetic/calculator'
        ].includes(data.action) && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {visibleDataIns.map(pin => (
              <div key={`label-in-${pin.name}`} style={{ fontSize: '0.7rem', color: 'var(--text-color)', textAlign: 'left', position: 'relative', width: '100%' }}>
                <Handle
                  type="target"
                  position={Position.Left}
                  id={pin.name}
                  style={{
                    position: 'absolute',
                    left: '-18px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: getPinColor(pin.type),
                    borderColor: '#ffffff',
                    width: '8px',
                    height: '8px'
                  }}
                  title={`Data Input: ${pin.label} (${pin.type || 'any'})${getConnectedPinValue(pin.name) !== undefined ? `\nValue: ${getConnectedPinValue(pin.name)}` : ''}`}
                />
                ↳ {pin.label}
              </div>
            ))}
          </div>
        )}

        {layout.dataOuts.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '6px' }}>
            {layout.dataOuts.map(pin => (
              <div key={`label-out-${pin.name}`} style={{ fontSize: '0.7rem', color: 'var(--text-color)', textAlign: 'right', position: 'relative', width: '100%' }}>
                <Handle
                  type="source"
                  position={Position.Right}
                  id={pin.name}
                  style={{
                    position: 'absolute',
                    right: '-18px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: getPinColor(pin.type),
                    borderColor: '#ffffff',
                    width: '8px',
                    height: '8px'
                  }}
                  title={`Data Output: ${pin.label} (${pin.type || 'any'})${data.pinValues?.[pin.name] !== undefined ? `\nValue: ${data.pinValues[pin.name]}` : ''}`}
                />
                {pin.label} ↲
              </div>
            ))}
          </div>
        )}
      </div>

      {hasOptionalInputs && (
        <div 
          ref={optionalToggleRef}
          className="nodrag optional-toggle"
          onClick={() => setShowOptional(!showOptional)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '6px 0',
            marginTop: '4px',
            marginBottom: '4px',
            cursor: 'pointer',
            fontSize: '0.7rem',
            fontWeight: 500,
            color: 'var(--text-muted)',
            borderRadius: '4px',
            background: 'var(--dnd-bg)',
            border: '1px dashed var(--node-border)',
            transition: 'all 0.2s ease',
            userSelect: 'none'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--dnd-hover-bg)';
            e.currentTarget.style.color = 'var(--accent-color)';
            e.currentTarget.style.borderColor = 'var(--accent-color)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--dnd-bg)';
            e.currentTarget.style.color = 'var(--text-muted)';
            e.currentTarget.style.borderColor = 'var(--node-border)';
          }}
        >
          <span style={{ 
            display: 'inline-block', 
            transition: 'transform 0.2s ease', 
            transform: showOptional ? 'rotate(180deg)' : 'rotate(0deg)',
            marginRight: '6px'
          }}>
            ▼
          </span>
          {showOptional ? 'Hide Optional Settings' : 'Show Optional Settings'}
        </div>
      )}

      {/* --- STATUS BAR --- */}
      <div ref={statusBarRef} id={`node-status-${id}`} className={`node-status ${data.status || 'idle'}`}>
        <span id={`node-msg-${id}`}>
          {data.status === 'running' ? '⏳ Running...' : data.status === 'stopped' ? '⏹️ Stopped' : (data.resultMessage || 'Idle')}
        </span>
      </div>
    </div>
  );
};
