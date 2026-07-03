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
  nodes: any[];
  edges: any[];
  currentBlueprintName: string;
  setNodes: React.Dispatch<React.SetStateAction<any[]>>;
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
}

export function useFlowExecution({
  activeTabId,
  nodes,
  edges,
  currentBlueprintName,
  setNodes,
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
}: UseFlowExecutionProps) {
  const wsRef = useRef<WebSocket | null>(null);
  
  const isRunningRef = useRef(isRunning);
  const isPausedRef = useRef(isPaused);
  const activeTabIdRef = useRef(activeTabId);
  const runningTabIdRef = useRef(runningTabId);

  useEffect(() => { isRunningRef.current = isRunning; }, [isRunning]);
  useEffect(() => { isPausedRef.current = isPaused; }, [isPaused]);
  useEffect(() => { activeTabIdRef.current = activeTabId; }, [activeTabId]);
  useEffect(() => { runningTabIdRef.current = runningTabId; }, [runningTabId]);

  const nodesRef = useRef<any[]>(nodes);
  const edgesRef = useRef<any[]>(edges);
  useEffect(() => { nodesRef.current = nodes; }, [nodes]);
  useEffect(() => { edgesRef.current = edges; }, [edges]);

  const startTelemetryStream = useCallback((runId: string) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const savedToken = localStorage.getItem("comfylab-auth-token") || "";
    const tokenQuery = savedToken ? `?token=${encodeURIComponent(savedToken)}` : '';
    const ws = new WebSocket(`${WS_BACKEND_URL}/telemetry/${runId}${tokenQuery}`);
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        const buffer = event.data;
        const decoder = new TextDecoder('utf-8');
        
        // 1. Read node_id (first 36 bytes)
        const nodeIdBytes = new Uint8Array(buffer, 0, 36);
        const nodeId = decoder.decode(nodeIdBytes).replace(/\0/g, '').trim();
        
        // 2. Read point_count (bytes 36-39)
        const countView = new DataView(buffer, 36, 4);
        const pointCount = countView.getUint32(0, true);
        
        // 3. Read waveform floats (bytes 40 onwards)
        const waveform = new Float32Array(buffer, 40, pointCount);
        
        // 4. Update the nodes state if active tab is running tab
        if (activeTabIdRef.current === runningTabIdRef.current) {
          setNodes((nds) =>
            nds.map((node) => {
              if (node.id === nodeId) {
                const updatedData = { ...node.data };
                updatedData.results = {
                  ...node.data.results,
                  waveform: Array.from(waveform)
                };
                updatedData.resultMessage = `Captured (Binary): ${waveform.length} pts`;
                return { ...node, data: updatedData };
              }
              return node;
            })
          );
        }

        // Keep inactive tab state in tabs array updated
        setTabs((prevTabs) =>
          prevTabs.map((t) => {
            if (t.id === runningTabIdRef.current) {
              const updatedNodes = t.nodes.map((node: any) => {
                if (node.id === nodeId) {
                  const updatedData = { ...node.data };
                  updatedData.results = {
                    ...node.data.results,
                    waveform: Array.from(waveform)
                  };
                  updatedData.resultMessage = `Captured (Binary): ${waveform.length} pts`;
                  return { ...node, data: updatedData };
                }
                return node;
              });
              return { ...t, nodes: updatedNodes };
            }
            return t;
          })
        );
        return;
      }

      const msg = JSON.parse(event.data);
      
      if (msg.type === 'status') {
        // Update node running status
        if (activeTabIdRef.current === runningTabIdRef.current) {
          setNodes((nds) =>
            nds.map((node) => {
              if (node.id === msg.node_id) {
                return {
                  ...node,
                  data: {
                    ...node.data,
                    status: msg.status,
                    resultMessage: msg.message || (msg.status === 'success' ? 'Success' : ''),
                  },
                };
              }
              return node;
            })
          );
        }

        setTabs((prevTabs) =>
          prevTabs.map((t) => {
            if (t.id === runningTabIdRef.current) {
              const updatedNodes = t.nodes.map((node: any) => {
                if (node.id === msg.node_id) {
                  return {
                    ...node,
                    data: {
                      ...node.data,
                      status: msg.status,
                      resultMessage: msg.message || (msg.status === 'success' ? 'Success' : ''),
                    },
                  };
                }
                return node;
              });
              return { ...t, nodes: updatedNodes };
            }
            return t;
          })
        );
      } else if (msg.type === 'telemetry') {
        // Stream live array or scalar data
        if (activeTabIdRef.current === runningTabIdRef.current) {
          setNodes((nds) =>
            nds.map((node) => {
              if (node.id === msg.node_id) {
                const updatedData = { ...node.data };
                const oldResults = node.data.results || {};
                
                updatedData.results = {
                  ...oldResults,
                  ...msg.data
                };
                
                if (msg.data.waveform !== undefined) {
                  updatedData.resultMessage = `Captured: ${msg.data.waveform?.length || 0} pts`;
                } else if (msg.data.x !== undefined && msg.data.y !== undefined) {
                  updatedData.resultMessage = `Plotted ${msg.data.y?.length || 0} pts`;
                } else if (msg.data.value !== undefined) {
                  if (node.data.action === 'outputs/plots/plot') {
                    const val = parseFloat(msg.data.value);
                    const oldHistory = oldResults.history || [];
                    updatedData.results.history = [...oldHistory, val].slice(-50);
                    updatedData.resultMessage = `Value: ${val.toFixed(2)}`;
                  } else {
                    updatedData.results.displayValue = msg.data.value;
                    updatedData.resultMessage = `Value: ${msg.data.value}`;
                  }
                } else if (msg.data.state !== undefined) {
                  updatedData.resultMessage = `State: ${msg.data.state ? 'ON' : 'OFF'}`;
                }
                
                return { ...node, data: updatedData };
              }
              return node;
            })
          );
        }

        setTabs((prevTabs) =>
          prevTabs.map((t) => {
            if (t.id === runningTabIdRef.current) {
              const updatedNodes = t.nodes.map((node: any) => {
                if (node.id === msg.node_id) {
                  const updatedData = { ...node.data };
                  const oldResults = node.data.results || {};
                  
                  updatedData.results = {
                    ...oldResults,
                    ...msg.data
                  };
                  
                  if (msg.data.waveform !== undefined) {
                    updatedData.resultMessage = `Captured: ${msg.data.waveform?.length || 0} pts`;
                  } else if (msg.data.x !== undefined && msg.data.y !== undefined) {
                    updatedData.resultMessage = `Plotted ${msg.data.y?.length || 0} pts`;
                  } else if (msg.data.value !== undefined) {
                    if (node.data.action === 'outputs/plots/plot') {
                      const val = parseFloat(msg.data.value);
                      const historyArr = Array.isArray(oldResults.history) ? oldResults.history : [];
                      updatedData.results.history = [...historyArr, val].slice(-50);
                      updatedData.resultMessage = `Value: ${val.toFixed(2)}`;
                    } else {
                      updatedData.results.displayValue = msg.data.value;
                      updatedData.resultMessage = `Value: ${msg.data.value}`;
                    }
                  } else if (msg.data.state !== undefined) {
                    updatedData.resultMessage = `State: ${msg.data.state ? 'ON' : 'OFF'}`;
                  }
                  
                  return { ...node, data: updatedData };
                }
                return node;
              });
              return { ...t, nodes: updatedNodes };
            }
            return t;
          })
        );
      } else if (msg.type === 'pin_values') {
        if (activeTabIdRef.current === runningTabIdRef.current) {
          setNodes((nds) =>
            nds.map((node) => {
              if (node.id === msg.node_id) {
                return {
                  ...node,
                  data: {
                    ...node.data,
                    pinValues: {
                      ...(node.data.pinValues || {}),
                      ...msg.pin_values
                    }
                  }
                };
              }
              return node;
            })
          );
        }

        setTabs((prevTabs) =>
          prevTabs.map((t) => {
            if (t.id === runningTabIdRef.current) {
              const updatedNodes = t.nodes.map((node: any) => {
                if (node.id === msg.node_id) {
                  return {
                    ...node,
                    data: {
                      ...node.data,
                      pinValues: {
                        ...(node.data.pinValues || {}),
                        ...msg.pin_values
                      }
                    }
                  };
                }
                return node;
              });
              return { ...t, nodes: updatedNodes };
            }
            return t;
          })
        );
      } else if (msg.type === 'run_status') {
        if (msg.status === 'completed' || msg.status === 'failed' || msg.status === 'aborted') {
          setIsRunning(false);
          setIsPaused(false);
          setRunningTabId(null);
          if (msg.status === 'failed') {
            setErrorMessage(msg.error || 'Execution failed.');
          }

          if (msg.status === 'failed' || msg.status === 'aborted') {
            setNodes((nds) =>
              nds.map((node) => {
                if (node.data.status === 'running') {
                  return {
                    ...node,
                    data: {
                      ...node.data,
                      status: 'stopped',
                      resultMessage: 'Stopped',
                    },
                  };
                }
                return node;
              })
            );

            setTabs((prevTabs) =>
              prevTabs.map((t) => {
                if (t.id === runningTabIdRef.current) {
                  const updatedNodes = t.nodes.map((node: any) => {
                    if (node.data.status === 'running') {
                      return {
                        ...node,
                        data: {
                          ...node.data,
                          status: 'stopped',
                          resultMessage: 'Stopped',
                        },
                      };
                    }
                    return node;
                  });
                  return { ...t, nodes: updatedNodes };
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
    };
  }, [WS_BACKEND_URL, setNodes, setTabs, setIsRunning, setIsPaused, setRunningTabId, setErrorMessage]);

  const handleRun = useCallback(async () => {
    setIsRunning(true);
    setIsPaused(false);
    setErrorMessage(null);
    setRunningTabId(activeTabIdRef.current);

    // Reset status on all nodes
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        data: { ...n.data, status: 'idle', resultMessage: '' },
      }))
    );

    const rawCanvas = {
      nodes: nodesRef.current.map(({ id, type, position, data, style }) => {
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
  }, [BACKEND_URL, exportBlueprint, currentBlueprintName, setNodes, startTelemetryStream, setIsRunning, setIsPaused, setRunningTabId, setErrorMessage]);

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

      setNodes((nds) =>
        nds.map((node) => {
          if (node.data.status === 'running') {
            return {
              ...node,
              data: {
                ...node.data,
                status: 'stopped',
                resultMessage: 'Stopped',
              },
            };
          }
          return node;
        })
      );

      setTabs((prevTabs) =>
        prevTabs.map((t) => {
          if (t.id === runningTabIdRef.current) {
            const updatedNodes = t.nodes.map((node: any) => {
              if (node.data.status === 'running') {
                return {
                  ...node,
                  data: {
                    ...node.data,
                    status: 'stopped',
                    resultMessage: 'Stopped',
                  },
                };
              }
              return node;
            });
            return { ...t, nodes: updatedNodes };
          }
          return t;
        })
      );
    } catch (err) {
      console.error('Failed to abort execution:', err);
    }
  }, [BACKEND_URL, setIsRunning, setIsPaused, setRunningTabId, setNodes, setTabs]);

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
