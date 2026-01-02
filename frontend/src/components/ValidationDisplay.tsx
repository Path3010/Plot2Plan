'use client';

interface ValidationIssue {
    code: string;
    message: string;
    severity: string;
}

interface ValidationDisplayProps {
    validation: {
        is_valid: boolean;
        is_closed: boolean;
        is_simple: boolean;
        orientation: string;
        is_convex: boolean;
        aspect_ratio: number;
        compactness: number;
        num_vertices: number;
        was_corrected: boolean;
        issues: ValidationIssue[];
    };
}

export default function ValidationDisplay({ validation }: ValidationDisplayProps) {
    const checks = [
        { label: 'Closed', value: validation.is_closed, icon: '🔒' },
        { label: 'Simple (no self-intersection)', value: validation.is_simple, icon: '✓' },
        { label: 'Convex', value: validation.is_convex, icon: '◇' },
    ];

    const properties = [
        { label: 'Vertices', value: validation.num_vertices },
        { label: 'Orientation', value: validation.orientation.toUpperCase() },
        { label: 'Aspect Ratio', value: validation.aspect_ratio.toFixed(2) },
        { label: 'Compactness', value: `${(validation.compactness * 100).toFixed(0)}%` },
    ];

    const errors = validation.issues.filter(i => i.severity === 'error');
    const warnings = validation.issues.filter(i => i.severity === 'warning');

    return (
        <div className="card">
            <div className="card-header">
                <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <svg style={{ width: 18, height: 18, color: validation.is_valid ? 'var(--success-500)' : 'var(--error-500)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        {validation.is_valid ? (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        )}
                    </svg>
                    Boundary Validation
                    {validation.was_corrected && (
                        <span style={{
                            fontSize: '0.625rem',
                            padding: '0.125rem 0.375rem',
                            background: '#fef3c7',
                            color: '#92400e',
                            borderRadius: '4px',
                        }}>
                            Auto-fixed
                        </span>
                    )}
                </h3>
            </div>
            <div className="card-body">
                {/* Overall Status */}
                <div style={{
                    padding: '0.75rem',
                    borderRadius: '8px',
                    marginBottom: '1rem',
                    background: validation.is_valid ? '#f0fdf4' : '#fef2f2',
                    border: `1px solid ${validation.is_valid ? '#bbf7d0' : '#fecaca'}`,
                }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        color: validation.is_valid ? '#166534' : '#991b1b',
                        fontWeight: 600,
                        fontSize: '0.875rem',
                    }}>
                        {validation.is_valid ? '✓ Boundary is valid' : '✗ Validation issues found'}
                    </div>
                </div>

                {/* Validation Checks */}
                <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', fontWeight: 500 }}>
                        CHECKS
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                        {checks.map((check, i) => (
                            <div key={i} style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                padding: '0.375rem 0.5rem',
                                background: 'var(--slate-50)',
                                borderRadius: '6px',
                                fontSize: '0.8125rem',
                            }}>
                                <span style={{ color: 'var(--text-secondary)' }}>{check.label}</span>
                                <span style={{
                                    color: check.value ? '#16a34a' : '#dc2626',
                                    fontWeight: 500,
                                }}>
                                    {check.value ? '✓ Yes' : '✗ No'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Properties */}
                <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', fontWeight: 500 }}>
                        PROPERTIES
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.375rem' }}>
                        {properties.map((prop, i) => (
                            <div key={i} style={{
                                padding: '0.375rem 0.5rem',
                                background: 'var(--slate-50)',
                                borderRadius: '6px',
                                fontSize: '0.8125rem',
                            }}>
                                <div style={{ color: 'var(--text-muted)', fontSize: '0.6875rem' }}>{prop.label}</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{prop.value}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Issues */}
                {(errors.length > 0 || warnings.length > 0) && (
                    <div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', fontWeight: 500 }}>
                            ISSUES
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                            {errors.map((issue, i) => (
                                <div key={`e-${i}`} style={{
                                    padding: '0.5rem',
                                    background: '#fef2f2',
                                    border: '1px solid #fecaca',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                }}>
                                    <div style={{ color: '#991b1b', fontWeight: 600 }}>⚠ {issue.code}</div>
                                    <div style={{ color: '#b91c1c', marginTop: '0.125rem' }}>{issue.message}</div>
                                </div>
                            ))}
                            {warnings.map((issue, i) => (
                                <div key={`w-${i}`} style={{
                                    padding: '0.5rem',
                                    background: '#fffbeb',
                                    border: '1px solid #fde68a',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                }}>
                                    <div style={{ color: '#92400e', fontWeight: 600 }}>⚡ {issue.code}</div>
                                    <div style={{ color: '#a16207', marginTop: '0.125rem' }}>{issue.message}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
