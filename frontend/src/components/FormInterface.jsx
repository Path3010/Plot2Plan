import { useState, useRef } from 'react'

const ROOM_TYPES = [
    { key: 'master_bedroom', label: 'Master Bedroom' },
    { key: 'bedroom', label: 'Bedroom' },
    { key: 'bathroom', label: 'Bathroom' },
    { key: 'kitchen', label: 'Kitchen' },
    { key: 'living', label: 'Living Room' },
    { key: 'dining', label: 'Dining Room' },
    { key: 'study', label: 'Study' },
    { key: 'pooja', label: 'Pooja Room' },
    { key: 'store', label: 'Store Room' },
    { key: 'garage', label: 'Garage' },
    { key: 'balcony', label: 'Balcony' },
    { key: 'hallway', label: 'Hallway' },
]

export default function FormInterface({ onGenerate, onBoundaryUpload, boundary }) {
    const [step, setStep] = useState(0)
    const [totalArea, setTotalArea] = useState(1200)
    const [selectedRooms, setSelectedRooms] = useState({
        master_bedroom: { selected: true, qty: 1 },
        bedroom: { selected: true, qty: 1 },
        bathroom: { selected: true, qty: 1 },
        kitchen: { selected: true, qty: 1 },
        living: { selected: true, qty: 1 },
        dining: { selected: true, qty: 1 },
    })
    const fileInputRef = useRef(null)

    const toggleRoom = (key) => {
        setSelectedRooms(prev => ({
            ...prev,
            [key]: {
                ...prev[key],
                selected: !prev[key]?.selected,
                qty: prev[key]?.qty || 1,
            },
        }))
    }

    const setQty = (key, qty) => {
        setSelectedRooms(prev => ({
            ...prev,
            [key]: { ...prev[key], qty: Math.max(1, parseInt(qty) || 1) },
        }))
    }

    const handleFileUpload = async (e) => {
        const file = e.target.files?.[0]
        if (file) await onBoundaryUpload(file)
    }

    const handleGenerate = () => {
        const rooms = Object.entries(selectedRooms)
            .filter(([_, v]) => v.selected)
            .map(([key, v]) => ({
                room_type: key,
                quantity: v.qty || 1,
            }))
        onGenerate(rooms, totalArea)
    }

    return (
        <div>
            <div className="step-indicator">
                {[0, 1, 2, 3].map(s => (
                    <div
                        key={s}
                        className={`step-dot ${s === step ? 'active' : s < step ? 'done' : ''}`}
                    />
                ))}
            </div>

            {step === 0 && (
                <div className="form-section">
                    <h3>Plot Details</h3>
                    <div className="form-group">
                        <label>Total Area (sq ft)</label>
                        <input
                            className="form-input"
                            type="number"
                            value={totalArea}
                            onChange={(e) => setTotalArea(parseInt(e.target.value) || 0)}
                            min={100}
                            max={50000}
                        />
                    </div>
                    <button className="btn btn-primary" onClick={() => setStep(1)} style={{ width: '100%', marginTop: '1rem' }}>
                        Next
                    </button>
                </div>
            )}

            {step === 1 && (
                <div className="form-section">
                    <h3>Boundary</h3>
                    <div
                        className="file-upload"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileUpload}
                            accept=".png,.jpg,.jpeg,.dxf"
                            style={{ display: 'none' }}
                        />
                        <div className="file-upload-icon">
                            <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <p><strong>Click to upload</strong> boundary sketch</p>
                        <p>PNG, JPEG, or DXF</p>
                    </div>

                    {boundary && (
                        <div style={{
                            marginTop: '1rem',
                            padding: '0.8rem',
                            background: 'var(--success-bg)',
                            border: '1px solid #a7f3d0',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '0.85rem',
                            color: '#065f46',
                        }}>
                            Boundary extracted ({boundary.length - 1} vertices)
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                        <button className="btn btn-secondary" onClick={() => setStep(0)} style={{ flex: 1 }}>
                            Back
                        </button>
                        <button className="btn btn-primary" onClick={() => setStep(2)} style={{ flex: 1 }}>
                            {boundary ? 'Next' : 'Skip (Rectangle)'}
                        </button>
                    </div>
                </div>
            )}

            {step === 2 && (
                <div className="form-section">
                    <h3>Rooms and Amenities</h3>
                    <div className="amenity-grid">
                        {ROOM_TYPES.map(r => {
                            const state = selectedRooms[r.key]
                            return (
                                <div
                                    key={r.key}
                                    className={`amenity-item ${state?.selected ? 'selected' : ''}`}
                                    onClick={() => toggleRoom(r.key)}
                                >
                                    <input
                                        type="checkbox"
                                        checked={!!state?.selected}
                                        onChange={() => toggleRoom(r.key)}
                                        onClick={(e) => e.stopPropagation()}
                                    />
                                    <span>{r.label}</span>
                                    {state?.selected && (
                                        <input
                                            className="form-input amenity-qty"
                                            type="number"
                                            value={state.qty || 1}
                                            onClick={(e) => e.stopPropagation()}
                                            onChange={(e) => setQty(r.key, e.target.value)}
                                            min={1}
                                            max={10}
                                        />
                                    )}
                                </div>
                            )
                        })}
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
                        <button className="btn btn-secondary" onClick={() => setStep(1)} style={{ flex: 1 }}>
                            Back
                        </button>
                        <button className="btn btn-primary" onClick={() => setStep(3)} style={{ flex: 1 }}>
                            Next
                        </button>
                    </div>
                </div>
            )}

            {step === 3 && (
                <div className="form-section">
                    <h3>Review and Generate</h3>

                    <div style={{
                        background: 'var(--bg-input)',
                        border: '1px solid var(--border)',
                        borderRadius: 'var(--radius-md)',
                        padding: '1rem',
                        marginBottom: '1.5rem',
                    }}>
                        <div style={{ marginBottom: '0.8rem' }}>
                            <strong style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Total Area</strong>
                            <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{totalArea} sq ft</div>
                        </div>

                        <div style={{ marginBottom: '0.8rem' }}>
                            <strong style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Boundary</strong>
                            <div style={{ fontSize: '0.9rem' }}>
                                {boundary ? `Custom (${boundary.length - 1} vertices)` : 'Auto Rectangle'}
                            </div>
                        </div>

                        <div>
                            <strong style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Rooms</strong>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.4rem' }}>
                                {Object.entries(selectedRooms)
                                    .filter(([_, v]) => v.selected)
                                    .map(([key, v]) => {
                                        const room = ROOM_TYPES.find(r => r.key === key)
                                        return (
                                            <span key={key} style={{
                                                padding: '0.3rem 0.6rem',
                                                background: 'var(--bg-secondary)',
                                                border: '1px solid var(--border)',
                                                borderRadius: 'var(--radius-sm)',
                                                fontSize: '0.8rem',
                                            }}>
                                                {room?.label} x{v.qty}
                                            </span>
                                        )
                                    })}
                            </div>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button className="btn btn-secondary" onClick={() => setStep(2)} style={{ flex: 1 }}>
                            Back
                        </button>
                        <button className="btn btn-primary" onClick={handleGenerate} style={{ flex: 1 }}>
                            Generate Floor Plan
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
