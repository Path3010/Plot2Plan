'use client';

import { useState, useEffect } from 'react';

interface ConfigurationPanelProps {
    onConfigChange: (config: any) => void;
    projectId: string;
}

export default function ConfigurationPanel({ onConfigChange, projectId }: ConfigurationPanelProps) {
    const [setbacks, setSetbacks] = useState({
        front: 3.0,
        back: 2.0,
        left: 1.5,
        right: 1.5,
    });

    const [strategy, setStrategy] = useState('compact');
    const [floors, setFloors] = useState(2);

    const strategies = [
        { id: 'compact', name: 'Compact', desc: 'Efficient rectangular layout' },
        { id: 'l_shape', name: 'L-Shape', desc: 'L-shaped with outdoor space' },
        { id: 'courtyard', name: 'Courtyard', desc: 'Central courtyard design' },
    ];

    useEffect(() => {
        onConfigChange({
            setbacks,
            layout: { strategy, floors },
            zones: { public: 40, private: 40, service: 20 },
        });
    }, [setbacks, strategy, floors]);

    const handleSetbackChange = (side: string, value: string) => {
        setSetbacks(prev => ({
            ...prev,
            [side]: parseFloat(value) || 0,
        }));
    };

    return (
        <div className="card">
            <div className="card-header">
                <h3>
                    <svg style={{ width: 18, height: 18, color: 'var(--primary-500)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Configuration
                </h3>
            </div>
            <div className="card-body">
                {/* Setbacks */}
                <div style={{ marginBottom: '1.25rem' }}>
                    <div className="form-label" style={{ marginBottom: '0.75rem' }}>Setbacks (meters)</div>
                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Front</label>
                            <input
                                type="number"
                                step="0.5"
                                value={setbacks.front}
                                onChange={(e) => handleSetbackChange('front', e.target.value)}
                                className="form-input"
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Back</label>
                            <input
                                type="number"
                                step="0.5"
                                value={setbacks.back}
                                onChange={(e) => handleSetbackChange('back', e.target.value)}
                                className="form-input"
                            />
                        </div>
                    </div>
                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Left</label>
                            <input
                                type="number"
                                step="0.5"
                                value={setbacks.left}
                                onChange={(e) => handleSetbackChange('left', e.target.value)}
                                className="form-input"
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Right</label>
                            <input
                                type="number"
                                step="0.5"
                                value={setbacks.right}
                                onChange={(e) => handleSetbackChange('right', e.target.value)}
                                className="form-input"
                            />
                        </div>
                    </div>
                </div>

                {/* Layout Strategy */}
                <div style={{ marginBottom: '1.25rem' }}>
                    <div className="form-label" style={{ marginBottom: '0.75rem' }}>Layout Strategy</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {strategies.map((s) => (
                            <div
                                key={s.id}
                                className={`option-card ${strategy === s.id ? 'selected' : ''}`}
                                onClick={() => setStrategy(s.id)}
                            >
                                <h4>{s.name}</h4>
                                <p>{s.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Number of Floors */}
                <div>
                    <div className="form-label" style={{ marginBottom: '0.75rem' }}>Number of Floors</div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {[1, 2, 3, 4].map((num) => (
                            <button
                                key={num}
                                onClick={() => setFloors(num)}
                                className="floor-tab"
                                style={{
                                    flex: 1,
                                    background: floors === num ? 'var(--primary-500)' : 'var(--slate-100)',
                                    color: floors === num ? 'white' : 'var(--text-secondary)',
                                    border: 'none',
                                    borderRadius: '8px',
                                    padding: '0.625rem',
                                    cursor: 'pointer',
                                    fontWeight: 600,
                                }}
                            >
                                {num}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
