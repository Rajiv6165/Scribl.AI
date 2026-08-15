'use client';

import React, { useRef, useEffect, useState, useCallback, useImperativeHandle, forwardRef } from 'react';
import { Point, StrokePayload, StrokeEventData } from '../utils/types';
import { drawSmoothStroke, interpolatePoints } from '../utils/strokeSmoothing';

export interface CanvasRef {
  clearCanvasLocal: () => void;
  undoLocal: () => void;
  drawRemoteStroke: (payload: StrokePayload) => void;
  syncHistory: (history: StrokeEventData[]) => void;
}

interface CanvasProps {
  color: string;
  brushSize: number;
  isEraser: boolean;
  isReadOnly?: boolean;
  onStrokeComplete: (payload: StrokePayload) => void;
}

export const Canvas = forwardRef<CanvasRef, CanvasProps>(({
  color,
  brushSize,
  isEraser,
  isReadOnly = false,
  onStrokeComplete,
}, ref) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [isDrawing, setIsDrawing] = useState(false);
  const currentPointsRef = useRef<Point[]>([]);
  const strokeHistoryRef = useRef<StrokePayload[]>([]);

  // Redraw the entire stroke history onto the canvas
  const redrawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Fill white background for clean drawing & crisp contrast
    ctx.save();
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.restore();

    strokeHistoryRef.current.forEach((stroke) => {
      drawSmoothStroke(ctx, stroke);
    });
  }, []);

  // Handle window resize with Retina / Device Pixel Ratio scaling
  const handleResize = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.scale(dpr, dpr);
    }

    redrawCanvas();
  }, [redrawCanvas]);

  useEffect(() => {
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [handleResize]);

  // Imperative handle for parent / WebSocket commands
  useImperativeHandle(ref, () => ({
    clearCanvasLocal: () => {
      strokeHistoryRef.current = [];
      redrawCanvas();
    },
    undoLocal: () => {
      strokeHistoryRef.current.pop();
      redrawCanvas();
    },
    drawRemoteStroke: (payload: StrokePayload) => {
      strokeHistoryRef.current.push(payload);
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        drawSmoothStroke(ctx, payload);
      }
    },
    syncHistory: (history: StrokeEventData[]) => {
      const strokes: StrokePayload[] = [];
      history.forEach((event) => {
        if (event.action_type === 'stroke' && event.payload && event.payload.points) {
          strokes.push(event.payload);
        } else if (event.action_type === 'clear') {
          strokes.length = 0;
        } else if (event.action_type === 'undo') {
          strokes.pop();
        }
      });
      strokeHistoryRef.current = strokes;
      redrawCanvas();
    },
  }));

  const getCanvasCoordinates = (e: React.PointerEvent<HTMLCanvasElement>): Point | null => {
    const canvas = canvasRef.current;
    if (!canvas) return null;

    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      pressure: e.pressure > 0 ? e.pressure : 0.5,
      timestamp: Date.now(),
    };
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (isReadOnly) return;
    canvasRef.current?.setPointerCapture(e.pointerId);
    setIsDrawing(true);

    const pt = getCanvasCoordinates(e);
    if (!pt) return;

    currentPointsRef.current = [pt];

    // Live preview initial point
    const ctx = canvasRef.current?.getContext('2d');
    if (ctx) {
      drawSmoothStroke(ctx, {
        color,
        brushSize,
        isEraser,
        points: [pt],
      });
    }
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (isReadOnly || !isDrawing) return;

    const pt = getCanvasCoordinates(e);
    if (!pt) return;

    currentPointsRef.current.push(pt);

    // Live smooth feedback while dragging
    const ctx = canvasRef.current?.getContext('2d');
    if (ctx && currentPointsRef.current.length >= 2) {
      const smoothed = interpolatePoints(currentPointsRef.current);
      drawSmoothStroke(ctx, {
        color,
        brushSize,
        isEraser,
        points: smoothed.slice(-3),
      });
    }
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    setIsDrawing(false);
    canvasRef.current?.releasePointerCapture(e.pointerId);

    if (currentPointsRef.current.length === 0) return;

    const finalPoints = interpolatePoints(currentPointsRef.current);
    const strokePayload: StrokePayload = {
      color,
      brushSize,
      isEraser,
      points: finalPoints,
    };

    strokeHistoryRef.current.push(strokePayload);
    redrawCanvas();
    onStrokeComplete(strokePayload);

    currentPointsRef.current = [];
  };

  return (
    <div ref={containerRef} className="relative w-full h-full min-h-[450px] bg-white rounded-2xl overflow-hidden shadow-2xl border border-slate-700/50">
      {isReadOnly && (
        <div className="absolute top-3 left-3 z-10 bg-slate-900/80 backdrop-blur-md px-3 py-1 rounded-lg border border-indigo-500/30 text-indigo-300 font-semibold text-xs flex items-center gap-1.5 shadow-md pointer-events-none">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span>Live Spectator Canvas</span>
        </div>
      )}
      <canvas
        ref={canvasRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        className={`w-full h-full touch-none block ${isReadOnly ? 'cursor-default' : 'cursor-crosshair'}`}
      />
    </div>
  );
});

Canvas.displayName = 'Canvas';
