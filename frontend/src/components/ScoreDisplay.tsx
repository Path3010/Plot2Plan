'use client';

interface ScoreDisplayProps {
    score: {
        total: number;
        area_efficiency: number;
        ventilation: number;
        circulation: number;
        adjacency: number;
        orientation?: number;
        proportion?: number;
    };
}

export default function ScoreDisplay({ score }: ScoreDisplayProps) {
    const scoreItems = [
        { key: 'area_efficiency', label: 'Area Efficiency', color: 'from-blue-500 to-cyan-500' },
        { key: 'ventilation', label: 'Ventilation', color: 'from-green-500 to-emerald-500' },
        { key: 'circulation', label: 'Circulation', color: 'from-purple-500 to-pink-500' },
        { key: 'adjacency', label: 'Adjacency', color: 'from-orange-500 to-yellow-500' },
    ];

    const getScoreColor = (value: number) => {
        if (value >= 0.8) return 'text-green-400';
        if (value >= 0.6) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getScoreLabel = (value: number) => {
        if (value >= 0.9) return 'Excellent';
        if (value >= 0.8) return 'Good';
        if (value >= 0.7) return 'Fair';
        return 'Needs Work';
    };

    return (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Layout Score
            </h3>

            {/* Total Score */}
            <div className="text-center mb-6">
                <div className="relative inline-flex items-center justify-center">
                    <svg className="w-32 h-32 transform -rotate-90">
                        <circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="none"
                            className="text-gray-700"
                        />
                        <circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke="url(#scoreGradient)"
                            strokeWidth="8"
                            fill="none"
                            strokeDasharray={`${score.total * 352} 352`}
                            strokeLinecap="round"
                        />
                        <defs>
                            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#3B82F6" />
                                <stop offset="100%" stopColor="#8B5CF6" />
                            </linearGradient>
                        </defs>
                    </svg>
                    <div className="absolute flex flex-col items-center">
                        <span className="text-3xl font-bold text-white">{Math.round(score.total * 100)}</span>
                        <span className="text-xs text-gray-400">/ 100</span>
                    </div>
                </div>
                <div className={`mt-2 font-medium ${getScoreColor(score.total)}`}>
                    {getScoreLabel(score.total)}
                </div>
            </div>

            {/* Individual Scores */}
            <div className="space-y-3">
                {scoreItems.map(({ key, label, color }) => {
                    const value = score[key as keyof typeof score] as number || 0;
                    return (
                        <div key={key}>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-400">{label}</span>
                                <span className={getScoreColor(value)}>{Math.round(value * 100)}%</span>
                            </div>
                            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                                <div
                                    className={`h-full bg-gradient-to-r ${color} transition-all duration-500`}
                                    style={{ width: `${value * 100}%` }}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
