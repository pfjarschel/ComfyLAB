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

import React, { useCallback } from 'react';

interface Point {
  x: number;
  y: number;
}

interface Annotation {
  id: string;
  type: string;
  color: string;
  strokeWidth?: number;
  width?: number;
  height?: number;
  x?: number;
  y?: number;
  cx?: number;
  cy?: number;
  r?: number;
  x1?: number;
  y1?: number;
  x2?: number;
  y2?: number;
  points?: Point[];
  style?: string;
  fill?: boolean;
  fillColor?: string;
  fillOpacity?: number;
  text?: string;
  fontSize?: number;
  startCap?: 'none' | 'arrow' | 'dot' | 'bar';
  endCap?: 'none' | 'arrow' | 'dot' | 'bar';
  arrowEnd?: boolean;
}

interface WhiteboardOverlayProps {
  showAnnotations: boolean;
  drawTool: string;
  canvasMode: 'select' | 'pan' | 'cut' | 'draw';
  viewport: { x: number; y: number; zoom: number };
  annotations: Annotation[];
  currentAnnotation: Annotation | null;
  eraserPath: Point[] | null;
  markedForDeletion: Set<string>;
  hoverPoint: Point | null;
  editingTextId: string | null;
  nodes: any[];
  edges: any[];
  pushStateToHistory: (nodes: any[], edges: any[], annotations: any[]) => void;
  setAnnotations: (annotations: Annotation[]) => void;
  setEditingTextId: (id: string | null) => void;
  onMouseDown: (e: React.MouseEvent<SVGSVGElement>) => void;
  onMouseMove: (e: React.MouseEvent<SVGSVGElement>) => void;
  onMouseUp: (e: React.MouseEvent<SVGSVGElement>) => void;
  onDoubleClick: (e: React.MouseEvent<SVGSVGElement>) => void;
  onWheel: (e: React.WheelEvent<SVGSVGElement>) => void;
}

