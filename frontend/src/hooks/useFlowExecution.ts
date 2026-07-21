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
}

export function useFlowExecution({
  activeTabId,
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
}: UseFlowExecutionProps) {
  const wsRef = useRef<WebSocket | null>(null);
  
  const isRunningRef = useRef(isRunning);
  const isPausedRef = useRef(isPaused);
  const activeTabIdRef = useRef(activeTabId);
  const runningTabIdRef = useRef(runningTabId);
  const blockRegistryRef = useRef(blockRegistry);

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
  }>>({});

  const flushUpdatesRef = useRef<(() => void) | undefined>(undefined);

  // Flush pending updates every 100ms to throttle React state updates & avoid scheduler queue leaks
  useEffect(() => {
    const flushUpdates = () => {
      const updates = pendingUpdatesRef.current;
      if (Object.keys(updates).length === 0) return;

      // Clear the ref immediately so subsequent messages go into a clean state
      pendingUpdatesRef.current = {};

      // 1. Update active blocks state
      // 1. Dispatch custom events to bypass React's state tree and avoid Fiber re-allocations
      if (activeTabIdRef.current === runningTabIdRef.current) {
        Object.keys(updates).forEach(blockId => {
          const update = updates[blockId];
          const existingNode = blocksRef.current.find((n: any) => n.id === blockId);
          if (existingNode) {
            // Mutate in-place
            if (update.status !== undefined) existingNode.data.status = update.status;
            if (update.statusMessage !== undefined) existingNode.data.resultMessage = update.statusMessage;
            if (update.results) {
               if (!existingNode.data.results) existingNode.data.results = {};
               Object.assign(existingNode.data.results, update.results);
            }
            if (update.value !== undefined) {
               if (!existingNode.data.results) existingNode.data.results = {};
               
               const uiBehavior = blockRegistryRef.current?.[existingNode.data.action]?.ui_behavior || {};
               
               if (uiBehavior.accumulate_history) {
                  const val = parseFloat(update.value);
                  const oldHistory = existingNode.data.results.history || [];
                  
                  let maxHistory = 0;
                  if (update.results?.max_history !== undefined) {
                     maxHistory = Number(update.results.max_history);
                  } else if (existingNode.data.results?.max_history !== undefined) {
                     maxHistory = Number(existingNode.data.results.max_history);
                  }
                  
                  if (maxHistory > 0) {
                     existingNode.data.results.history = [...oldHistory, val].slice(-maxHistory);
                  } else {
                     existingNode.data.results.history = [...oldHistory, val];
                  }
               } else {
                  existingNode.data.results.displayValue = update.value;
               }
            }
            if (update.resultMessage !== undefined && update.value === undefined && update.statusMessage === undefined) {
               existingNode.data.resultMessage = update.resultMessage;
            }
            if (update.pinValues) {
               existingNode.data.pinValues = { ...(existingNode.data.pinValues || {}), ...update.pinValues };
            }
            
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
      }
    };
    
    flushUpdatesRef.current = flushUpdates;
    const interval = setInterval(flushUpdates, 100);

    return () => clearInterval(interval);
  }, [setBlocks]);

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
        
        // Mutate in-place to avoid React state GC pressure and Fiber memory leaks
        const existingNode = blocksRef.current.find((n: any) => n.id === blockId);
        if (existingNode) {
          if (!existingNode.data.results) existingNode.data.results = {};
          existingNode.data.results.waveform = waveform;
          existingNode.data.resultMessage = `Captured (Binary): ${waveform.length} pts`;
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
        
        // Find existing block to perform in-place mutation for large arrays
        const existingNode = blocksRef.current.find((n: any) => n.id === block_id);
        let hasArrayData = false;
        
        if (existingNode && data) {
          if (!existingNode.data.results) existingNode.data.results = {};
          
          for (const key of Object.keys(data)) {
            // If the payload contains a large array, intercept it
            if (Array.isArray(data[key]) && data[key].length > 0) {
              existingNode.data.results[key] = data[key];
              hasArrayData = true;
            }
          }
        }

        if (!pendingUpdatesRef.current[block_id]) {
          pendingUpdatesRef.current[block_id] = {};
        }
        if (!pendingUpdatesRef.current[block_id].results) {
          pendingUpdatesRef.current[block_id].results = {};
        }

        // Generate messages based on the intercepted arrays on the block, since we are about to delete them from `data`
        if (hasArrayData && existingNode) {
          if (existingNode.data.results.waveform) {
            pendingUpdatesRef.current[block_id].resultMessage = `Captured: ${existingNode.data.results.waveform.length} pts`;
          } else if (existingNode.data.results.z) {
             const zArr = existingNode.data.results.z;
             pendingUpdatesRef.current[block_id].resultMessage = `Plotted 2D: ${zArr[0]?.length || 0}x${zArr.length || 0}`;
          } else if (existingNode.data.results.x && existingNode.data.results.y) {
            pendingUpdatesRef.current[block_id].resultMessage = `Plotted ${existingNode.data.results.y.length} pts`;
          }
        }

        // Remove large arrays from data so they don't enter React's setBlocks pipeline
        if (hasArrayData) {
          for (const key of Object.keys(data)) {
             if (Array.isArray(data[key]) && data[key].length > 0) {
                 delete data[key];
             }
          }
        }

        pendingUpdatesRef.current[block_id].results = {
          ...pendingUpdatesRef.current[block_id].results,
          ...data
        };
        
        // Handle small/scalar data messages
        if (data.value !== undefined) {
          pendingUpdatesRef.current[block_id].value = data.value;
        } else if (data.state !== undefined) {
          pendingUpdatesRef.current[block_id].resultMessage = `State: ${data.state ? 'ON' : 'OFF'}`;
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
          
          setIsRunning(false);
          setIsPaused(false);
          setRunningTabId(null);
          if (msg.status === 'failed') {
            setErrorMessage(msg.error || 'Execution failed.');
          }

          pendingUpdatesRef.current = {};

          if (msg.status === 'failed' || msg.status === 'aborted') {
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
  }, [WS_BACKEND_URL, setBlocks, setTabs, setIsRunning, setIsPaused, setRunningTabId, setErrorMessage]);

  const handleRun = useCallback(async () => {
    setIsRunning(true);
    setIsPaused(false);
    setErrorMessage(null);
    setRunningTabId(activeTabIdRef.current);

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
