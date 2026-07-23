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
  blocks: any[];
  edges: any[];
  annotations: any[];
}

export interface UseWorkspaceHistoryProps {
  blocks: any[];
  edges: any[];
  annotations: any[];
  setBlocks: React.Dispatch<React.SetStateAction<any[]>>;
  setEdges: React.Dispatch<React.SetStateAction<any[]>>;
  setAnnotations: React.Dispatch<React.SetStateAction<any[]>>;
  setIsDirty: React.Dispatch<React.SetStateAction<boolean>>;
  selectedBlockIds: Set<string>;
  setSelectedBlockIds: React.Dispatch<React.SetStateAction<Set<string>>>;
  reactFlowInstance: any;
  snapToGrid: boolean;
  getBaseBlockData: (extra?: any) => any;
  pastRef: React.MutableRefObject<HistorySnapshot[]>;
  futureRef: React.MutableRefObject<HistorySnapshot[]>;
}

export function useWorkspaceHistory({
  blocks,
  edges,
  annotations,
  setBlocks,
  setEdges,
  setAnnotations,
  setIsDirty,
  selectedBlockIds,
  setSelectedBlockIds,
  reactFlowInstance,
  snapToGrid,
  getBaseBlockData,
  pastRef,
  futureRef,
}: UseWorkspaceHistoryProps) {
  const clipboardRef = useRef<{ blocks: any[]; edges: any[] }>({ blocks: [], edges: [] });

  const blocksRef = useRef<any[]>([]);
  const edgesRef = useRef<any[]>([]);
  const annotationsRef = useRef<any[]>([]);

  blocksRef.current = blocks;
  edgesRef.current = edges;
  annotationsRef.current = annotations;

  const pushStateToHistory = useCallback((
    currentNodes = blocksRef.current,
    currentEdges = edgesRef.current,
    currentAnnotations = annotationsRef.current
  ) => {
    const snapshot = {
      blocks: JSON.parse(JSON.stringify(currentNodes)),
      edges: JSON.parse(JSON.stringify(currentEdges)),
      annotations: JSON.parse(JSON.stringify(currentAnnotations)),
    };
    pastRef.current.push(snapshot);
    if (pastRef.current.length > 50) {
      pastRef.current.shift();
    }
    futureRef.current = []; // Clear redo stack on new action
    setIsDirty(true);
  }, [setIsDirty]);

  const handleUndo = useCallback(() => {
    if (pastRef.current.length === 0) return;
    const previous = pastRef.current.pop()!;
    const currentSnapshot = {
      blocks: JSON.parse(JSON.stringify(blocksRef.current)),
      edges: JSON.parse(JSON.stringify(edgesRef.current)),
      annotations: JSON.parse(JSON.stringify(annotationsRef.current)),
    };
    futureRef.current.push(currentSnapshot);

    const restoredNodes = (previous.blocks || []).map((block: any) => ({
      ...block,
      data: getBaseBlockData(block.data)
    }));
    setBlocks(restoredNodes);
    setEdges(previous.edges);
    setAnnotations(previous.annotations || []);
    setIsDirty(true);
  }, [setBlocks, setEdges, setAnnotations, getBaseBlockData, setIsDirty]);

  const handleRedo = useCallback(() => {
    if (futureRef.current.length === 0) return;
    const next = futureRef.current.pop()!;
    const currentSnapshot = {
      blocks: JSON.parse(JSON.stringify(blocksRef.current)),
      edges: JSON.parse(JSON.stringify(edgesRef.current)),
      annotations: JSON.parse(JSON.stringify(annotationsRef.current)),
    };
    pastRef.current.push(currentSnapshot);

    const restoredNodes = (next.blocks || []).map((block: any) => ({
      ...block,
      data: getBaseBlockData(block.data)
    }));
    setBlocks(restoredNodes);
    setEdges(next.edges);
    setAnnotations(next.annotations || []);
    setIsDirty(true);
  }, [setBlocks, setEdges, setAnnotations, getBaseBlockData, setIsDirty]);

  const handleCopy = useCallback(() => {
    const selectedNodes = blocksRef.current.filter(n => selectedBlockIds.has(n.id));
    const selectedEdges = edgesRef.current.filter(e => selectedBlockIds.has(e.source) && selectedBlockIds.has(e.target));
    if (selectedNodes.length === 0) return;

    clipboardRef.current = {
      blocks: JSON.parse(JSON.stringify(selectedNodes)),
      edges: JSON.parse(JSON.stringify(selectedEdges)),
    };
  }, [selectedBlockIds]);

  const handlePaste = useCallback((clientCoords?: { x: number; y: number }) => {
    const clipboard = clipboardRef.current;
    if (!clipboard || clipboard.blocks.length === 0) return;

    pushStateToHistory();
    setIsDirty(true);

    const idMap: Record<string, string> = {};
    let dx = 40;
    let dy = 40;

    if (clientCoords && reactFlowInstance) {
      const flowPos = reactFlowInstance.screenToFlowPosition(clientCoords);
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      clipboard.blocks.forEach(n => {
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

    const newBlocks = clipboard.blocks.map(block => {
      const newId = `block_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
      idMap[block.id] = newId;
      const cleanData = JSON.parse(JSON.stringify(block.data || {}));
      let newPos = {
        x: block.position.x + dx,
        y: block.position.y + dy,
      };

      if (snapToGrid) {
        const GRID = 16;
        newPos = {
          x: Math.round(newPos.x / GRID) * GRID,
          y: Math.round(newPos.y / GRID) * GRID,
        };
      }

      return {
        ...block,
        id: newId,
        position: newPos,
        data: getBaseBlockData(cleanData),
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

    setBlocks(nds => nds.map(n => ({ ...n, selected: false })).concat(newBlocks));
    setEdges(eds => eds.map(e => ({ ...e, selected: false })).concat(newEdges));
    setSelectedBlockIds(new Set(newBlocks.map(n => n.id)));
  }, [setBlocks, setEdges, pushStateToHistory, getBaseBlockData, reactFlowInstance, snapToGrid, setSelectedBlockIds, setIsDirty]);

  const handleDuplicate = useCallback(() => {
    const selectedNodes = blocksRef.current.filter(n => selectedBlockIds.has(n.id));
    const selectedEdges = edgesRef.current.filter(e => selectedBlockIds.has(e.source) && selectedBlockIds.has(e.target));
    if (selectedNodes.length === 0) return;

    pushStateToHistory();
    setIsDirty(true);

    const idMap: Record<string, string> = {};
    const newBlocks = selectedNodes.map(block => {
      const newId = `block_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
      idMap[block.id] = newId;
      const cleanData = JSON.parse(JSON.stringify(block.data || {}));
      return {
        ...block,
        id: newId,
        position: {
          x: block.position.x + 40,
          y: block.position.y + 40,
        },
        data: getBaseBlockData(cleanData),
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

    setBlocks(nds => nds.map(n => ({ ...n, selected: false })).concat(newBlocks));
    setEdges(eds => eds.map(e => ({ ...e, selected: false })).concat(newEdges));
    setSelectedBlockIds(new Set(newBlocks.map(n => n.id)));
  }, [selectedBlockIds, setBlocks, setEdges, pushStateToHistory, getBaseBlockData, setSelectedBlockIds, setIsDirty]);

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
    clipboardBlocksCount: clipboardRef.current.blocks.length,
  };
}