export const WhiteboardOverlay = ({
  showAnnotations,
  drawTool,
  canvasMode,
  viewport,
  annotations,
  currentAnnotation,
  eraserPath,
  markedForDeletion,
  hoverPoint,
  editingTextId,
  nodes,
  edges,
  pushStateToHistory,
  setAnnotations,
  setEditingTextId,
  onMouseDown,
  onMouseMove,
  onMouseUp,
  onDoubleClick,
  onWheel,
}: WhiteboardOverlayProps) => {


  const renderLineCap = (
    type: 'none' | 'arrow' | 'dot' | 'bar',
    px: number,
    py: number,
    angle: number,
    color: string,
    strokeWidth: number,
    neonFilter: string | undefined,
    commonProps: any
  ) => {
    if (type === 'none') return null;

    const { key: _, className: commonClassName, ...otherCommonProps } = commonProps;

    if (type === 'arrow') {
      const d = Math.max(12, strokeWidth * 2.5);
      const arrowX1 = px - d * Math.cos(angle - Math.PI / 6);
      const arrowY1 = py - d * Math.sin(angle - Math.PI / 6);
      const arrowX2 = px - d * Math.cos(angle + Math.PI / 6);
      const arrowY2 = py - d * Math.sin(angle + Math.PI / 6);
      const pointsStr = `${px},${py} ${arrowX1},${arrowY1} ${arrowX2},${arrowY2}`;

      return (
        <polygon
          key={`arrow-${px}-${py}-${angle}`}
          points={pointsStr}
          className={`${commonClassName || 'annotation-element'} fill-element`}
          {...otherCommonProps}
          style={{
            fill: color,
            '--annotation-fill': color,
            filter: neonFilter,
          } as any}
        />
      );
    }

    if (type === 'dot') {
      const r = Math.max(6, strokeWidth * 1.5);
      return (
        <circle
          key={`dot-${px}-${py}`}
          cx={px}
          cy={py}
          r={r}
          className={`${commonClassName || 'annotation-element'} fill-element`}
          {...otherCommonProps}
          style={{
            fill: color,
            '--annotation-fill': color,
            filter: neonFilter,
          } as any}
        />
      );
    }

    if (type === 'bar') {
      const h = Math.max(8, strokeWidth * 2);
      const perpAngle = angle + Math.PI / 2;
      const x1 = px + h * Math.cos(perpAngle);
      const y1 = py + h * Math.sin(perpAngle);
      const x2 = px - h * Math.cos(perpAngle);
      const y2 = py - h * Math.sin(perpAngle);

      return (
        <line
          key={`bar-${px}-${py}`}
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          className={`${commonClassName || 'annotation-element'} stroke-element`}
          {...otherCommonProps}
          style={{
            stroke: color,
            strokeWidth: strokeWidth,
            strokeLinecap: 'round',
            filter: neonFilter,
          }}
        />
      );
    }

    return null;
  };

  const renderAnnotation = useCallback((ann: Annotation) => {
    const isEditing = editingTextId === ann.id;
    const isEraser = drawTool === 'eraser';
    const isMarked = markedForDeletion.has(ann.id);

    const commonProps = {
      className: `annotation-element ${isEraser ? 'hoverable-eraser' : ''}`,
      onMouseDown: (e: React.MouseEvent) => {
        e.stopPropagation();
      },
      onClick: (e: React.MouseEvent) => {
        if (isEraser) {
          e.stopPropagation();
          pushStateToHistory(nodes, edges, annotations);
          const nextAnnotations = annotations.filter(a => a.id !== ann.id);
          setAnnotations(nextAnnotations);
        }
      },
    };

    let strokeWidth = 4;
    if (ann.strokeWidth !== undefined) {
      strokeWidth = ann.strokeWidth;
    } else if (ann.type !== 'rectangle' && ann.width !== undefined) {
      strokeWidth = ann.width;
    }
    const isNeon = ann.style === 'neon' || ann.style === 'neon-dashed';
    const isDashed = ann.style === 'dashed' || ann.style === 'neon-dashed';

    const strokeStyle = {
      stroke: isMarked ? '#ef4444' : ann.color,
      strokeWidth: strokeWidth,
      strokeLinecap: 'round' as const,
      strokeLinejoin: 'round' as const,
      strokeDasharray: isDashed
        ? `${strokeWidth * (isNeon ? 4 : 3)} ${strokeWidth * (isNeon ? 4 : 2)}`
        : undefined,
      filter: isNeon && !isMarked
        ? `drop-shadow(0 0 ${Math.max(2, strokeWidth / 2)}px ${ann.color}) drop-shadow(0 0 ${strokeWidth}px ${ann.color})`
        : isMarked
        ? 'drop-shadow(0 0 6px #ef4444)'
        : undefined,
      opacity: isMarked ? 0.4 : undefined,
    };

    switch (ann.type) {
      case 'pen': {
        if (!ann.points || ann.points.length === 0) return null;
        const d = ann.points.map((p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ');
        return (
          <path
            key={ann.id}
            d={d}
            {...commonProps}
            className={`${commonProps.className} stroke-element`}
            style={{ ...strokeStyle }}
            fill="none"
          />
        );
      }
      case 'polygon': {
        if (!ann.points || ann.points.length === 0) return null;

        let pts = [...ann.points];
        if (ann.id === currentAnnotation?.id && hoverPoint) {
          pts.push(hoverPoint);
        }

        if (pts.length < 2) return null;

        let pointsStr = pts.map((p) => `${p.x},${p.y}`).join(' ');

        const strokePoly = (
          <polygon
            key={ann.id}
            points={pointsStr}
            {...commonProps}
            className={`${commonProps.className} stroke-element`}
            style={{
              ...strokeStyle,
              fill: 'none',
              '--annotation-fill': 'none',
            } as any}
          />
        );
        
        let polyElement = strokePoly;
        if (ann.fill) {
          const fillColorVal = isMarked ? '#ef4444' : ann.fillColor;
          const fillOpacityVal = isMarked ? 0.2 : ann.fillOpacity;
          const fillPoly = (
            <polygon
              points={pointsStr}
              style={{
                fill: fillColorVal,
                fillOpacity: fillOpacityVal,
                stroke: 'none',
                '--annotation-fill': fillColorVal,
                '--annotation-fill-opacity': fillOpacityVal,
              } as any}
              className="annotation-element fill-element"
              onMouseDown={(e) => e.stopPropagation()}
            />
          );
          polyElement = (
            <g key={ann.id}>
              {fillPoly}
              {strokePoly}
            </g>
          );
        }
        
        let previewClosingLine = null;
        if (ann.id === currentAnnotation?.id && hoverPoint && ann.points.length > 0) {
           const startPoint = ann.points[0];
           previewClosingLine = (
             <line 
                x1={hoverPoint.x} y1={hoverPoint.y} x2={startPoint.x} y2={startPoint.y}
                stroke={ann.color} strokeWidth={Math.max(1, strokeWidth / 2)} strokeDasharray="4 4" opacity={0.5}
             />
           );
        }
        
        return (
           <g key={ann.id}>
              {polyElement}
              {previewClosingLine}
           </g>
        );
      }
      case 'polyline': {
        if (!ann.points || ann.points.length === 0) return null;

        let pts = [...ann.points];
        if (ann.id === currentAnnotation?.id && hoverPoint) {
          pts.push(hoverPoint);
        }

        if (pts.length < 2) return null;

        const displayPoints = pts.map(p => ({ ...p }));
        const startAngle = Math.atan2(displayPoints[1].y - displayPoints[0].y, displayPoints[1].x - displayPoints[0].x);
        const startCap = ann.startCap || 'none';
        
        if (startCap === 'arrow') {
          const d = Math.max(12, strokeWidth * 2.5);
          displayPoints[0].x += d * 0.8 * Math.cos(startAngle);
          displayPoints[0].y += d * 0.8 * Math.sin(startAngle);
        } else if (startCap === 'dot') {
          const r = Math.max(6, strokeWidth * 1.5);
          displayPoints[0].x += r * 0.5 * Math.cos(startAngle);
          displayPoints[0].y += r * 0.5 * Math.sin(startAngle);
        }

        const n = displayPoints.length;
        const endAngle = Math.atan2(displayPoints[n-1].y - displayPoints[n-2].y, displayPoints[n-1].x - displayPoints[n-2].x);
        const endCap = ann.endCap || (ann.arrowEnd ? 'arrow' : 'none');

        if (endCap === 'arrow') {
          const d = Math.max(12, strokeWidth * 2.5);
          displayPoints[n-1].x -= d * 0.8 * Math.cos(endAngle);
          displayPoints[n-1].y -= d * 0.8 * Math.sin(endAngle);
        } else if (endCap === 'dot') {
          const r = Math.max(6, strokeWidth * 1.5);
          displayPoints[n-1].x -= r * 0.5 * Math.cos(endAngle);
          displayPoints[n-1].y -= r * 0.5 * Math.sin(endAngle);
        }

        const dAttr = displayPoints
          .map((p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`))
          .join(' ');

        const pathEl = (
          <path
            key={ann.id}
            d={dAttr}
            {...commonProps}
            className={`${commonProps.className} stroke-element`}
            style={{ ...strokeStyle }}
            fill="none"
          />
        );

        const caps: React.ReactNode[] = [];
        const startCapEl = renderLineCap(
          startCap,
          ann.points[0].x,
          ann.points[0].y,
          startAngle + Math.PI,
          isMarked ? '#ef4444' : ann.color,
          strokeWidth,
          strokeStyle.filter,
          commonProps
        );
        if (startCapEl) caps.push(startCapEl);

        const endCapEl = renderLineCap(
          endCap,
          pts[pts.length - 1].x,
          pts[pts.length - 1].y,
          endAngle,
          isMarked ? '#ef4444' : ann.color,
          strokeWidth,
          strokeStyle.filter,
          commonProps
        );
        if (endCapEl) caps.push(endCapEl);

        return (
          <g key={ann.id}>
            {pathEl}
            {caps}
          </g>
        );
      }
      case 'line': {
        const angle = Math.atan2((ann.y2 || 0) - (ann.y1 || 0), (ann.x2 || 0) - (ann.x1 || 0));
        const startCap = ann.startCap || 'none';
        const endCap = ann.endCap || (ann.arrowEnd ? 'arrow' : 'none');

        let drawX1 = ann.x1 || 0;
        let drawY1 = ann.y1 || 0;
        let drawX2 = ann.x2 || 0;
        let drawY2 = ann.y2 || 0;

        if (startCap === 'arrow') {
          const d = Math.max(12, strokeWidth * 2.5);
          drawX1 += d * 0.8 * Math.cos(angle);
          drawY1 += d * 0.8 * Math.sin(angle);
        } else if (startCap === 'dot') {
          const r = Math.max(6, strokeWidth * 1.5);
          drawX1 += r * 0.5 * Math.cos(angle);
          drawY1 += r * 0.5 * Math.sin(angle);
        }

        if (endCap === 'arrow') {
          const d = Math.max(12, strokeWidth * 2.5);
          drawX2 -= d * 0.8 * Math.cos(angle);
          drawY2 -= d * 0.8 * Math.sin(angle);
        } else if (endCap === 'dot') {
          const r = Math.max(6, strokeWidth * 1.5);
          drawX2 -= r * 0.5 * Math.cos(angle);
          drawY2 -= r * 0.5 * Math.sin(angle);
        }

        const lineEl = (
          <line
            key={ann.id}
            x1={drawX1}
            y1={drawY1}
            x2={drawX2}
            y2={drawY2}
            {...commonProps}
            className={`${commonProps.className} stroke-element`}
            style={{ ...strokeStyle }}
          />
        );

        const caps: React.ReactNode[] = [];
        const startCapEl = renderLineCap(
          startCap,
          ann.x1 || 0,
          ann.y1 || 0,
          angle + Math.PI,
          isMarked ? '#ef4444' : ann.color,
          strokeWidth,
          strokeStyle.filter,
          commonProps
        );
        if (startCapEl) caps.push(startCapEl);

        const endCapEl = renderLineCap(
          endCap,
          ann.x2 || 0,
          ann.y2 || 0,
          angle,
          isMarked ? '#ef4444' : ann.color,
          strokeWidth,
          strokeStyle.filter,
          commonProps
        );
        if (endCapEl) caps.push(endCapEl);

        return (
          <g key={ann.id}>
            {lineEl}
            {caps}
          </g>
        );
      }
      case 'rectangle': {
        const strokeRect = (
          <rect
            key={ann.id}
            x={ann.x}
            y={ann.y}
            width={ann.width}
            height={ann.height}
            rx={8}
            ry={8}
            {...commonProps}
            className={`${commonProps.className} stroke-element`}
            style={{
              ...strokeStyle,
              fill: 'none',
              '--annotation-fill': 'none',
            } as any}
          />
        );

        if (ann.fill) {
          const fillColorVal = isMarked ? '#ef4444' : ann.fillColor;
          const fillOpacityVal = isMarked ? 0.2 : ann.fillOpacity;
          const fillRect = (
            <rect
              key={ann.id}
              x={ann.x}
              y={ann.y}
              width={ann.width}
              height={ann.height}
              rx={8}
              ry={8}
              style={{
                fill: fillColorVal,
                fillOpacity: fillOpacityVal,
                stroke: 'none',
                '--annotation-fill': fillColorVal,
                '--annotation-fill-opacity': fillOpacityVal,
              } as any}
              className="annotation-element fill-element"
              onMouseDown={(e) => e.stopPropagation()}
            />
          );
          return (
            <g key={ann.id}>
              {fillRect}
              {strokeRect}
            </g>
          );
        }
        return strokeRect;
      }
      case 'circle': {
        const strokeCircle = (
          <circle
            key={ann.id}
            cx={ann.cx}
            cy={ann.cy}
            r={ann.r}
            {...commonProps}
            className={`${commonProps.className} stroke-element`}
            style={{
              ...strokeStyle,
              fill: 'none',
              '--annotation-fill': 'none',
            } as any}
          />
        );

        if (ann.fill) {
          const fillColorVal = isMarked ? '#ef4444' : ann.fillColor;
          const fillOpacityVal = isMarked ? 0.2 : ann.fillOpacity;
          const fillCircle = (
            <circle
              cx={ann.cx}
              cy={ann.cy}
              r={ann.r}
              style={{
                fill: fillColorVal,
                fillOpacity: fillOpacityVal,
                stroke: 'none',
                '--annotation-fill': fillColorVal,
                '--annotation-fill-opacity': fillOpacityVal,
              } as any}
              className="annotation-element fill-element"
              onMouseDown={(e) => e.stopPropagation()}
            />
          );
          return (
            <g key={ann.id}>
              {fillCircle}
              {strokeCircle}
            </g>
          );
        }
        return strokeCircle;
      }
      case 'text': {
        if (isEditing) {
          return (
            <foreignObject
              key={ann.id}
              x={ann.x}
              y={(ann.y || 0) - 12}
              width={250}
              height={120}
              style={{ overflow: 'visible' }}
              onMouseDown={(e) => e.stopPropagation()}
              onMouseUp={(e) => e.stopPropagation()}
              onClick={(e) => e.stopPropagation()}
            >
              <textarea
                defaultValue={ann.text === 'Text Note' ? '' : ann.text}
                placeholder="Type note..."
                ref={(el) => {
                  if (el && document.activeElement !== el) {
                    el.focus();
                    if (el.value === 'Text Note') {
                      el.select();
                    }
                  }
                }}
                onBlur={(e) => {
                  const val = e.target.value.trim() || 'Text Note';
                  setEditingTextId(null);
                  if (val === ann.text) return;
                  pushStateToHistory(nodes, edges, annotations);
                  const nextAnnotations = annotations.map(a => a.id === ann.id ? { ...a, text: val } : a);
                  setAnnotations(nextAnnotations);
                }}
                onKeyDown={(e) => {
                  e.stopPropagation();
                  if (e.key === 'Escape') {
                    e.preventDefault();
                    e.currentTarget.blur();
                  } else if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    e.currentTarget.blur();
                  }
                }}
                className="annotation-text-input"
                style={{
                  color: ann.color,
                  fontSize: `${ann.fontSize || 16}px`,
                }}
              />
            </foreignObject>
          );
        }
        const { onClick: commonOnClick, ...otherCommonProps } = commonProps;
        return (
          <text
            x={ann.x}
            y={ann.y}
            fill={isMarked ? '#ef4444' : ann.color}
            fontSize={ann.fontSize || 16}
            fontFamily="'Outfit', 'Inter', sans-serif"
            fontWeight="600"
            style={{
              cursor: isEraser ? 'cell' : (canvasMode === 'draw' ? 'pointer' : 'default'),
              userSelect: 'none',
              filter: strokeStyle.filter,
              opacity: isMarked ? 0.4 : undefined,
            }}
            onClick={(e) => {
              e.stopPropagation();
              if (isEraser) {
                if (commonOnClick) commonOnClick(e);
              } else if (canvasMode === 'draw') {
                setEditingTextId(ann.id);
              }
            }}
            {...otherCommonProps}
          >
            {(ann.text || '').split('\n').map((line, i) => (
              <tspan x={ann.x} dy={i === 0 ? 0 : '1.2em'} key={i}>
                {line}
              </tspan>
            ))}
          </text>
        );
      }
      default:
        return null;
    }
  }, [editingTextId, drawTool, canvasMode, pushStateToHistory, annotations, nodes, edges, setAnnotations, setEditingTextId, hoverPoint, markedForDeletion]);

  if (!showAnnotations) return null;

  return (
    <svg
      className={`annotations-overlay mode-${drawTool}`}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: canvasMode === 'draw' ? 'auto' : 'none',
        zIndex: canvasMode === 'draw' ? 999 : 1,
      }}
      onMouseDown={canvasMode === 'draw' ? onMouseDown : undefined}
      onMouseMove={canvasMode === 'draw' ? onMouseMove : undefined}
      onMouseUp={canvasMode === 'draw' ? onMouseUp : undefined}
      onDoubleClick={canvasMode === 'draw' ? onDoubleClick : undefined}
      onContextMenu={(e) => { if (canvasMode === 'draw') e.preventDefault(); }}
      onWheel={canvasMode === 'draw' ? onWheel : undefined}
    >
      <defs>
        <filter id="neon-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <g transform={`translate(${viewport.x}, ${viewport.y}) scale(${viewport.zoom})`}>
        {annotations.map((ann) => renderAnnotation(ann))}
        {currentAnnotation && renderAnnotation(currentAnnotation)}

        {/* Eraser path visual guide */}
        {eraserPath && eraserPath.length > 1 && (
          <path
            d={eraserPath.map((p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ')}
            fill="none"
            stroke="#ef4444"
            strokeWidth="12"
            strokeOpacity="0.3"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ pointerEvents: 'none' }}
          />
        )}
      </g>
    </svg>
  );
};
