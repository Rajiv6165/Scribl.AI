import { Point, StrokePayload } from './types';

/**
 * Renders a smooth stroke on an HTML5 2D Canvas context using quadratic midpoint curve interpolation.
 */
export function drawSmoothStroke(
  ctx: CanvasRenderingContext2D,
  payload: StrokePayload
): void {
  const { color, brushSize, isEraser, points } = payload;
  if (!points || points.length === 0) return;

  ctx.save();
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  if (isEraser) {
    ctx.globalCompositeOperation = 'destination-out';
    ctx.strokeStyle = 'rgba(0,0,0,1)';
    ctx.lineWidth = brushSize * 1.5;
  } else {
    ctx.globalCompositeOperation = 'source-over';
    ctx.strokeStyle = color;
    ctx.lineWidth = brushSize;
  }

  ctx.beginPath();

  if (points.length === 1) {
    // Single click / dot
    const p = points[0];
    ctx.arc(p.x, p.y, (ctx.lineWidth || 1) / 2, 0, Math.PI * 2);
    ctx.fillStyle = isEraser ? 'rgba(0,0,0,1)' : color;
    ctx.fill();
    ctx.restore();
    return;
  }

  if (points.length === 2) {
    // Two points straight line
    ctx.moveTo(points[0].x, points[0].y);
    ctx.lineTo(points[1].x, points[1].y);
    ctx.stroke();
    ctx.restore();
    return;
  }

  // Quadratic curve smoothing through midpoints for 3+ points
  ctx.moveTo(points[0].x, points[0].y);

  let i = 1;
  for (; i < points.length - 1; i++) {
    const midX = (points[i].x + points[i + 1].x) / 2;
    const midY = (points[i].y + points[i + 1].y) / 2;
    ctx.quadraticCurveTo(points[i].x, points[i].y, midX, midY);
  }

  // Draw final segment to last point
  ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
  ctx.stroke();
  ctx.restore();
}

/**
 * Interpolates extra points between distant sampled points to smooth out fast gestures.
 */
export function interpolatePoints(points: Point[], minDistance: number = 4): Point[] {
  if (points.length < 2) return points;

  const result: Point[] = [points[0]];

  for (let i = 1; i < points.length; i++) {
    const prev = result[result.length - 1];
    const curr = points[i];

    const dx = curr.x - prev.x;
    const dy = curr.y - prev.y;
    const dist = Math.hypot(dx, dy);

    if (dist > minDistance) {
      const steps = Math.floor(dist / minDistance);
      for (let s = 1; s <= steps; s++) {
        const factor = s / (steps + 1);
        result.push({
          x: prev.x + dx * factor,
          y: prev.y + dy * factor,
          pressure: (prev.pressure || 0.5) + ((curr.pressure || 0.5) - (prev.pressure || 0.5)) * factor,
          timestamp: prev.timestamp + (curr.timestamp - prev.timestamp) * factor,
        });
      }
    }
    result.push(curr);
  }

  return result;
}
