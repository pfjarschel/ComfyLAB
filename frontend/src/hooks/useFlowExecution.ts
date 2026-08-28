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

import { useRef, useEffect, useCallback } from 'react';
import axios from 'axios';

export interface UseFlowExecutionProps {
  activeTabId: string;
  tabs?: any[];
  blocks: any[];
  edges: any[];
  currentBlueprintName: string;
  setBlocks: React.Dispatch<React.SetStateAction<any[]>>;
  setTabs: React.Dispatch<React.SetStateAction<any[]>>;
  exportBlueprint: () => any;
  BACKEND_URL: string;
  WS_BACKEND_URL: string;
  
  // State variables passed from App.tsx
  isRunning: boolean;
  setIsRunning: React.Dispatch<React.SetStateAction<boolean>>;
  isPaused: boolean;
  setIsPaused: React.Dispatch<React.SetStateAction<boolean>>;
  runningTabId: string | null;
  setRunningTabId: React.Dispatch<React.SetStateAction<string | null>>;
  setErrorMessage: React.Dispatch<React.SetStateAction<string | null>>;
  blockRegistry: Record<string, any> | null;
  liteMode?: boolean;
}

const applyUpdateToNode = (existingNode: any, update: any, registry: any) => {
  if (!existingNode || !existingNode.data) return;
  if (update.status !== undefined) existingNode.data.status = update.status;
  if (update.statusMessage !== undefined) existingNode.data.resultMessage = update.statusMessage;
  if (update.results) {
    if (!existingNode.data.results) existingNode.data.results = {};
    Object.assign(existingNode.data.results, update.results);
  }

  const uiBehavior = registry?.[existingNode.data.action]?.ui_behavior || {};

  if (uiBehavior.accumulate_history) {
    if (update.valuesQueue && update.valuesQueue.length > 0) {
      if (!existingNode.data.results) existingNode.data.results = {};
      let oldHistory = existingNode.data.results.history || [];
      let oldTimeHistory = existingNode.data.results.time_history || [];

      for (const item of update.valuesQueue) {
        let val;
        if (Array.isArray(item.value)) {
          val = item.value.map((v: any) => parseFloat(v));
        } else {
          val = parseFloat(item.value);
        }

        let maxHistory = 0;
        if (item.max_history !== undefined) {
          maxHistory = Number(item.max_history);
        } else if (existingNode.data.results?.max_history !== undefined) {
          maxHistory = Number(existingNode.data.results.max_history);
        }

        oldHistory.push(val);
        if (item.timestamp !== undefined && item.timestamp !== null) {
          oldTimeHistory.push(item.timestamp);
        }

        if (maxHistory > 0 && oldHistory.length > maxHistory) {
          oldHistory = oldHistory.slice(-maxHistory);
          if (oldTimeHistory.length > maxHistory) {
            oldTimeHistory = oldTimeHistory.slice(-maxHistory);
          }
        }
      }

      existingNode.data.results.history = oldHistory;
      existingNode.data.results.time_history = oldTimeHistory.length > 0 ? oldTimeHistory : [];
    } else if (update.value !== undefined) {
      if (!existingNode.data.results) existingNode.data.results = {};
      let val;
      if (Array.isArray(update.value)) {
        val = update.value.map((v: any) => parseFloat(v));
      } else {
        val = parseFloat(update.value);
      }
      const oldHistory = existingNode.data.results.history || [];
      const oldTimeHistory = existingNode.data.results.time_history || [];

      let maxHistory = 0;
      if (update.results?.max_history !== undefined) {
        maxHistory = Number(update.results.max_history);
      } else if (existingNode.data.results?.max_history !== undefined) {
        maxHistory = Number(existingNode.data.results.max_history);
      }

      const timestamp = update.results?.timestamp;

      if (maxHistory > 0) {
        existingNode.data.results.history = [...oldHistory, val].slice(-maxHistory);
        if (timestamp !== undefined && timestamp !== null) {
          existingNode.data.results.time_history = [...oldTimeHistory, timestamp].slice(-maxHistory);
        } else {
          existingNode.data.results.time_history = [];
        }
      } else {
        existingNode.data.results.history = [...oldHistory, val];
        if (timestamp !== undefined && timestamp !== null) {
          existingNode.data.results.time_history = [...oldTimeHistory, timestamp];
        } else {
          existingNode.data.results.time_history = [];
        }
      }
    }
  } else {
    if (update.value !== undefined) {
      if (!existingNode.data.results) existingNode.data.results = {};
      existingNode.data.results.displayValue = update.value;
    }
  }

  if (update.resultMessage !== undefined && update.value === undefined && update.statusMessage === undefined) {
    existingNode.data.resultMessage = update.resultMessage;
  }
  if (update.pinValues) {
    existingNode.data.pinValues = { ...(existingNode.data.pinValues || {}), ...update.pinValues };
  }
};

