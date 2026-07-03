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

import { useCallback, useRef } from 'react';

export interface HistorySnapshot {
  nodes: any[];
  edges: any[];
  annotations: any[];
}

export interface UseWorkspaceHistoryProps {
  nodes: any[];
  edges: any[];
  annotations: any[];
  setNodes: React.Dispatch<React.SetStateAction<any[]>>;
  setEdges: React.Dispatch<React.SetStateAction<any[]>>;
  setAnnotations: React.Dispatch<React.SetStateAction<any[]>>;
  setIsDirty: React.Dispatch<React.SetStateAction<boolean>>;
  selectedNodeIds: Set<string>;
  setSelectedNodeIds: React.Dispatch<React.SetStateAction<Set<string>>>;
  reactFlowInstance: any;
  snapToGrid: boolean;
  getBaseNodeData: (extra?: any) => any;
  pastRef: React.MutableRefObject<HistorySnapshot[]>;
  futureRef: React.MutableRefObject<HistorySnapshot[]>;
}

export function useWorkspaceHistory({
  nodes,
  edges,
  annotations,
  setNodes,
  setEdges,
  setAnnotations,
  setIsDirty,
  selectedNodeIds,
  setSelectedNodeIds,
  reactFlowInstance,
  snapToGrid,
  getBaseNodeData,
  pastRef,
  futureRef,
}: UseWorkspaceHistoryProps) {
  const clipboardRef = useRef<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] });

  const nodesRef = useRef<any[]>([]);
  const edgesRef = useRef<any[]>([]);
  const annotationsRef = useRef<any[]>([]);

  nodesRef.current = nodes;
  edgesRef.current = edges;
  annotationsRef.current = annotations;

  const pushStateToHistory = useCallback((
    currentNodes = nodesRef.current,
    currentEdges = edgesRef.current,
    currentAnnotations = annotationsRef.current
  ) => {
    const snapshot = {
      nodes: JSON.parse(JSON.stringify(currentNodes)),
      edges: JSON.parse(JSON.stringify(currentEdges)),
      annotations: JSON.parse(JSON.stringify(currentAnnotations)),
    };
    pastRef.current.push(snapshot);
    if (pastRef.current.length > 50) {
      pastRef.current.shift();
    }
    futureRef.current = []; // Clear redo stack on new action
  }, []);

  const handleUndo = useCallback(() => {
    if (pastRef.current.length === 0) return;
    const previous = pastRef.current.pop()!;
    const currentSnapshot = {
      nodes: JSON.parse(JSON.stringify(nodesRef.current)),
      edges: JSON.parse(JSON.stringify(edgesRef.current)),
      annotations: JSON.parse(JSON.stringify(annotationsRef.current)),
    };
    futureRef.current.push(currentSnapshot);

    const restoredNodes = (previous.nodes || []).map((node: any) => ({
      ...node,
      data: getBaseNodeData(node.data)
    }));
    setNodes(restoredNodes);
    setEdges(previous.edges);
    setAnnotations(previous.annotations || []);
    setIsDirty(true);
  }, [setNodes, setEdges, setAnnotations, getBaseNodeData, setIsDirty]);

  const handleRedo = useCallback(() => {
    if (futureRef.current.length === 0) return;
    const next = futureRef.current.pop()!;
    const currentSnapshot = {
      nodes: JSON.parse(JSON.stringify(nodesRef.current)),
      edges: JSON.parse(JSON.stringify(edgesRef.current)),
      annotations: JSON.parse(JSON.stringify(annotationsRef.current)),
    };
    pastRef.current.push(currentSnapshot);

    const restoredNodes = (next.nodes || []).map((node: any) => ({
      ...node,
      data: getBaseNodeData(node.data)
    }));
    setNodes(restoredNodes);
    setEdges(next.edges);
    setAnnotations(next.annotations || []);
    setIsDirty(true);
  }, [setNodes, setEdges, setAnnotations, getBaseNodeData, setIsDirty]);

  const handleCopy = useCallback(() => {
    const selectedNodes = nodesRef.current.filter(n => selectedNodeIds.has(n.id));
    const selectedEdges = edgesRef.current.filter(e => selectedNodeIds.has(e.source) && selectedNodeIds.has(e.target));
    if (selectedNodes.length === 0) return;

    clipboardRef.current = {
      nodes: JSON.parse(JSON.stringify(selectedNodes)),
      edges: JSON.parse(JSON.stringify(selectedEdges)),
    };
  }, [selectedNodeIds]);

  const handlePaste = useCallback((clientCoords?: { x: number; y: number }) => {
    const clipboard = clipboardRef.current;
    if (!clipboard || clipboard.nodes.length === 0) return;

    pushStateToHistory();
    setIsDirty(true);

    const idMap: Record<string, string> = {};
    let dx = 40;
    let dy = 40;

    if (clientCoords && reactFlowInstance) {
      const flowPos = reactFlowInstance.screenToFlowPosition(clientCoords);
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      clipboard.nodes.forEach(n => {
        if (n.position.x < minX) minX = n.position.x;
        if (n.position.y < minY) minY = n.position.y;
        if (n.position.x > maxX) maxX = n.position.x;
        if (n.position.y > maxY) maxY = n.position.y;
      });

      const groupWidth = maxX - minX;
      const groupHeight = maxY - minY;
      const centerX = minX + groupWidth / 2;
      const centerY = minY + groupHeight / 2;

      dx = flowPos.x - centerX;
      dy = flowPos.y - centerY;
    }

    const newNodes = clipboard.nodes.map(node => {
      const newId = `node_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
      idMap[node.id] = newId;
      const cleanData = JSON.parse(JSON.stringify(node.data || {}));
      let newPos = {
        x: node.position.x + dx,
        y: node.position.y + dy,
      };

      if (snapToGrid) {
        const GRID = 16;
        newPos = {
          x: Math.round(newPos.x / GRID) * GRID,
          y: Math.round(newPos.y / GRID) * GRID,
        };
      }

      return {
        ...node,
        id: newId,
        position: newPos,
        data: getBaseNodeData(cleanData),
        selected: true,
      };
    });

    const newEdges = clipboard.edges.map(edge => {
      return {
        ...edge,
        id: `edge_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
        source: idMap[edge.source],
        target: idMap[edge.target],
        selected: false,
      };
    });

    setNodes(nds => nds.map(n => ({ ...n, selected: false })).concat(newNodes));
    setEdges(eds => eds.map(e => ({ ...e, selected: false })).concat(newEdges));
    setSelectedNodeIds(new Set(newNodes.map(n => n.id)));
  }, [setNodes, setEdges, pushStateToHistory, getBaseNodeData, reactFlowInstance, snapToGrid, setSelectedNodeIds, setIsDirty]);

  const handleDuplicate = useCallback(() => {
    const selectedNodes = nodesRef.current.filter(n => selectedNodeIds.has(n.id));
    const selectedEdges = edgesRef.current.filter(e => selectedNodeIds.has(e.source) && selectedNodeIds.has(e.target));
    if (selectedNodes.length === 0) return;

    pushStateToHistory();
    setIsDirty(true);

    const idMap: Record<string, string> = {};
    const newNodes = selectedNodes.map(node => {
      const newId = `node_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
      idMap[node.id] = newId;
      const cleanData = JSON.parse(JSON.stringify(node.data || {}));
      return {
        ...node,
        id: newId,
        position: {
          x: node.position.x + 40,
          y: node.position.y + 40,
        },
        data: getBaseNodeData(cleanData),
        selected: true,
      };
    });

    const newEdges = selectedEdges.map(edge => {
      return {
        ...edge,
        id: `edge_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
        source: idMap[edge.source],
        target: idMap[edge.target],
        selected: false,
      };
    });

    setNodes(nds => nds.map(n => ({ ...n, selected: false })).concat(newNodes));
    setEdges(eds => eds.map(e => ({ ...e, selected: false })).concat(newEdges));
    setSelectedNodeIds(new Set(newNodes.map(n => n.id)));
  }, [selectedNodeIds, setNodes, setEdges, pushStateToHistory, getBaseNodeData, setSelectedNodeIds, setIsDirty]);

  const clearHistory = useCallback(() => {
    pastRef.current = [];
    futureRef.current = [];
  }, []);

  return {
    pushStateToHistory,
    handleUndo,
    handleRedo,
    handleCopy,
    handlePaste,
    handleDuplicate,
    clearHistory,
    clipboardNodesCount: clipboardRef.current.nodes.length,
  };
}
