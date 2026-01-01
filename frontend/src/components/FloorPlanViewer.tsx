'use client';

import { useEffect, useRef } from 'react';

interface FloorPlanViewerProps {
    boundary: [number, number][];
    buildableArea?: [number, number][];
    rooms?: {
        id: string;
        type: string;
        polygon: [number, number][];
        zone: string;
    }[];
    staircase?: {
        polygon: [number, number][];
    };
    width?: number;
    height?: number;
}

const ZONE_COLORS: Record<string, string> = {
    public: '#3B82F6',    // Blue
    private: '#8B5CF6',   // Purple
    service: '#F59E0B',   // Orange
    circulation: '#6B7280', // Gray
};

const ROOM_COLORS: Record<string, string> = {
    living_room: '#60A5FA',
    dining_room: '#34D399',
    kitchen: '#FBBF24',
    master_bedroom: '#A78BFA',
    bedroom: '#C4B5FD',
    bathroom: '#67E8F9',
    study: '#FCD34D',
    utility: '#9CA3AF',
    foyer: '#E5E7EB',
};

export default function FloorPlanViewer({
    boundary,
    buildableArea,
    rooms = [],
    staircase,
    width = 600,
    height = 500,
}: FloorPlanViewerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !boundary.length) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Calculate bounds
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        boundary.forEach(([x, y]) => {
            minX = Math.min(minX, x);
            minY = Math.min(minY, y);
            maxX = Math.max(maxX, x);
            maxY = Math.max(maxY, y);
        });

        const plotWidth = maxX - minX;
        const plotHeight = maxY - minY;
        const padding = 40;
        const scale = Math.min(
            (width - padding * 2) / plotWidth,
            (height - padding * 2) / plotHeight
        );

        const offsetX = (width - plotWidth * scale) / 2;
        const offsetY = (height - plotHeight * scale) / 2;

        const transform = (x: number, y: number): [number, number] => [
            (x - minX) * scale + offsetX,
            height - ((y - minY) * scale + offsetY), // Flip Y for canvas
        ];

        // Clear canvas
        ctx.fillStyle = '#1F2937';
        ctx.fillRect(0, 0, width, height);

        // Draw grid
        ctx.strokeStyle = '#374151';
        ctx.lineWidth = 0.5;
        const gridSize = 1 * scale; // 1 meter grid
        for (let x = 0; x < width; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
        }
        for (let y = 0; y < height; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }

        // Draw plot boundary
        ctx.beginPath();
        ctx.strokeStyle = '#FFFFFF';
        ctx.lineWidth = 3;
        const [startX, startY] = transform(boundary[0][0], boundary[0][1]);
        ctx.moveTo(startX, startY);
        boundary.slice(1).forEach(([x, y]) => {
            const [tx, ty] = transform(x, y);
            ctx.lineTo(tx, ty);
        });
        ctx.closePath();
        ctx.stroke();

        // Draw buildable area
        if (buildableArea && buildableArea.length > 0) {
            ctx.beginPath();
            ctx.fillStyle = 'rgba(59, 130, 246, 0.1)';
            ctx.strokeStyle = '#3B82F6';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            const [bStartX, bStartY] = transform(buildableArea[0][0], buildableArea[0][1]);
            ctx.moveTo(bStartX, bStartY);
            buildableArea.slice(1).forEach(([x, y]) => {
                const [tx, ty] = transform(x, y);
                ctx.lineTo(tx, ty);
            });
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            ctx.setLineDash([]);
        }

        // Draw rooms
        rooms.forEach((room) => {
            if (!room.polygon || room.polygon.length === 0) return;

            ctx.beginPath();
            const color = ROOM_COLORS[room.type] || ZONE_COLORS[room.zone] || '#6B7280';
            ctx.fillStyle = color + '40'; // Add transparency
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;

            const [rStartX, rStartY] = transform(room.polygon[0][0], room.polygon[0][1]);
            ctx.moveTo(rStartX, rStartY);
            room.polygon.slice(1).forEach(([x, y]) => {
                const [tx, ty] = transform(x, y);
                ctx.lineTo(tx, ty);
            });
            ctx.closePath();
            ctx.fill();
            ctx.stroke();

            // Draw room label
            const centerX = room.polygon.reduce((sum, [x]) => sum + x, 0) / room.polygon.length;
            const centerY = room.polygon.reduce((sum, [, y]) => sum + y, 0) / room.polygon.length;
            const [labelX, labelY] = transform(centerX, centerY);

            ctx.fillStyle = '#FFFFFF';
            ctx.font = '11px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(room.type.replace('_', ' '), labelX, labelY);
        });

        // Draw staircase
        if (staircase && staircase.polygon.length > 0) {
            ctx.beginPath();
            ctx.fillStyle = 'rgba(236, 72, 153, 0.3)';
            ctx.strokeStyle = '#EC4899';
            ctx.lineWidth = 2;

            const [sStartX, sStartY] = transform(staircase.polygon[0][0], staircase.polygon[0][1]);
            ctx.moveTo(sStartX, sStartY);
            staircase.polygon.slice(1).forEach(([x, y]) => {
                const [tx, ty] = transform(x, y);
                ctx.lineTo(tx, ty);
            });
            ctx.closePath();
            ctx.fill();
            ctx.stroke();

            // Stair symbol
            const cx = staircase.polygon.reduce((sum, [x]) => sum + x, 0) / staircase.polygon.length;
            const cy = staircase.polygon.reduce((sum, [, y]) => sum + y, 0) / staircase.polygon.length;
            const [scx, scy] = transform(cx, cy);
            ctx.fillStyle = '#EC4899';
            ctx.font = 'bold 12px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('↑ STAIR', scx, scy);
        }

        // Draw scale bar
        ctx.fillStyle = '#9CA3AF';
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('1m', padding, height - 10);
        ctx.strokeStyle = '#9CA3AF';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(padding, height - 20);
        ctx.lineTo(padding + scale, height - 20);
        ctx.stroke();

    }, [boundary, buildableArea, rooms, staircase, width, height]);

    return (
        <div className="relative rounded-xl overflow-hidden bg-gray-800 shadow-xl">
            <canvas
                ref={canvasRef}
                width={width}
                height={height}
                className="block"
            />

            {/* Legend */}
            <div className="absolute bottom-4 right-4 bg-gray-900/80 backdrop-blur p-3 rounded-lg">
                <div className="text-xs text-gray-400 mb-2 font-medium">Legend</div>
                <div className="flex flex-col gap-1 text-xs">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-white/80 border border-white"></div>
                        <span className="text-gray-300">Plot Boundary</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 border-2 border-blue-500 border-dashed"></div>
                        <span className="text-gray-300">Buildable Area</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-pink-500/50 border border-pink-500"></div>
                        <span className="text-gray-300">Staircase</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
