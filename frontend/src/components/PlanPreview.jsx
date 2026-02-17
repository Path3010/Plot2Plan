import { useMemo } from 'react'

const ROOM_COLORS = {
    living: '#4f46e5',
    master_bedroom: '#dc2626',
    bedroom: '#ea580c',
    kitchen: '#059669',
    bathroom: '#0284c7',
    dining: '#d97706',
    study: '#7c3aed',
    hallway: '#6b7280',
    pooja: '#e11d48',
    store: '#64748b',
    garage: '#475569',
    balcony: '#0d9488',
    other: '#6b7280',
}

const ROOM_BG_COLORS = {
    living: '#eef2ff',
    master_bedroom: '#fef2f2',
    bedroom: '#fff7ed',
    kitchen: '#ecfdf5',
    bathroom: '#f0f9ff',
    dining: '#fffbeb',
    study: '#f5f3ff',
    hallway: '#f9fafb',
    pooja: '#fff1f2',
    store: '#f8fafc',
    garage: '#f1f5f9',
    balcony: '#f0fdfa',
    other: '#f9fafb',
}

export default function PlanPreview({ plan }) {
    const svgContent = useMemo(() => {
        if (!plan || !plan.boundary || plan.boundary.length < 3) return null

        const allPoints = [
            ...plan.boundary,
            ...plan.rooms.flatMap(r => r.polygon || []),
        ]
        const xs = allPoints.map(p => p[0])
        const ys = allPoints.map(p => p[1])
        const minX = Math.min(...xs)
        const minY = Math.min(...ys)
        const maxX = Math.max(...xs)
        const maxY = Math.max(...ys)
        const padFrac = 0.12
        const w = maxX - minX
        const h = maxY - minY
        const pad = Math.max(w, h) * padFrac

        const viewBox = `${minX - pad} ${minY - pad} ${w + pad * 2} ${h + pad * 2}`

        return { viewBox, minX, minY, maxX, maxY, w, h }
    }, [plan])

    if (!svgContent) return <div className="preview-empty"><p>No plan data</p></div>

    const toPathD = (coords) => {
        if (!coords || coords.length < 2) return ''
        return coords.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ') + ' Z'
    }

    const scale = Math.max(svgContent.w, svgContent.h)

    return (
        <div className="plan-svg" style={{ padding: '1rem' }}>
            <svg viewBox={svgContent.viewBox} xmlns="http://www.w3.org/2000/svg">
                {/* Background */}
                <rect
                    x={svgContent.minX - svgContent.w * 0.12}
                    y={svgContent.minY - svgContent.h * 0.12}
                    width={svgContent.w * 1.24}
                    height={svgContent.h * 1.24}
                    fill="#ffffff"
                />

                {/* Boundary */}
                <path
                    d={toPathD(plan.boundary)}
                    fill="#f8f9fc"
                    stroke="#0f172a"
                    strokeWidth={scale * 0.005}
                />

                {/* Rooms */}
                {plan.rooms.map((room, i) => {
                    const color = ROOM_COLORS[room.room_type] || ROOM_COLORS.other
                    const bgColor = ROOM_BG_COLORS[room.room_type] || ROOM_BG_COLORS.other
                    return (
                        <g key={i}>
                            <path
                                d={toPathD(room.polygon)}
                                fill={bgColor}
                                stroke={color}
                                strokeWidth={scale * 0.003}
                            />
                            {room.centroid && (
                                <>
                                    <text
                                        x={room.centroid[0]}
                                        y={room.centroid[1] - svgContent.h * 0.012}
                                        textAnchor="middle"
                                        fill={color}
                                        fontSize={scale * 0.022}
                                        fontWeight="700"
                                        fontFamily="Inter, sans-serif"
                                    >
                                        {room.label}
                                    </text>
                                    <text
                                        x={room.centroid[0]}
                                        y={room.centroid[1] + svgContent.h * 0.025}
                                        textAnchor="middle"
                                        fill="#94a3b8"
                                        fontSize={scale * 0.016}
                                        fontFamily="Inter, sans-serif"
                                    >
                                        {room.actual_area?.toFixed(0)} sqft
                                    </text>
                                </>
                            )}
                        </g>
                    )
                })}

                {/* Doors */}
                {plan.doors?.map((door, i) => (
                    <circle
                        key={`door-${i}`}
                        cx={door.position[0]}
                        cy={door.position[1]}
                        r={scale * 0.007}
                        fill="none"
                        stroke="#059669"
                        strokeWidth={scale * 0.002}
                    />
                ))}

                {/* Windows */}
                {plan.windows?.map((win, i) => (
                    <rect
                        key={`win-${i}`}
                        x={win.position[0] - svgContent.w * 0.012}
                        y={win.position[1] - svgContent.h * 0.003}
                        width={svgContent.w * 0.024}
                        height={svgContent.h * 0.006}
                        fill="#0284c7"
                        rx={1}
                    />
                ))}

                {/* Title */}
                <text
                    x={svgContent.minX}
                    y={svgContent.minY - svgContent.h * 0.05}
                    fill="#0f172a"
                    fontSize={scale * 0.03}
                    fontWeight="800"
                    fontFamily="Inter, sans-serif"
                >
                    FLOOR PLAN
                </text>
                <text
                    x={svgContent.minX}
                    y={svgContent.minY - svgContent.h * 0.02}
                    fill="#94a3b8"
                    fontSize={scale * 0.018}
                    fontFamily="Inter, sans-serif"
                >
                    Total: {plan.total_area?.toFixed(0)} sq ft | {plan.rooms.length} rooms
                </text>
            </svg>
        </div>
    )
}
