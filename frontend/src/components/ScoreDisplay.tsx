'use client';

interface ScoreDisplayProps {
    score: {
        total: number;
        space_utilization?: number;
        adjacency?: number;
        proportions?: number;
        accessibility?: number;
    };
}

export default function ScoreDisplay({ score }: ScoreDisplayProps) {
    const scoreItems = [
        { key: 'space_utilization', label: 'Space Usage', color: '#3b82f6' },
        { key: 'adjacency', label: 'Adjacency', color: '#8b5cf6' },
        { key: 'proportions', label: 'Proportions', color: '#f59e0b' },
        { key: 'accessibility', label: 'Accessibility', color: '#22c55e' },
    ];

    const totalPercent = Math.round(score.total * 100);

    return (
        <div className="card">
            <div className="card-header">
                <h3>
                    <svg style={{ width: 18, height: 18, color: 'var(--primary-500)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Layout Score
                </h3>
            </div>
            <div className="card-body">
                {/* Total Score Circle */}
                <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                    <div style={{
                        width: '100px',
                        height: '100px',
                        borderRadius: '50%',
                        background: `conic-gradient(${totalPercent >= 70 ? '#22c55e' : totalPercent >= 40 ? '#f59e0b' : '#ef4444'} ${totalPercent}%, #e2e8f0 0%)`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto',
                    }}>
                        <div style={{
                            width: '80px',
                            height: '80px',
                            borderRadius: '50%',
                            background: 'white',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexDirection: 'column',
                        }}>
                            <span style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a' }}>{totalPercent}</span>
                            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>/ 100</span>
                        </div>
                    </div>
                    <p style={{ marginTop: '0.75rem', fontSize: '0.875rem', fontWeight: 500, color: '#475569' }}>
                        {totalPercent >= 80 ? 'Excellent' : totalPercent >= 60 ? 'Good' : totalPercent >= 40 ? 'Fair' : 'Needs Work'}
                    </p>
                </div>

                {/* Score Breakdown */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {scoreItems.map((item) => {
                        const value = score[item.key as keyof typeof score] as number | undefined;
                        const percent = value !== undefined ? Math.round(value * 100) : 0;

                        return (
                            <div key={item.key}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                    <span style={{ fontSize: '0.8125rem', color: '#475569' }}>{item.label}</span>
                                    <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#0f172a' }}>{percent}%</span>
                                </div>
                                <div style={{
                                    height: '8px',
                                    background: '#e2e8f0',
                                    borderRadius: '4px',
                                    overflow: 'hidden'
                                }}>
                                    <div style={{
                                        height: '100%',
                                        width: `${percent}%`,
                                        background: item.color,
                                        borderRadius: '4px',
                                        transition: 'width 0.5s ease',
                                    }}></div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