export function useFlowExecution({
  activeTabId,
  tabs = [],
  blocks,
  edges,
  currentBlueprintName,
  setBlocks,
  setTabs,
  exportBlueprint,
  BACKEND_URL,
  WS_BACKEND_URL,
  isRunning,
  setIsRunning,
  isPaused,
  setIsPaused,
  runningTabId,
  setRunningTabId,
  setErrorMessage,
  blockRegistry,
  liteMode = false,
}: UseFlowExecutionProps) {
  const wsRef = useRef<WebSocket | null>(null);
  
  const isRunningRef = useRef(isRunning);
  const isPausedRef = useRef(isPaused);
  const activeTabIdRef = useRef(activeTabId);
  const runningTabIdRef = useRef(runningTabId);
  const blockRegistryRef = useRef(blockRegistry);
  const tabsRef = useRef<any[]>(tabs);

  useEffect(() => { tabsRef.current = tabs; }, [tabs]);
  useEffect(() => { blockRegistryRef.current = blockRegistry; }, [blockRegistry]);

  useEffect(() => { isRunningRef.current = isRunning; }, [isRunning]);
  useEffect(() => { isPausedRef.current = isPaused; }, [isPaused]);
  useEffect(() => { activeTabIdRef.current = activeTabId; }, [activeTabId]);
  useEffect(() => { runningTabIdRef.current = runningTabId; }, [runningTabId]);

  const blocksRef = useRef<any[]>(blocks);
  const edgesRef = useRef<any[]>(edges);
  useEffect(() => { blocksRef.current = blocks; }, [blocks]);
  useEffect(() => { edgesRef.current = edges; }, [edges]);

  // Ref for batching high-frequency telemetry updates
  const pendingUpdatesRef = useRef<Record<string, {
    status?: string;
    statusMessage?: string;
    results?: Record<string, any>;
    resultMessage?: string;
    pinValues?: Record<string, any>;
    value?: any;
    valuesQueue?: Array<{ value: any; timestamp?: number; max_history?: number }>;
  }>>({});

  const flushUpdatesRef = useRef<(() => void) | undefined>(undefined);

  // Flush pending updates every 100ms to throttle React state updates & avoid scheduler queue leaks
  useEffect(() => {
    const flushUpdates = () => {
      const updates = pendingUpdatesRef.current;
      if (Object.keys(updates).length === 0) return;

      // Clear the ref immediately so subsequent messages go into a clean state
      pendingUpdatesRef.current = {};

      const isForeground = activeTabIdRef.current === runningTabIdRef.current;
      if (isForeground) {
        // Active foreground tab: mutate blocks in active memory and dispatch custom DOM events
        Object.keys(updates).forEach(blockId => {
          const update = updates[blockId];
          const existingNode = blocksRef.current.find((n: any) => n.id === blockId);
          if (existingNode) {
            applyUpdateToNode(existingNode, update, blockRegistryRef.current);
            
            // Dispatch to local block plot widgets
            window.dispatchEvent(new CustomEvent(`telemetry-${blockId}`, {
              detail: {
                status: existingNode.data.status,
                resultMessage: existingNode.data.resultMessage,
                results: existingNode.data.results
              }
            }));
          }
        });
      } else {
        // Running tab is currently in the background: update its blocks inside tabsRef
        const rTabId = runningTabIdRef.current;
        if (rTabId) {
          const targetTab = tabsRef.current.find((t: any) => t.id === rTabId);
          if (targetTab && targetTab.blocks) {
            targetTab.blocks.forEach((node: any) => {
              const update = updates[node.id];
              if (update) {
                applyUpdateToNode(node, update, blockRegistryRef.current);
              }
            });
          }
        }
      }
    };
    
    flushUpdatesRef.current = flushUpdates;
    const intervalMs = liteMode ? 200 : 100;
    const interval = setInterval(flushUpdates, intervalMs);

    return () => clearInterval(interval);
  }, [setBlocks, liteMode]);

  const startTelemetryStream = useCallback((runId: string) => {
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (e) {}
    }

    const savedToken = localStorage.getItem("comfylab-auth-token") || "";
    const tokenQuery = savedToken ? `?token=${encodeURIComponent(savedToken)}` : '';
    const ws = new WebSocket(`${WS_BACKEND_URL}/telemetry/${runId}${tokenQuery}`);
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;
    pendingUpdatesRef.current = {};

    const decoder = new TextDecoder('utf-8');

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        const buffer = event.data;
        
        // 1. Read block_id (first 36 bytes)
        const blockIdBytes = new Uint8Array(buffer, 0, 36);
        const blockId = decoder.decode(blockIdBytes).replace(/\0/g, '').trim();
        
        // 2. Read point_count (bytes 36-39)
        const countView = new DataView(buffer, 36, 4);
        const pointCount = countView.getUint32(0, true);
        
        // 3. Read waveform floats (bytes 40 onwards)
        const waveform = new Float32Array(buffer, 40, pointCount);
        
        const isForeground = activeTabIdRef.current === runningTabIdRef.current;
        if (isForeground) {
          const existingNode = blocksRef.current.find((n: any) => n.id === blockId);
          if (existingNode) {
            if (!existingNode.data.results) existingNode.data.results = {};
            existingNode.data.results.waveform = waveform;
            existingNode.data.resultMessage = `Captured (Binary): ${waveform.length} pts`;
          }
        } else {
          const rTabId = runningTabIdRef.current;
          if (rTabId) {
            const targetTab = tabsRef.current.find((t: any) => t.id === rTabId);
            const node = targetTab?.blocks?.find((n: any) => n.id === blockId);
            if (node) {
              if (!node.data.results) node.data.results = {};
              node.data.results.waveform = waveform;
              node.data.resultMessage = `Captured (Binary): ${waveform.length} pts`;
            }
          }
        }

        // We specifically DO NOT add the waveform array to pendingUpdatesRef to prevent it from going into React state.
        if (!pendingUpdatesRef.current[blockId]) {
          pendingUpdatesRef.current[blockId] = {};
        }
        pendingUpdatesRef.current[blockId].resultMessage = `Captured (Binary): ${waveform.length} pts`;
        return;
      }

      const msg = JSON.parse(event.data);
      
      if (msg.type === 'status') {
        // Batch status updates into pendingUpdatesRef instead of direct state updates
        const blockId = msg.block_id;
        if (!pendingUpdatesRef.current[blockId]) {
          pendingUpdatesRef.current[blockId] = {};
        }
        pendingUpdatesRef.current[blockId].status = msg.status;
        pendingUpdatesRef.current[blockId].statusMessage = msg.message || (msg.status === 'success' ? 'Success' : '');
      } else if (msg.type === 'telemetry') {
        const { block_id, data } = msg;
        if (!data) return;

        if (!pendingUpdatesRef.current[block_id]) {
          pendingUpdatesRef.current[block_id] = {};
        }
        if (!pendingUpdatesRef.current[block_id].results) {
          pendingUpdatesRef.current[block_id].results = {};
        }

        // Determine human-readable result message based on telemetry data
        if (data.resultMessage !== undefined) {
          pendingUpdatesRef.current[block_id].resultMessage = data.resultMessage;
        } else if (data.statusMessage !== undefined) {
          pendingUpdatesRef.current[block_id].resultMessage = data.statusMessage;
        } else if (data.message !== undefined) {
          pendingUpdatesRef.current[block_id].resultMessage = data.message;
        } else if (data.waveform && (Array.isArray(data.waveform) || ArrayBuffer.isView(data.waveform))) {
          pendingUpdatesRef.current[block_id].resultMessage = `Captured: ${data.waveform.length} pts`;
        } else if (data.z && Array.isArray(data.z)) {
          const zArr = data.z;
          pendingUpdatesRef.current[block_id].resultMessage = `Plotted 2D: ${zArr[0]?.length || 0}x${zArr.length || 0}`;
        } else if (data.y && (Array.isArray(data.y) || ArrayBuffer.isView(data.y))) {
          const ptCount = Array.isArray(data.y[0]) ? data.y[0].length : data.y.length;
          pendingUpdatesRef.current[block_id].resultMessage = `Plotted ${ptCount} pts`;
        } else if (data.state !== undefined) {
          pendingUpdatesRef.current[block_id].resultMessage = `State: ${data.state ? 'ON' : 'OFF'}`;
        }

        // Retain all telemetry keys intact in results (x, y, z, waveform, limits, logs, labels, etc.)
        Object.assign(pendingUpdatesRef.current[block_id].results, data);
        
        // Handle scalar or time-series data values
        if (data.value !== undefined) {
          pendingUpdatesRef.current[block_id].value = data.value;
          if (!pendingUpdatesRef.current[block_id].valuesQueue) {
            pendingUpdatesRef.current[block_id].valuesQueue = [];
          }
          pendingUpdatesRef.current[block_id].valuesQueue.push({
            value: data.value,
            timestamp: data.timestamp,
            max_history: data.max_history
          });
        }
      } else if (msg.type === 'pin_values') {
        const { block_id, pin_values } = msg;
        if (!pendingUpdatesRef.current[block_id]) {
          pendingUpdatesRef.current[block_id] = {};
        }
        pendingUpdatesRef.current[block_id].pinValues = {
          ...pendingUpdatesRef.current[block_id].pinValues,
          ...pin_values
        };
      } else if (msg.type === 'run_status') {
        if (msg.status === 'completed' || msg.status === 'failed' || msg.status === 'aborted') {
          // Flush any final telemetry before shutting down the flow!
          if (flushUpdatesRef.current) {
             flushUpdatesRef.current();
          }
          
          const finishedTabId = runningTabIdRef.current;
          setIsRunning(false);
          setIsPaused(false);
          setRunningTabId(null);
          isRunningRef.current = false;
          isPausedRef.current = false;
          runningTabIdRef.current = null;
          if (msg.status === 'failed') {
            setErrorMessage(msg.error || 'Execution failed.');
          }

          pendingUpdatesRef.current = {};

          const targetStatus = msg.status === 'completed' ? 'success' : 'stopped';
          const targetMsg = msg.status === 'completed' ? 'Completed' : 'Stopped';

          if (activeTabIdRef.current === finishedTabId) {
            setBlocks((nds) =>
              nds.map((block) => {
                if (block.data?.status === 'running') {
                  return {
                    ...block,
                    data: {
                      ...block.data,
                      status: targetStatus,
                      resultMessage: targetMsg,
                    },
                  };
                }
                return block;
              })
            );
          }

          if (finishedTabId) {
            setTabs((prevTabs) =>
              prevTabs.map((t) => {
                if (t.id === finishedTabId) {
                  const updatedNodes = (t.blocks || []).map((block: any) => {
                    if (block.data?.status === 'running') {
                      return {
                        ...block,
                        data: {
                          ...block.data,
                          status: targetStatus,
                          resultMessage: targetMsg,
                        },
                      };
                    }
                    return block;
                  });
                  return { ...t, blocks: updatedNodes };
                }
                return t;
              })
            );
          }

          ws.close();
        } else if (msg.status === 'paused') {
          setIsPaused(true);
        } else if (msg.status === 'running') {
          setIsPaused(false);
        }
      }
    };

    ws.onclose = () => {
      console.log('[Telemetry WS] Closed.');
      pendingUpdatesRef.current = {};
    };

    ws.onerror = (err) => {
      console.error('[Telemetry WS] Error:', err);
    };
  }, [WS_BACKEND_URL, setBlocks, setTabs, setIsRunning, setIsPaused, setRunningTabId, setErrorMessage]);

  const handleRun = useCallback(async () => {
    setIsRunning(true);
    setIsPaused(false);
    setErrorMessage(null);
    setRunningTabId(activeTabIdRef.current);
    isRunningRef.current = true;
    isPausedRef.current = false;
    runningTabIdRef.current = activeTabIdRef.current;

    // Reset status on all blocks
    setBlocks((nds) =>
      nds.map((n) => ({
        ...n,
        data: { ...n.data, status: 'idle', resultMessage: '' },
      }))
    );

    const rawCanvas = {
      blocks: blocksRef.current.map(({ id, type, position, data, style }) => {
        const persistData = { ...data };
        delete persistData.onChange;
        delete persistData.status;
        delete persistData.resultMessage;
        delete persistData.result;
        delete persistData.results;
        delete persistData.waveform;
        delete persistData.history;
        return { id, type, position, data: persistData, style };
      }),
      edges: edgesRef.current,
      blueprintName: currentBlueprintName || 'Untitled'
    };

    const blueprint = {
      ...exportBlueprint(),
      raw_canvas: rawCanvas
    };

    try {
      const response = await axios.post(`${BACKEND_URL}/run`, blueprint);
      const { run_id } = response.data;
      startTelemetryStream(run_id);
    } catch (err: any) {
      setIsRunning(false);
      setIsPaused(false);
      setRunningTabId(null);
      isRunningRef.current = false;
      isPausedRef.current = false;
      runningTabIdRef.current = null;
      setErrorMessage(err.response?.data?.detail || 'Failed to start execution.');
    }
  }, [BACKEND_URL, exportBlueprint, currentBlueprintName, setBlocks, startTelemetryStream, setIsRunning, setIsPaused, setRunningTabId, setErrorMessage]);

  const handlePause = useCallback(async () => {
    try {
      await axios.post(`${BACKEND_URL}/pause`);
      setIsPaused(true);
    } catch (err) {
      console.error('Failed to pause execution:', err);
    }
  }, [BACKEND_URL, setIsPaused]);

  const handleResume = useCallback(async () => {
    try {
      await axios.post(`${BACKEND_URL}/resume`);
      setIsPaused(false);
    } catch (err) {
      console.error('Failed to resume execution:', err);
    }
  }, [BACKEND_URL, setIsPaused]);

  const handleAbort = useCallback(async () => {
    try {
      await axios.post(`${BACKEND_URL}/abort`);
      setIsRunning(false);
      setIsPaused(false);
      setRunningTabId(null);
      isRunningRef.current = false;
      isPausedRef.current = false;
      runningTabIdRef.current = null;

      setBlocks((nds) =>
        nds.map((block) => {
          if (block.data.status === 'running') {
            return {
              ...block,
              data: {
                ...block.data,
                status: 'stopped',
                resultMessage: 'Stopped',
              },
            };
          }
          return block;
        })
      );

      setTabs((prevTabs) =>
        prevTabs.map((t) => {
          if (t.id === runningTabIdRef.current) {
            const updatedNodes = t.blocks.map((block: any) => {
              if (block.data.status === 'running') {
                return {
                  ...block,
                  data: {
                    ...block.data,
                    status: 'stopped',
                    resultMessage: 'Stopped',
                  },
                };
              }
              return block;
            });
            return { ...t, blocks: updatedNodes };
          }
          return t;
        })
      );
    } catch (err) {
      console.error('Failed to abort execution:', err);
    }
  }, [BACKEND_URL, setIsRunning, setIsPaused, setRunningTabId, setBlocks, setTabs]);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    handleRun,
    handlePause,
    handleResume,
    handleAbort,
    startTelemetryStream,
    wsRef,
  };
}
