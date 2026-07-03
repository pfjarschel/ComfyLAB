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

import { useState, useRef, useEffect, useCallback } from 'react';

export interface Point {
  x: number;
  y: number;
}

export interface UseWhiteboardStateProps {
  reactFlowInstance: any;
  snapToGrid: boolean;
  pushStateToHistory: (currentNodes?: any[], currentEdges?: any[], currentAnnotations?: any[]) => void;
  closeContextMenu: () => void;
  nodes: any[];
  edges: any[];
  annotations: any[];
  setAnnotations: React.Dispatch<React.SetStateAction<any[]>>;
  isLocked: boolean;
  reactFlowWrapperRef: React.RefObject<HTMLDivElement | null>;
}

export function useWhiteboardState({
  reactFlowInstance,
  snapToGrid,
  pushStateToHistory,
  closeContextMenu,
  nodes,
  edges,
  annotations,
  setAnnotations,
  isLocked,
  reactFlowWrapperRef,
}: UseWhiteboardStateProps) {
  // Whiteboard settings states
  const [drawTool, setDrawTool] = useState<'pen' | 'line' | 'rectangle' | 'circle' | 'text' | 'eraser' | 'polyline' | 'polygon'>('pen');
  const [drawColor, setDrawColor] = useState('#3b82f6');
  const [drawWidth, setDrawWidth] = useState(4);
  const [drawStyle, setDrawStyle] = useState<'flat' | 'neon' | 'dashed' | 'neon-dashed'>('neon');
  const [lineStartCap, setLineStartCap] = useState<'none' | 'arrow' | 'dot' | 'bar'>('none');
  const [lineEndCap, setLineEndCap] = useState<'none' | 'arrow' | 'dot' | 'bar'>('none');
  const [drawFillEnable, setDrawFillEnable] = useState(false);
  const [drawFillColor, setDrawFillColor] = useState('#3b82f6');
  const [drawFillOpacity, setDrawFillOpacity] = useState(0.3);

  // Drawing states
  const [isDrawing, setIsDrawing] = useState(false);
  const [eraserPath, setEraserPath] = useState<Point[] | null>(null);
  const [markedForDeletion, setMarkedForDeletion] = useState<Set<string>>(new Set());
  const [hoverPoint, setHoverPoint] = useState<Point | null>(null);
  const [currentAnnotation, setCurrentAnnotation] = useState<any | null>(null);
  const [editingTextId, setEditingTextId] = useState<string | null>(null);
  const [whiteboardSidebarOpen, setWhiteboardSidebarOpen] = useState(false);

  // Sync state refs to prevent event handler closure stale state issues
  const annotationsRef = useRef<any[]>(annotations);
  const drawToolRef = useRef(drawTool);
  const drawColorRef = useRef(drawColor);
  const drawWidthRef = useRef(drawWidth);
  const drawStyleRef = useRef(drawStyle);
  const drawFillEnableRef = useRef(drawFillEnable);
  const drawFillColorRef = useRef(drawFillColor);
  const drawFillOpacityRef = useRef(drawFillOpacity);
  const snapToGridRef = useRef(snapToGrid);
  const lineStartCapRef = useRef(lineStartCap);
  const lineEndCapRef = useRef(lineEndCap);
  const currentAnnotationRef = useRef<any>(currentAnnotation);
  const isDrawingRef = useRef(isDrawing);
  const eraserPathRef = useRef(eraserPath);
  const markedForDeletionRef = useRef<Set<string>>(markedForDeletion);
  const hoverPointRef = useRef<Point | null>(hoverPoint);

  useEffect(() => { annotationsRef.current = annotations; }, [annotations]);
  useEffect(() => { drawToolRef.current = drawTool; }, [drawTool]);
  useEffect(() => { drawColorRef.current = drawColor; }, [drawColor]);
  useEffect(() => { drawWidthRef.current = drawWidth; }, [drawWidth]);
  useEffect(() => { drawStyleRef.current = drawStyle; }, [drawStyle]);
  useEffect(() => { drawFillEnableRef.current = drawFillEnable; }, [drawFillEnable]);
  useEffect(() => { drawFillColorRef.current = drawFillColor; }, [drawFillColor]);
  useEffect(() => { drawFillOpacityRef.current = drawFillOpacity; }, [drawFillOpacity]);
  useEffect(() => { snapToGridRef.current = snapToGrid; }, [snapToGrid]);
  useEffect(() => { lineStartCapRef.current = lineStartCap; }, [lineStartCap]);
  useEffect(() => { lineEndCapRef.current = lineEndCap; }, [lineEndCap]);
  useEffect(() => { currentAnnotationRef.current = currentAnnotation; }, [currentAnnotation]);
  useEffect(() => { isDrawingRef.current = isDrawing; }, [isDrawing]);
  useEffect(() => { eraserPathRef.current = eraserPath; }, [eraserPath]);
  useEffect(() => { markedForDeletionRef.current = markedForDeletion; }, [markedForDeletion]);
  useEffect(() => { hoverPointRef.current = hoverPoint; }, [hoverPoint]);

  // --- WHITEBOARD COLLISION HELPERS ---
  const ccw = useCallback((A: Point, B: Point, C: Point) => {
    return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x);
  }, []);

  const intersectSegments = useCallback((A: Point, B: Point, C: Point, D: Point) => {
    return ccw(A, C, D) !== ccw(B, C, D) && ccw(A, B, C) !== ccw(A, B, D);
  }, [ccw]);

  const distToSegment = useCallback((C: Point, A: Point, B: Point) => {
    const dx = B.x - A.x;
    const dy = B.y - A.y;
    const lenSq = dx * dx + dy * dy;
    if (lenSq === 0) return Math.hypot(C.x - A.x, C.y - A.y);
    let t = ((C.x - A.x) * dx + (C.y - A.y) * dy) / lenSq;
    t = Math.max(0, Math.min(1, t));
    const closestX = A.x + t * dx;
    const closestY = A.y + t * dy;
    return Math.hypot(C.x - closestX, C.y - closestY);
  }, []);

  const checkAnnotationIntersection = useCallback((ann: any, p1: Point, p2: Point): boolean => {
    if (ann.type === 'pen' || ann.type === 'polyline' || ann.type === 'polygon') {
      if (!ann.points || ann.points.length < 2) return false;
      for (let i = 0; i < ann.points.length - 1; i++) {
        if (intersectSegments(ann.points[i], ann.points[i + 1], p1, p2)) {
          return true;
        }
      }
      if (ann.type === 'polygon' && ann.points.length >= 3) {
        if (intersectSegments(ann.points[ann.points.length - 1], ann.points[0], p1, p2)) {
          return true;
        }
        if (ann.fill) {
          const xs = ann.points.map((p: any) => p.x);
          const ys = ann.points.map((p: any) => p.y);
          const minX = Math.min(...xs);
          const maxX = Math.max(...xs);
          const minY = Math.min(...ys);
          const maxY = Math.max(...ys);
          if (p2.x >= minX && p2.x <= maxX && p2.y >= minY && p2.y <= maxY) {
            let inside = false;
            for (let i = 0, j = ann.points.length - 1; i < ann.points.length; j = i++) {
              const xi = ann.points[i].x, yi = ann.points[i].y;
              const xj = ann.points[j].x, yj = ann.points[j].y;
              const intersect = ((yi > p2.y) !== (yj > p2.y)) && (p2.x < (xj - xi) * (p2.y - yi) / (yj - yi) + xi);
              if (intersect) inside = !inside;
            }
            if (inside) return true;
          }
        }
      }
    } else if (ann.type === 'line') {
      const a1 = { x: ann.x1, y: ann.y1 };
      const a2 = { x: ann.x2, y: ann.y2 };
      return intersectSegments(a1, a2, p1, p2);
    } else if (ann.type === 'rectangle') {
      const x = ann.x;
      const y = ann.y;
      const w = ann.width;
      const h = ann.height;
      const tl = { x, y };
      const tr = { x: x + w, y };
      const br = { x: x + w, y: y + h };
      const bl = { x, y: y + h };
      if (intersectSegments(tl, tr, p1, p2)) return true;
      if (intersectSegments(tr, br, p1, p2)) return true;
      if (intersectSegments(br, bl, p1, p2)) return true;
      if (intersectSegments(bl, tl, p1, p2)) return true;
      if (ann.fill && p2.x >= x && p2.x <= x + w && p2.y >= y && p2.y <= y + h) {
        return true;
      }
    } else if (ann.type === 'circle') {
      const dist = distToSegment({ x: ann.cx, y: ann.cy }, p1, p2);
      if (dist <= ann.r) return true;
    } else if (ann.type === 'text') {
      const fontSize = ann.fontSize || 16;
      const lines = ann.text.split('\n');
      const w = Math.max(...lines.map((l: string) => l.length)) * fontSize * 0.6;
      const h = lines.length * fontSize * 1.2;
      const x = ann.x;
      const y = ann.y - fontSize;
      const tl = { x, y };
      const tr = { x: x + w, y };
      const br = { x: x + w, y: y + h };
      const bl = { x, y: y + h };
      if (intersectSegments(tl, tr, p1, p2)) return true;
      if (intersectSegments(tr, br, p1, p2)) return true;
      if (intersectSegments(br, bl, p1, p2)) return true;
      if (intersectSegments(bl, tl, p1, p2)) return true;
      if (p2.x >= x && p2.x <= x + w && p2.y >= y && p2.y <= y + h) {
        return true;
      }
    }
    return false;
  }, [intersectSegments, distToSegment]);

  const commitActivePolyshape = useCallback(() => {
    if (!currentAnnotationRef.current || (currentAnnotationRef.current.type !== 'polyline' && currentAnnotationRef.current.type !== 'polygon')) return;

    const ann = { ...currentAnnotationRef.current };
    if (ann.points && ann.points.length >= 2) {
      // Filter out duplicate points added by double clicks
      const uniquePoints = [ann.points[0]];
      for (let i = 1; i < ann.points.length; i++) {
        const pPrev = uniquePoints[uniquePoints.length - 1];
        const pCurr = ann.points[i];
        const dist = Math.hypot(pCurr.x - pPrev.x, pCurr.y - pPrev.y);
        if (dist > 2) {
          uniquePoints.push(pCurr);
        }
      }
      ann.points = uniquePoints;

      if (ann.type === 'polygon' && ann.points.length >= 3) {
        const first = ann.points[0];
        const last = ann.points[ann.points.length - 1];
        const dist = Math.hypot(last.x - first.x, last.y - first.y);
        if (dist < 20) {
          ann.points.pop(); // Remove overlapping end point
        }
      }
    }

    if (ann.points && ((ann.type === 'polyline' && ann.points.length >= 2) || (ann.type === 'polygon' && ann.points.length >= 3))) {
      pushStateToHistory(nodes, edges, annotationsRef.current);
      const nextAnnotations = [...annotationsRef.current, ann];
      setAnnotations(nextAnnotations);
    }

    currentAnnotationRef.current = null;
    setCurrentAnnotation(null);
    setHoverPoint(null);
    hoverPointRef.current = null;
    setIsDrawing(false);
    isDrawingRef.current = false;
  }, [nodes, edges, setAnnotations, pushStateToHistory]);

  // Event handlers
  const handleSvgMouseDown = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    // Middle click always pans: forward it to the React Flow pane
    if (e.button === 1) {
      const pane = reactFlowWrapperRef.current?.querySelector('.react-flow__pane');
      if (pane) {
        const clonedEvent = new MouseEvent(e.type, e.nativeEvent);
        pane.dispatchEvent(clonedEvent);
      }
      return;
    }

    if (!reactFlowInstance || isLocked) return;

    const isRightClick = e.button === 2;
    const isLeftClick = e.button === 0;

    if (!isLeftClick && !isRightClick) return;

    // Intercept clicks if we are actively editing a text note to exit edit mode
    if (editingTextId) {
      setEditingTextId(null);
      return;
    }

    const rawFlowPos = reactFlowInstance.screenToFlowPosition({ x: e.clientX, y: e.clientY }, { snapToGrid: false });
    const shouldSnap = snapToGridRef.current && drawToolRef.current !== 'pen' && drawToolRef.current !== 'eraser' && !isRightClick;
    const flowPos = shouldSnap
      ? { x: Math.round(rawFlowPos.x / 16) * 16, y: Math.round(rawFlowPos.y / 16) * 16 }
      : rawFlowPos;

    if (isRightClick || drawToolRef.current === 'eraser') {
      e.preventDefault();
      setIsDrawing(true);
      isDrawingRef.current = true;
      setEraserPath([flowPos]);
      eraserPathRef.current = [flowPos];
      setMarkedForDeletion(new Set());
      markedForDeletionRef.current = new Set();
      return;
    }

    // Polyline drawing logic
    if (drawToolRef.current === 'polyline' || drawToolRef.current === 'polygon') {
      if (!isDrawingRef.current || !currentAnnotationRef.current) {
        setIsDrawing(true);
        isDrawingRef.current = true;
        const annotationId = `annotation_${Date.now()}`;
        const newAnn = {
          id: annotationId,
          type: drawToolRef.current,
          points: [flowPos],
          color: drawColorRef.current,
          strokeWidth: drawWidthRef.current,
          style: drawStyleRef.current,
          startCap: drawToolRef.current === 'polyline' ? lineStartCapRef.current : 'none',
          endCap: drawToolRef.current === 'polyline' ? lineEndCapRef.current : 'none',
          fill: drawToolRef.current === 'polygon' ? drawFillEnableRef.current : false,
          fillColor: drawToolRef.current === 'polygon' ? drawFillColorRef.current : 'transparent',
          fillOpacity: drawToolRef.current === 'polygon' ? drawFillOpacityRef.current : 1,
        };
        currentAnnotationRef.current = newAnn;
        setCurrentAnnotation(newAnn);
      } else {
        const updatedAnn = {
          ...currentAnnotationRef.current,
          points: [...currentAnnotationRef.current.points, flowPos],
        };
        currentAnnotationRef.current = updatedAnn;
        setCurrentAnnotation(updatedAnn);
      }
      return;
    }

    setIsDrawing(true);
    isDrawingRef.current = true;
    closeContextMenu();

    const annotationId = `annotation_${Date.now()}`;
    let newAnn: any = null;

    if (drawToolRef.current === 'pen') {
      newAnn = {
        id: annotationId,
        type: 'pen',
        points: [flowPos],
        color: drawColorRef.current,
        width: drawWidthRef.current,
        style: drawStyleRef.current,
      };
    } else if (drawToolRef.current === 'line') {
      newAnn = {
        id: annotationId,
        type: 'line',
        x1: flowPos.x,
        y1: flowPos.y,
        x2: flowPos.x,
        y2: flowPos.y,
        color: drawColorRef.current,
        width: drawWidthRef.current,
        style: drawStyleRef.current,
        startCap: lineStartCapRef.current,
        endCap: lineEndCapRef.current,
      };
    } else if (drawToolRef.current === 'rectangle') {
      newAnn = {
        id: annotationId,
        type: 'rectangle',
        startX: flowPos.x,
        startY: flowPos.y,
        x: flowPos.x,
        y: flowPos.y,
        width: 0,
        height: 0,
        color: drawColorRef.current,
        strokeWidth: drawWidthRef.current,
        style: drawStyleRef.current,
        fill: drawFillEnableRef.current,
        fillColor: drawFillColorRef.current,
        fillOpacity: drawFillOpacityRef.current,
      };
    } else if (drawToolRef.current === 'circle') {
      newAnn = {
        id: annotationId,
        type: 'circle',
        startX: flowPos.x,
        startY: flowPos.y,
        cx: flowPos.x,
        cy: flowPos.y,
        r: 0,
        color: drawColorRef.current,
        strokeWidth: drawWidthRef.current,
        style: drawStyleRef.current,
        fill: drawFillEnableRef.current,
        fillColor: drawFillColorRef.current,
        fillOpacity: drawFillOpacityRef.current,
      };
    } else if (drawToolRef.current === 'text') {
      e.preventDefault();
      newAnn = {
        id: annotationId,
        type: 'text',
        x: flowPos.x,
        y: flowPos.y,
        text: 'Text Note',
        color: drawColorRef.current,
        fontSize: 16,
        style: drawStyleRef.current,
      };
      setIsDrawing(false);
      isDrawingRef.current = false;
      pushStateToHistory(nodes, edges, annotationsRef.current);
      const nextAnnotations = [...annotationsRef.current, newAnn];
      setAnnotations(nextAnnotations);
      setEditingTextId(annotationId);
      return;
    }

    currentAnnotationRef.current = newAnn;
    setCurrentAnnotation(newAnn);
  }, [
    reactFlowInstance,
    editingTextId,
    closeContextMenu,
    pushStateToHistory,
    setAnnotations,
    setEditingTextId,
    nodes,
    edges,
    isLocked,
    reactFlowWrapperRef,
  ]);

  const handleSvgMouseMove = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDrawingRef.current || !reactFlowInstance || isLocked) return;

    const rawFlowPos = reactFlowInstance.screenToFlowPosition({ x: e.clientX, y: e.clientY }, { snapToGrid: false });
    const isErasing = eraserPathRef.current !== null;
    const shouldSnap = snapToGridRef.current && drawToolRef.current !== 'pen' && drawToolRef.current !== 'eraser' && !isErasing;
    const flowPos = shouldSnap
      ? { x: Math.round(rawFlowPos.x / 16) * 16, y: Math.round(rawFlowPos.y / 16) * 16 }
      : rawFlowPos;

    if (eraserPathRef.current) {
      const path = [...eraserPathRef.current, flowPos];
      setEraserPath(path);
      eraserPathRef.current = path;

      if (path.length >= 2) {
        const p1 = path[path.length - 2];
        const p2 = path[path.length - 1];
        const newMarked = new Set(markedForDeletionRef.current);
        let changed = false;

        annotationsRef.current.forEach((ann) => {
          if (!newMarked.has(ann.id)) {
            if (checkAnnotationIntersection(ann, p1, p2)) {
              newMarked.add(ann.id);
              changed = true;
            }
          }
        });

        if (changed) {
          setMarkedForDeletion(newMarked);
          markedForDeletionRef.current = newMarked;
        }
      }
      return;
    }

    if (!currentAnnotationRef.current) return;

    if (drawToolRef.current === 'pen') {
      const updatedAnn = {
        ...currentAnnotationRef.current,
        points: [...currentAnnotationRef.current.points, flowPos],
      };
      currentAnnotationRef.current = updatedAnn;
      setCurrentAnnotation(updatedAnn);
    } else if (drawToolRef.current === 'polyline' || drawToolRef.current === 'polygon') {
      setHoverPoint(flowPos);
      hoverPointRef.current = flowPos;
    } else if (drawToolRef.current === 'line') {
      const updatedAnn = {
        ...currentAnnotationRef.current,
        x2: flowPos.x,
        y2: flowPos.y,
      };
      currentAnnotationRef.current = updatedAnn;
      setCurrentAnnotation(updatedAnn);
    } else if (drawToolRef.current === 'rectangle') {
      const startX = currentAnnotationRef.current.startX;
      const startY = currentAnnotationRef.current.startY;
      const updatedAnn = {
        ...currentAnnotationRef.current,
        x: Math.min(startX, flowPos.x),
        y: Math.min(startY, flowPos.y),
        width: Math.abs(startX - flowPos.x),
        height: Math.abs(startY - flowPos.y),
      };
      currentAnnotationRef.current = updatedAnn;
      setCurrentAnnotation(updatedAnn);
    } else if (drawToolRef.current === 'circle') {
      const startX = currentAnnotationRef.current.startX;
      const startY = currentAnnotationRef.current.startY;
      const r = Math.sqrt(Math.pow(flowPos.x - startX, 2) + Math.pow(flowPos.y - startY, 2));
      const updatedAnn = {
        ...currentAnnotationRef.current,
        r,
      };
      currentAnnotationRef.current = updatedAnn;
      setCurrentAnnotation(updatedAnn);
    }
  }, [reactFlowInstance, setEraserPath, setMarkedForDeletion, setHoverPoint, setCurrentAnnotation, checkAnnotationIntersection, isLocked]);

  const handleSvgMouseUp = useCallback(() => {
    if (isLocked) return;

    if (eraserPathRef.current) {
      if (markedForDeletionRef.current.size > 0) {
        pushStateToHistory(nodes, edges, annotationsRef.current);
        const nextAnnotations = annotationsRef.current.filter(
          (ann) => !markedForDeletionRef.current.has(ann.id)
        );
        setAnnotations(nextAnnotations);
      }
      setEraserPath(null);
      eraserPathRef.current = null;
      setMarkedForDeletion(new Set());
      markedForDeletionRef.current = new Set();
      setIsDrawing(false);
      isDrawingRef.current = false;
      return;
    }

    if (!isDrawingRef.current) return;

    if (drawToolRef.current === 'polyline' || drawToolRef.current === 'polygon') {
      return;
    }

    setIsDrawing(false);
    isDrawingRef.current = false;

    if (currentAnnotationRef.current) {
      const cleaned = { ...currentAnnotationRef.current };
      delete cleaned.startX;
      delete cleaned.startY;

      let valid = true;
      if (cleaned.type === 'pen' && (!cleaned.points || cleaned.points.length < 2)) {
        valid = false;
      } else if (cleaned.type === 'line' && Math.abs(cleaned.x1 - cleaned.x2) < 2 && Math.abs(cleaned.y1 - cleaned.y2) < 2) {
        valid = false;
      } else if (cleaned.type === 'rectangle' && (cleaned.width < 2 || cleaned.height < 2)) {
        valid = false;
      } else if (cleaned.type === 'circle' && cleaned.r < 2) {
        valid = false;
      }

      if (valid) {
        pushStateToHistory(nodes, edges, annotationsRef.current);
        const nextAnnotations = [...annotationsRef.current, cleaned];
        setAnnotations(nextAnnotations);
      }
    }

    currentAnnotationRef.current = null;
    setCurrentAnnotation(null);
  }, [pushStateToHistory, setAnnotations, setCurrentAnnotation, nodes, edges, isLocked]);

  const handleSvgDoubleClick = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (isLocked) return;
    if (drawToolRef.current !== 'polyline' && drawToolRef.current !== 'polygon') return;
    e.stopPropagation();
    e.preventDefault();
    commitActivePolyshape();
  }, [commitActivePolyshape, isLocked]);

  const handleSvgWheel = useCallback((e: React.WheelEvent<SVGSVGElement>) => {
    const pane = reactFlowWrapperRef.current?.querySelector('.react-flow__pane');
    if (pane) {
      const clonedEvent = new WheelEvent(e.type, e.nativeEvent);
      pane.dispatchEvent(clonedEvent);
    }
  }, [reactFlowWrapperRef]);

  return {
    // Styling states
    drawTool,
    setDrawTool,
    drawColor,
    setDrawColor,
    drawWidth,
    setDrawWidth,
    drawStyle,
    setDrawStyle,
    lineStartCap,
    setLineStartCap,
    lineEndCap,
    setLineEndCap,
    drawFillEnable,
    setDrawFillEnable,
    drawFillColor,
    setDrawFillColor,
    drawFillOpacity,
    setDrawFillOpacity,

    // Drawing states
    isDrawing,
    eraserPath,
    markedForDeletion,
    hoverPoint,
    currentAnnotation,
    currentAnnotationRef,
    editingTextId,
    setEditingTextId,
    whiteboardSidebarOpen,
    setWhiteboardSidebarOpen,

    // Actions & Handlers
    commitActivePolyshape,
    handleSvgMouseDown,
    handleSvgMouseMove,
    handleSvgMouseUp,
    handleSvgDoubleClick,
    handleSvgWheel,
  };
}
