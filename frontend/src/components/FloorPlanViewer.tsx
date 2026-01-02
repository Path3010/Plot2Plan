'use client';

import { useRef, useEffect } from 'react';

interface Hole {
  id: number;
  coordinates: [number, number][];
  area_sqm: number;
}

interface Room {
  id: string;
  type: string;
  zone: 'public' | 'private' | 'service';
  polygon: [number, number][];
  area_sqm: number;
}

interface FloorPlanViewerProps {
  boundary: [number, number][];
  boundaryUnclosed?: [number, number][];  // Original unclosed boundary for accurate display
  isOriginallyClosed?: boolean;  // Was boundary closed in DXF?
  holes?: Hole[];
  rooms: Room[];
  staircase?: { polygon: [number, number][] };
  width: number;
  height: number;
}

const ZONE_COLORS = {
  public: { fill: '#3b82f6', stroke: '#2563eb', label: 'Public' },
  private: { fill: '#8b5cf6', stroke: '#7c3aed', label: 'Private' },
  service: { fill: '#f59e0b', stroke: '#d97706', label: 'Service' },
};

export default function FloorPlanViewer({ boundary, boundaryUnclosed, isOriginallyClosed = true, holes, rooms, staircase, width, height }: FloorPlanViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, width, height);

    // Draw grid
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 0.5;
    const gridSize = 20;
    for (let x = 0; x <= width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y <= height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    if (boundary.length < 3) return;

    // Calculate bounds (include holes in calculation)
    let allPoints = [...boundary];
    if (holes) {
      holes.forEach(hole => {
        allPoints = allPoints.concat(hole.coordinates);
      });
    }

    const xs = allPoints.map(p => p[0]);
    const ys = allPoints.map(p => p[1]);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    const padding = 60;
    const scaleX = (width - padding * 2) / (maxX - minX);
    const scaleY = (height - padding * 2) / (maxY - minY);
    const scale = Math.min(scaleX, scaleY);

    const offsetX = (width - (maxX - minX) * scale) / 2;
    const offsetY = (height - (maxY - minY) * scale) / 2;

    const transform = (p: [number, number]): [number, number] => [
      (p[0] - minX) * scale + offsetX,
      height - ((p[1] - minY) * scale + offsetY),
    ];

    // Draw outer boundary fill
    ctx.beginPath();
    const startPoint = transform(boundary[0]);
    ctx.moveTo(startPoint[0], startPoint[1]);
    for (let i = 1; i < boundary.length; i++) {
      const point = transform(boundary[i]);
      ctx.lineTo(point[0], point[1]);
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(229, 231, 235, 0.5)';
    ctx.fill();

    // Draw holes (cut out from boundary) - fill with white/background color
    if (holes && holes.length > 0) {
      holes.forEach((hole) => {
        if (hole.coordinates.length < 3) return;

        ctx.beginPath();
        const holeStart = transform(hole.coordinates[0]);
        ctx.moveTo(holeStart[0], holeStart[1]);
        for (let i = 1; i < hole.coordinates.length; i++) {
          const point = transform(hole.coordinates[i]);
          ctx.lineTo(point[0], point[1]);
        }
        ctx.closePath();

        // Fill hole with background color to "cut out"
        ctx.fillStyle = '#f8fafc';
        ctx.fill();

        // Draw hole outline with dashed red line
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 2;
        ctx.setLineDash([6, 4]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Label the hole
        const centerX = hole.coordinates.reduce((sum, p) => sum + p[0], 0) / hole.coordinates.length;
        const centerY = hole.coordinates.reduce((sum, p) => sum + p[1], 0) / hole.coordinates.length;
        const [labelX, labelY] = transform([centerX, centerY]);

        ctx.fillStyle = '#ef4444';
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('Courtyard', labelX, labelY - 8);

        ctx.font = '10px Inter, sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText(`${hole.area_sqm.toFixed(1)} m²`, labelX, labelY + 8);
      });
    }

    // Draw rooms
    rooms.forEach((room) => {
      if (!room.polygon || room.polygon.length < 3) return;

      const colors = ZONE_COLORS[room.zone] || ZONE_COLORS.public;

      ctx.beginPath();
      const rStart = transform(room.polygon[0]);
      ctx.moveTo(rStart[0], rStart[1]);
      for (let i = 1; i < room.polygon.length; i++) {
        const point = transform(room.polygon[i]);
        ctx.lineTo(point[0], point[1]);
      }
      ctx.closePath();

      // Fill with transparency
      ctx.fillStyle = colors.fill + '40';
      ctx.fill();
      ctx.strokeStyle = colors.stroke;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Room label
      const centerX = room.polygon.reduce((sum, p) => sum + p[0], 0) / room.polygon.length;
      const centerY = room.polygon.reduce((sum, p) => sum + p[1], 0) / room.polygon.length;
      const [labelX, labelY] = transform([centerX, centerY]);

      ctx.fillStyle = '#1e293b';
      ctx.font = 'bold 11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(room.type.replace('_', ' '), labelX, labelY - 6);

      ctx.font = '10px Inter, sans-serif';
      ctx.fillStyle = '#64748b';
      ctx.fillText(`${room.area_sqm.toFixed(1)} m²`, labelX, labelY + 8);
    });

    // Draw staircase
    if (staircase && staircase.polygon && staircase.polygon.length >= 3) {
      ctx.beginPath();
      const sStart = transform(staircase.polygon[0]);
      ctx.moveTo(sStart[0], sStart[1]);
      for (let i = 1; i < staircase.polygon.length; i++) {
        const point = transform(staircase.polygon[i]);
        ctx.lineTo(point[0], point[1]);
      }
      ctx.closePath();

      ctx.fillStyle = 'rgba(239, 68, 68, 0.3)';
      ctx.fill();
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 3]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Draw outer boundary outline
    // Use unclosed coordinates for display if boundary was not originally closed
    const displayBoundary = (!isOriginallyClosed && boundaryUnclosed && boundaryUnclosed.length > 0) 
      ? boundaryUnclosed 
      : boundary;
    
    ctx.beginPath();
    const outlineStart = transform(displayBoundary[0]);
    ctx.moveTo(outlineStart[0], outlineStart[1]);
    for (let i = 1; i < displayBoundary.length; i++) {
      const point = transform(displayBoundary[i]);
      ctx.lineTo(point[0], point[1]);
    }
    
    // Only close path if boundary was originally closed in DXF
    if (isOriginallyClosed) {
      ctx.closePath();
    }
    
    ctx.strokeStyle = isOriginallyClosed ? '#334155' : '#ef4444';  // Red for unclosed
    ctx.lineWidth = 3;
    ctx.stroke();
    
    // If unclosed, draw warning indicators at the gap
    if (!isOriginallyClosed && displayBoundary.length > 0) {
      const firstPoint = transform(displayBoundary[0]);
      const lastPoint = transform(displayBoundary[displayBoundary.length - 1]);
      
      // Draw circles at gap endpoints
      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.arc(firstPoint[0], firstPoint[1], 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(lastPoint[0], lastPoint[1], 6, 0, Math.PI * 2);
      ctx.fill();
      
      // Draw dashed line showing the gap
      ctx.beginPath();
      ctx.moveTo(firstPoint[0], firstPoint[1]);
      ctx.lineTo(lastPoint[0], lastPoint[1]);
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

  }, [boundary, boundaryUnclosed, isOriginallyClosed, holes, rooms, staircase, width, height]);

  const hasHoles = holes && holes.length > 0;

  return (
    <div className="viewer-container">
      <div className="viewer-toolbar">
        <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
          Floor Plan View
          {hasHoles && (
            <span style={{
              marginLeft: '0.5rem',
              padding: '0.125rem 0.5rem',
              background: '#fef2f2',
              color: '#dc2626',
              borderRadius: '4px',
              fontSize: '0.75rem'
            }}>
              {holes!.length} Courtyard{holes!.length > 1 ? 's' : ''}
            </span>
          )}
        </span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Scale: Auto-fit
        </span>
      </div>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="viewer-canvas"
      />
      <div className="viewer-legend">
        {Object.entries(ZONE_COLORS).map(([zone, colors]) => (
          <div key={zone} className="legend-item">
            <div className="legend-color" style={{ backgroundColor: colors.fill }}></div>
            <span>{colors.label}</span>
          </div>
        ))}
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#334155' }}></div>
          <span>Plot Boundary</span>
        </div>
        {hasHoles && (
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#ef4444', border: '1px dashed #ef4444' }}></div>
            <span>Courtyard</span>
          </div>
        )}
      </div>
    </div>
  );
}
