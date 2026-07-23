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
  blocks: any[];
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
  blocks,
  edges,
  annotations,
  setAnnotations,
  isLocked,
  reactFlowWrapperRef,
}: UseWhiteboardStateProps) {
  // Whiteboard settings states
  const [drawTool, setDrawTool] = useState<'select' | 'pen' | 'line' | 'rectangle' | 'circle' | 'text' | 'note' | 'eraser' | 'polyline' | 'polygon'>('pen');
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
  const [selectedAnnotationId, setSelectedAnnotationId] = useState<string | null>(null);
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
  const selectedAnnotationIdRef = useRef<string | null>(selectedAnnotationId);
  const isDraggingAnnotationRef = useRef(false);
  const dragStartPosRef = useRef<Point | null>(null);
  const dragInitialAnnRef = useRef<any | null>(null);

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

  const snapPointToAngle = useCallback((p1: Point, p2: Point): Point => {
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    const absDx = Math.abs(dx);
    const absDy = Math.abs(dy);

    if (absDx > 2 * absDy) {
      return { x: p2.x, y: p1.y };
    } else if (absDy > 2 * absDx) {
      return { x: p1.x, y: p2.y };
    } else {
      const dist = Math.max(absDx, absDy);
      return {
        x: p1.x + (dx >= 0 ? dist : -dist),
        y: p1.y + (dy >= 0 ? dist : -dist),
      };
    }
  }, []);
  useEffect(() => { currentAnnotationRef.current = currentAnnotation; }, [currentAnnotation]);
  useEffect(() => { isDrawingRef.current = isDrawing; }, [isDrawing]);
  useEffect(() => { eraserPathRef.current = eraserPath; }, [eraserPath]);
  useEffect(() => { markedForDeletionRef.current = markedForDeletion; }, [markedForDeletion]);
  useEffect(() => { hoverPointRef.current = hoverPoint; }, [hoverPoint]);
  useEffect(() => { selectedAnnotationIdRef.current = selectedAnnotationId; }, [selectedAnnotationId]);

  // --- WHITEBOARD COLLISION & SELECTION HELPERS ---
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

  const isPointInAnnotation = useCallback((p: Point, ann: any): boolean => {
    if (!ann) return false;
    if (ann.type === 'pen' || ann.type === 'polyline' || ann.type === 'polygon') {
      if (!ann.points || ann.points.length === 0) return false;
      const strokeWidth = ann.strokeWidth || ann.width || 4;
      const threshold = Math.max(16, strokeWidth / 2 + 10);
      for (let i = 0; i < ann.points.length - 1; i++) {
        if (distToSegment(p, ann.points[i], ann.points[i + 1]) <= threshold) {
          return true;
        }
      }
      if (ann.type === 'polygon' && ann.points.length >= 3) {
        if (distToSegment(p, ann.points[ann.points.length - 1], ann.points[0]) <= threshold) {
          return true;
        }
        if (ann.fill) {
          let inside = false;
          for (let i = 0, j = ann.points.length - 1; i < ann.points.length; j = i++) {
            const xi = ann.points[i].x, yi = ann.points[i].y;
            const xj = ann.points[j].x, yj = ann.points[j].y;
            const intersect = ((yi > p.y) !== (yj > p.y)) && (p.x < (xj - xi) * (p.y - yi) / (yj - yi) + xi);
            if (intersect) inside = !inside;
          }
          if (inside) return true;
        }
      }
    } else if (ann.type === 'line') {
      const strokeWidth = ann.width || 4;
      const threshold = Math.max(16, strokeWidth / 2 + 10);
      const a1 = { x: ann.x1 ?? 0, y: ann.y1 ?? 0 };
      const a2 = { x: ann.x2 ?? 0, y: ann.y2 ?? 0 };
      return distToSegment(p, a1, a2) <= threshold;
    } else if (ann.type === 'rectangle' || ann.type === 'note') {
      const x = ann.x ?? 0;
      const y = ann.y ?? 0;
      const w = ann.width ?? 0;
      const h = ann.height ?? 0;
      if (ann.fill || ann.type === 'note') {
        return p.x >= x - 4 && p.x <= x + w + 4 && p.y >= y - 4 && p.y <= y + h + 4;
      } else {
        const threshold = Math.max(12, (ann.strokeWidth || 4) / 2 + 6);
        const tl = { x, y }, tr = { x: x + w, y }, br = { x: x + w, y: y + h }, bl = { x, y: y + h };
        return distToSegment(p, tl, tr) <= threshold || distToSegment(p, tr, br) <= threshold ||
               distToSegment(p, br, bl) <= threshold || distToSegment(p, bl, tl) <= threshold;
      }
    } else if (ann.type === 'circle') {
      const cx = ann.cx ?? 0;
      const cy = ann.cy ?? 0;
      const rx = ann.rx !== undefined ? ann.rx : (ann.r ?? 0);
      const ry = ann.ry !== undefined ? ann.ry : (ann.r ?? 0);
      const dx = (p.x - cx) / (rx || 1);
      const dy = (p.y - cy) / (ry || 1);
      const normDist = Math.sqrt(dx * dx + dy * dy);
      if (ann.fill) {
        return normDist <= 1.15;
      } else {
        const strokeWidth = ann.strokeWidth || 4;
        const avgR = (rx + ry) / 2;
        const normWidth = Math.max(14, strokeWidth / 2 + 8) / (avgR || 1);
        return Math.abs(normDist - 1.0) <= normWidth;
      }
    } else if (ann.type === 'text') {
      const fontSize = ann.fontSize || 16;
      const lines = (ann.text || '').split('\n');
      const w = Math.max(...lines.map((l: string) => l.length), 1) * fontSize * 0.6;
      const h = lines.length * fontSize * 1.2;
      const x = ann.x ?? 0;
      const y = (ann.y ?? 0) - fontSize;
      return p.x >= x - 8 && p.x <= x + w + 8 && p.y >= y - 8 && p.y <= y + h + 8;
    }
    return false;
  }, [distToSegment]);

  const findAnnotationAtPoint = useCallback((p: Point, list?: any[]): any | null => {
    const targetList = list || annotationsRef.current;
    for (let i = targetList.length - 1; i >= 0; i--) {
      if (isPointInAnnotation(p, targetList[i])) {
        return targetList[i];
      }
    }
    return null;
  }, [isPointInAnnotation]);

  const deleteSelectedAnnotation = useCallback(() => {
    if (!selectedAnnotationIdRef.current) return;
    pushStateToHistory(blocks, edges, annotationsRef.current);
    const nextAnnotations = annotationsRef.current.filter((ann) => ann.id !== selectedAnnotationIdRef.current);
    setAnnotations(nextAnnotations);
    setSelectedAnnotationId(null);
    selectedAnnotationIdRef.current = null;
  }, [blocks, edges, pushStateToHistory, setAnnotations]);

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
    } else if (ann.type === 'rectangle' || ann.type === 'note') {
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
      const cx = ann.cx ?? 0;
      const cy = ann.cy ?? 0;
      const rx = ann.rx !== undefined ? ann.rx : (ann.r ?? 0);
      const ry = ann.ry !== undefined ? ann.ry : (ann.r ?? 0);
      const dist1 = Math.hypot((p1.x - cx) / (rx || 1), (p1.y - cy) / (ry || 1));
      const dist2 = Math.hypot((p2.x - cx) / (rx || 1), (p2.y - cy) / (ry || 1));
      if (dist1 <= 1.1 || dist2 <= 1.1) return true;
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
      pushStateToHistory(blocks, edges, annotationsRef.current);
      const nextAnnotations = [...annotationsRef.current, ann];
      setAnnotations(nextAnnotations);
    }

    currentAnnotationRef.current = null;
    setCurrentAnnotation(null);
    setHoverPoint(null);
    hoverPointRef.current = null;
    setIsDrawing(false);
    isDrawingRef.current = false;
  }, [blocks, edges, setAnnotations, pushStateToHistory]);

  const isResizingRef = useRef(false);
  const activeResizeHandleRef = useRef<string | null>(null);
  const resizeStartPosRef = useRef<Point | null>(null);
  const resizeInitialAnnRef = useRef<any | null>(null);

  const handleResizeStart = useCallback((handle: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!reactFlowInstance || !selectedAnnotationIdRef.current) return;
    const ann = annotationsRef.current.find(a => a.id === selectedAnnotationIdRef.current);
    if (!ann) return;

    const rawFlowPos = reactFlowInstance.screenToFlowPosition({ x: e.clientX, y: e.clientY }, { snapToGrid: false });
    isResizingRef.current = true;
    activeResizeHandleRef.current = handle;
    resizeStartPosRef.current = rawFlowPos;
    resizeInitialAnnRef.current = JSON.parse(JSON.stringify(ann));
    setIsDrawing(true);
    isDrawingRef.current = true;
  }, [reactFlowInstance]);

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
    const shouldSnap = snapToGridRef.current && drawToolRef.current !== 'pen' && drawToolRef.current !== 'eraser' && drawToolRef.current !== 'select' && !isRightClick;
    const flowPos = shouldSnap
      ? { x: Math.round(rawFlowPos.x / 16) * 16, y: Math.round(rawFlowPos.y / 16) * 16 }
      : rawFlowPos;

    if (drawToolRef.current === 'select' && !isRightClick) {
      e.preventDefault();
      const hitAnn = findAnnotationAtPoint(flowPos);
      if (hitAnn) {
        setSelectedAnnotationId(hitAnn.id);
        selectedAnnotationIdRef.current = hitAnn.id;
        isDraggingAnnotationRef.current = true;
        dragStartPosRef.current = flowPos;
        dragInitialAnnRef.current = JSON.parse(JSON.stringify(hitAnn));
        setIsDrawing(true);
        isDrawingRef.current = true;
      } else {
        setSelectedAnnotationId(null);
        selectedAnnotationIdRef.current = null;
        isDraggingAnnotationRef.current = false;
        dragStartPosRef.current = null;
        dragInitialAnnRef.current = null;
      }
      return;
    }

    if (isRightClick || drawToolRef.current === 'eraser') {
      e.preventDefault();
      if (isRightClick && (drawToolRef.current === 'polyline' || drawToolRef.current === 'polygon')) {
        commitActivePolyshape();
        return;
      }
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
      const isCtrl = e.ctrlKey || e.metaKey;
      let targetPos = flowPos;
      if (!isDrawingRef.current || !currentAnnotationRef.current) {
        setIsDrawing(true);
        isDrawingRef.current = true;
        const annotationId = `annotation_${Date.now()}`;
        const newAnn = {
          id: annotationId,
          type: drawToolRef.current,
          points: [targetPos],
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
        const pts = currentAnnotationRef.current.points || [];
        const lastP = pts[pts.length - 1];
        if (isCtrl && lastP) {
          targetPos = snapPointToAngle(lastP, flowPos);
        }
        const dist = lastP ? Math.hypot(targetPos.x - lastP.x, targetPos.y - lastP.y) : 999;
        if (dist >= 1) {
          const updatedAnn = {
            ...currentAnnotationRef.current,
            points: [...pts, targetPos],
          };
          currentAnnotationRef.current = updatedAnn;
          setCurrentAnnotation(updatedAnn);
        }
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
    } else if (drawToolRef.current === 'note') {
      // If user clicks an existing sticky note, focus and edit it!
      const hitNote = findAnnotationAtPoint(flowPos, annotationsRef.current.filter(a => a.type === 'note'));
      if (hitNote) {
        setIsDrawing(false);
        isDrawingRef.current = false;
        setEditingTextId(hitNote.id);
        return;
      }
      newAnn = {
        id: annotationId,
        type: 'note',
        startX: flowPos.x,
        startY: flowPos.y,
        x: flowPos.x,
        y: flowPos.y,
        width: 0,
        height: 0,
        text: '',
        color: drawColorRef.current,
        strokeWidth: drawWidthRef.current,
        style: drawStyleRef.current,
        fill: true,
        fillColor: drawFillEnableRef.current ? drawFillColorRef.current : 'rgba(30, 41, 59, 0.75)',
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
        rx: 0,
        ry: 0,
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
        text: 'Text Label',
        color: drawColorRef.current,
        fontSize: 16,
        style: drawStyleRef.current,
      };
      setIsDrawing(false);
      isDrawingRef.current = false;
      pushStateToHistory(blocks, edges, annotationsRef.current);
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
    blocks,
    edges,
    isLocked,
    reactFlowWrapperRef,
  ]);

  const handleSvgMouseMove = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDrawingRef.current || !reactFlowInstance || isLocked) return;

    const rawFlowPos = reactFlowInstance.screenToFlowPosition({ x: e.clientX, y: e.clientY }, { snapToGrid: false });
    const isErasing = eraserPathRef.current !== null;
    const shouldSnap = snapToGridRef.current && drawToolRef.current !== 'pen' && drawToolRef.current !== 'eraser' && drawToolRef.current !== 'select' && !isErasing;
    const flowPos = shouldSnap
      ? { x: Math.round(rawFlowPos.x / 16) * 16, y: Math.round(rawFlowPos.y / 16) * 16 }
      : rawFlowPos;

    const isCtrl = e.ctrlKey || e.metaKey;

    if (isResizingRef.current && resizeStartPosRef.current && resizeInitialAnnRef.current && activeResizeHandleRef.current) {
      const dx = flowPos.x - resizeStartPosRef.current.x;
      const dy = flowPos.y - resizeStartPosRef.current.y;
      const init = resizeInitialAnnRef.current;
      const handle = activeResizeHandleRef.current;
      const updated = { ...init };

      if (init.type === 'rectangle' || init.type === 'note') {
        let x = init.x ?? 0;
        let y = init.y ?? 0;
        let w = init.width ?? 100;
        let h = init.height ?? 80;

        if (handle.includes('e')) w = Math.max(40, init.width + dx);
        if (handle.includes('s')) h = Math.max(30, init.height + dy);
        if (handle.includes('w')) {
          const newW = Math.max(40, init.width - dx);
          x = init.x + (init.width - newW);
          w = newW;
        }
        if (handle.includes('n')) {
          const newH = Math.max(30, init.height - dy);
          y = init.y + (init.height - newH);
          h = newH;
        }

        if (isCtrl) {
          const aspect = (init.width || 1) / (init.height || 1);
          const origBottom = (init.y ?? 0) + (init.height ?? 80);
          h = Math.max(30, w / aspect);
          if (handle.includes('n')) {
            y = origBottom - h;
          }
        }

        updated.x = x;
        updated.y = y;
        updated.width = w;
        updated.height = h;
      } else if (init.type === 'circle') {
        const initCx = init.cx ?? 0;
        const initCy = init.cy ?? 0;
        const initRx = init.rx !== undefined ? init.rx : (init.r ?? 20);
        const initRy = init.ry !== undefined ? init.ry : (init.r ?? 20);

        let minX = initCx - initRx;
        let maxX = initCx + initRx;
        let minY = initCy - initRy;
        let maxY = initCy + initRy;

        if (handle.includes('e')) maxX = Math.max(minX + 10, initCx + initRx + dx);
        if (handle.includes('s')) maxY = Math.max(minY + 10, initCy + initRy + dy);
        if (handle.includes('w')) minX = Math.min(maxX - 10, initCx - initRx + dx);
        if (handle.includes('n')) minY = Math.min(maxY - 10, initCy - initRy + dy);

        let w = maxX - minX;
        let h = maxY - minY;

        if (isCtrl && initRx > 0 && initRy > 0) {
          const aspect = initRx / initRy;
          h = Math.max(10, w / aspect);
          if (handle.includes('n')) {
            minY = (initCy + initRy) - h;
          } else {
            maxY = minY + h;
          }
        }

        const rx = w / 2;
        const ry = h / 2;
        const cx = minX + rx;
        const cy = minY + ry;

        updated.cx = cx;
        updated.cy = cy;
        updated.rx = rx;
        updated.ry = ry;
        updated.r = Math.max(rx, ry);
      } else if (init.type === 'line') {
        if (handle === 'p1') {
          const rawP = { x: init.x1 + dx, y: init.y1 + dy };
          const p = isCtrl ? snapPointToAngle({ x: init.x2, y: init.y2 }, rawP) : rawP;
          updated.x1 = p.x;
          updated.y1 = p.y;
        } else if (handle === 'p2') {
          const rawP = { x: init.x2 + dx, y: init.y2 + dy };
          const p = isCtrl ? snapPointToAngle({ x: init.x1, y: init.y1 }, rawP) : rawP;
          updated.x2 = p.x;
          updated.y2 = p.y;
        }
      } else if (init.type === 'pen' || init.type === 'polyline' || init.type === 'polygon') {
        if (init.points && init.points.length > 0) {
          const xs = init.points.map((p: Point) => p.x);
          const ys = init.points.map((p: Point) => p.y);
          const origMinX = Math.min(...xs);
          const origMinY = Math.min(...ys);
          const origMaxX = Math.max(...xs);
          const origMaxY = Math.max(...ys);
          const origW = Math.max(origMaxX - origMinX, 1);
          const origH = Math.max(origMaxY - origMinY, 1);

          let newMinX = origMinX;
          let newMinY = origMinY;
          let newW = origW;
          let newH = origH;

          if (handle.includes('e')) newW = Math.max(10, origW + dx);
          if (handle.includes('s')) newH = Math.max(10, origH + dy);
          if (handle.includes('w')) {
            newW = Math.max(10, origW - dx);
            newMinX = origMinX + (origW - newW);
          }
          if (handle.includes('n')) {
            newH = Math.max(10, origH - dy);
            newMinY = origMinY + (origH - newH);
          }

          if (isCtrl) {
            const aspect = origW / origH;
            newH = Math.max(10, newW / aspect);
            if (handle.includes('n')) {
              newMinY = origMaxY - newH;
            }
          }

          const scaleX = newW / origW;
          const scaleY = newH / origH;

          updated.points = init.points.map((p: Point) => ({
            x: newMinX + (p.x - origMinX) * scaleX,
            y: newMinY + (p.y - origMinY) * scaleY,
          }));
        }
      } else if (init.type === 'text') {
        const initFS = init.fontSize || 16;
        const scale = 1 + (dx + dy) / 200;
        updated.fontSize = Math.max(10, Math.min(120, Math.round(initFS * scale)));
      }

      const nextAnnotations = annotationsRef.current.map((ann) => (ann.id === updated.id ? updated : ann));
      setAnnotations(nextAnnotations);
      return;
    }

    if (drawToolRef.current === 'select') {
      if (isDraggingAnnotationRef.current && dragStartPosRef.current && dragInitialAnnRef.current) {
        const dx = flowPos.x - dragStartPosRef.current.x;
        const dy = flowPos.y - dragStartPosRef.current.y;
        const init = dragInitialAnnRef.current;
        const updated = { ...init };

        if (init.type === 'pen' || init.type === 'polyline' || init.type === 'polygon') {
          if (init.points) {
            updated.points = init.points.map((p: Point) => ({ x: p.x + dx, y: p.y + dy }));
          }
        } else if (init.type === 'line') {
          updated.x1 = (init.x1 ?? 0) + dx;
          updated.y1 = (init.y1 ?? 0) + dy;
          updated.x2 = (init.x2 ?? 0) + dx;
          updated.y2 = (init.y2 ?? 0) + dy;
        } else if (init.type === 'rectangle' || init.type === 'text' || init.type === 'note') {
          updated.x = (init.x ?? 0) + dx;
          updated.y = (init.y ?? 0) + dy;
        } else if (init.type === 'circle') {
          updated.cx = (init.cx ?? 0) + dx;
          updated.cy = (init.cy ?? 0) + dy;
        }

        const nextAnnotations = annotationsRef.current.map((ann) => (ann.id === updated.id ? updated : ann));
        setAnnotations(nextAnnotations);
      }
      return;
    }

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
          if (!markedForDeletionRef.current.has(ann.id)) {
            if (checkAnnotationIntersection(ann, p1, p2)) {
              newMarked.add(ann.id);
              changed = true;
            }
          }
        });

        if (changed) {
          setMarkedForDeletion(markedForDeletionRef.current);
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
      const pts = currentAnnotationRef.current?.points || [];
      const lastP = pts[pts.length - 1];
      const targetPos = isCtrl && lastP ? snapPointToAngle(lastP, flowPos) : flowPos;
      setHoverPoint(targetPos);
      hoverPointRef.current = targetPos;
    } else if (drawToolRef.current === 'line') {
      const startX = currentAnnotationRef.current.x1;
      const startY = currentAnnotationRef.current.y1;
      const targetPos = isCtrl ? snapPointToAngle({ x: startX, y: startY }, flowPos) : flowPos;
      const updatedAnn = {
        ...currentAnnotationRef.current,
        x2: targetPos.x,
        y2: targetPos.y,
      };
      currentAnnotationRef.current = updatedAnn;
      setCurrentAnnotation(updatedAnn);
    } else if (drawToolRef.current === 'rectangle' || drawToolRef.current === 'note') {
      const startX = currentAnnotationRef.current.startX;
      const startY = currentAnnotationRef.current.startY;
      let w = Math.abs(startX - flowPos.x);
      let h = Math.abs(startY - flowPos.y);

      if (isCtrl) {
        const side = Math.max(w, h);
        w = side;
        h = side;
      }

      const updatedAnn = {
        ...currentAnnotationRef.current,
        x: flowPos.x >= startX ? startX : startX - w,
        y: flowPos.y >= startY ? startY : startY - h,
        width: w,
        height: h,
      };
      currentAnnotationRef.current = updatedAnn;
      setCurrentAnnotation(updatedAnn);
    } else if (drawToolRef.current === 'circle') {
      const startX = currentAnnotationRef.current.startX;
      const startY = currentAnnotationRef.current.startY;
      let rx = Math.abs(flowPos.x - startX) / 2;
      let ry = Math.abs(flowPos.y - startY) / 2;

      if (isCtrl) {
        const r = Math.max(rx, ry);
        rx = r;
        ry = r;
      }

      const cx = (flowPos.x >= startX ? startX : startX - rx * 2) + rx;
      const cy = (flowPos.y >= startY ? startY : startY - ry * 2) + ry;

      const updatedAnn = {
        ...currentAnnotationRef.current,
        cx,
        cy,
        rx,
        ry,
        r: Math.max(rx, ry),
      };
      currentAnnotationRef.current = updatedAnn;
      setCurrentAnnotation(updatedAnn);
    }
  }, [reactFlowInstance, setEraserPath, setMarkedForDeletion, setHoverPoint, setCurrentAnnotation, checkAnnotationIntersection, isLocked, setAnnotations]);

  const handleSvgMouseUp = useCallback(() => {
    if (isLocked) return;

    if (isResizingRef.current) {
      if (resizeInitialAnnRef.current) {
        pushStateToHistory(blocks, edges, annotationsRef.current.map(a => a.id === resizeInitialAnnRef.current.id ? resizeInitialAnnRef.current : a));
      }
      isResizingRef.current = false;
      activeResizeHandleRef.current = null;
      resizeStartPosRef.current = null;
      resizeInitialAnnRef.current = null;
      setIsDrawing(false);
      isDrawingRef.current = false;
      return;
    }

    if (drawToolRef.current === 'select') {
      if (isDraggingAnnotationRef.current && dragStartPosRef.current && dragInitialAnnRef.current) {
        const init = dragInitialAnnRef.current;
        const currentAnn = annotationsRef.current.find(a => a.id === init.id);
        if (currentAnn) {
          pushStateToHistory(blocks, edges, annotationsRef.current.map(a => a.id === init.id ? init : a));
        }
      }
      isDraggingAnnotationRef.current = false;
      dragStartPosRef.current = null;
      dragInitialAnnRef.current = null;
      setIsDrawing(false);
      isDrawingRef.current = false;
      return;
    }

    if (eraserPathRef.current) {
      if (markedForDeletionRef.current.size > 0) {
        pushStateToHistory(blocks, edges, annotationsRef.current);
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
      } else if (cleaned.type === 'circle' && ((cleaned.rx || 0) < 2 && (cleaned.ry || 0) < 2 && (cleaned.r || 0) < 2)) {
        valid = false;
      } else if (cleaned.type === 'note') {
        if (cleaned.width < 10 || cleaned.height < 10) {
          cleaned.width = 180;
          cleaned.height = 140;
        }
      }

      if (valid) {
        pushStateToHistory(blocks, edges, annotationsRef.current);
        const nextAnnotations = [...annotationsRef.current, cleaned];
        setAnnotations(nextAnnotations);
        if (cleaned.type === 'note') {
          setEditingTextId(cleaned.id);
        }
      }
    }

    currentAnnotationRef.current = null;
    setCurrentAnnotation(null);
  }, [pushStateToHistory, setAnnotations, setCurrentAnnotation, setEditingTextId, blocks, edges, isLocked]);

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
    selectedAnnotationId,
    setSelectedAnnotationId,
    whiteboardSidebarOpen,
    setWhiteboardSidebarOpen,

    // Actions & Handlers
    commitActivePolyshape,
    deleteSelectedAnnotation,
    handleResizeStart,
    handleSvgMouseDown,
    handleSvgMouseMove,
    handleSvgMouseUp,
    handleSvgDoubleClick,
    handleSvgWheel,
  };
}
