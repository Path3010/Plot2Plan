'use client';

import { useState } from 'react';

interface ConfigPanelProps {
    onConfigChange: (config: any) => void;
    projectId?: string;
}

export default function ConfigurationPanel({ onConfigChange, projectId }: ConfigPanelProps) {
    const [setbacks, setSetbacks] = useState({
        front: 3.0,
        back: 2.0,
        left: 1.5,
        right: 1.5,
    });

    const [layout, setLayout] = useState({
        strategy: 'compact',
        floors: 2,
    });

    const [zones, setZones] = useState({
        public: 40,
        private: 40,
        service: 20,
    });

    const strategies = [
        { id: 'compact', name: 'Compact', desc: 'Efficient rectangular layout' },
        { id: 'l_shape', name: 'L-Shape', desc: 'L-shaped with outdoor space' },
        { id: 'courtyard', name: 'Courtyard', desc: 'Central courtyard design' },
    ];

    const handleSetbackChange = (key: string, value: number) => {
        const newSetbacks = { ...setbacks, [key]: value };
        setSetbacks(newSetbacks);
        onConfigChange({ setbacks: newSetbacks, layout, zones });
    };

    const handleZoneChange = (key: string, value: number) => {
        const remaining = 100 - value;
        const others = Object.keys(zones).filter(k => k !== key);
        const newZones = {
            ...zones,
            [key]: value,
            [others[0]]: Math.round(remaining / 2),
            [others[1]]: remaining - Math.round(remaining / 2),
        };
        setZones(newZones);
        onConfigChange({ setbacks, layout, zones: newZones });
    };

    return (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 space-y-6 border border-gray-700">
            <div>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Configuration
                </h3>
            </div>

            {/* Setbacks Section */}
            <div className="space-y-4">
                <h4 className="text-sm font-medium text-gray-300 uppercase tracking-wider">Setbacks (meters)</h4>
                <div className="grid grid-cols-2 gap-4">
                    {Object.entries(setbacks).map(([key, value]) => (
                        <div key={key}>
                            <label className="block text-xs text-gray-400 mb-1 capitalize">{key}</label>
                            <input
                                type="number"
                                step="0.5"
                                min="0"
                                max="10"
                                value={value}
                                onChange={(e) => handleSetbackChange(key, parseFloat(e.target.value))}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                    ))}
                </div>
            </div>

            {/* Layout Strategy */}
            <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-300 uppercase tracking-wider">Layout Strategy</h4>
                <div className="space-y-2">
                    {strategies.map((strategy) => (
                        <label
                            key={strategy.id}
                            className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${layout.strategy === strategy.id
                                    ? 'bg-blue-600/20 border border-blue-500'
                                    : 'bg-gray-700/50 border border-transparent hover:bg-gray-700'
                                }`}
                        >
                            <input
                                type="radio"
                                name="strategy"
                                value={strategy.id}
                                checked={layout.strategy === strategy.id}
                                onChange={(e) => {
                                    const newLayout = { ...layout, strategy: e.target.value };
                                    setLayout(newLayout);
                                    onConfigChange({ setbacks, layout: newLayout, zones });
                                }}
                                className="hidden"
                            />
                            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${layout.strategy === strategy.id ? 'border-blue-500' : 'border-gray-500'
                                }`}>
                                {layout.strategy === strategy.id && (
                                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                                )}
                            </div>
                            <div>
                                <div className="text-sm font-medium text-white">{strategy.name}</div>
                                <div className="text-xs text-gray-400">{strategy.desc}</div>
                            </div>
                        </label>
                    ))}
                </div>
            </div>

            {/* Floor Count */}
            <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-300 uppercase tracking-wider">Number of Floors</h4>
                <div className="flex gap-2">
                    {[1, 2, 3, 4].map((num) => (
                        <button
                            key={num}
                            onClick={() => {
                                const newLayout = { ...layout, floors: num };
                                setLayout(newLayout);
                                onConfigChange({ setbacks, layout: newLayout, zones });
                            }}
                            className={`flex-1 py-2 rounded-lg font-medium transition-all ${layout.floors === num
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                }`}
                        >
                            {num}
                        </button>
                    ))}
                </div>
            </div>

            {/* Zone Distribution */}
            <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-300 uppercase tracking-wider">Zone Distribution</h4>
                <div className="space-y-3">
                    {[
                        { key: 'public', label: 'Public', color: 'bg-blue-500' },
                        { key: 'private', label: 'Private', color: 'bg-purple-500' },
                        { key: 'service', label: 'Service', color: 'bg-orange-500' },
                    ].map(({ key, label, color }) => (
                        <div key={key}>
                            <div className="flex justify-between text-xs mb-1">
                                <span className="text-gray-400">{label}</span>
                                <span className="text-white">{zones[key as keyof typeof zones]}%</span>
                            </div>
                            <input
                                type="range"
                                min="10"
                                max="60"
                                value={zones[key as keyof typeof zones]}
                                onChange={(e) => handleZoneChange(key, parseInt(e.target.value))}
                                className={`w-full h-2 rounded-lg appearance-none cursor-pointer ${color}`}
                            />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
