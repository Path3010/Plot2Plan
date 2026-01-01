'use client';

import { useState } from 'react';
import DXFUploader from '@/components/DXFUploader';
import FloorPlanViewer from '@/components/FloorPlanViewer';
import ConfigurationPanel from '@/components/ConfigurationPanel';
import ScoreDisplay from '@/components/ScoreDisplay';
import FloorSelector from '@/components/FloorSelector';

interface ProjectData {
  project_id: string;
  filename: string;
  boundary: [number, number][];
  area_sqm: number;
  area_sqft: number;
}

interface FloorData {
  floor_number: number;
  rooms: any[];
  staircase?: any;
  score: any;
  buildable_area_sqm: number;
}

export default function Home() {
  const [project, setProject] = useState<ProjectData | null>(null);
  const [floors, setFloors] = useState<FloorData[]>([]);
  const [activeFloor, setActiveFloor] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState({
    setbacks: { front: 3.0, back: 2.0, left: 1.5, right: 1.5 },
    layout: { strategy: 'compact', floors: 2 },
    zones: { public: 40, private: 40, service: 20 },
  });

  const handleUploadSuccess = (data: ProjectData) => {
    setProject(data);
    setError(null);
    setFloors([]);
  };

  const handleUploadError = (errorMsg: string) => {
    setError(errorMsg);
  };

  const handleConfigChange = (newConfig: any) => {
    setConfig(newConfig);
  };

  const handleGenerateFloor = async () => {
    if (!project) return;

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/api/generate/floor/${activeFloor}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: project.project_id,
          strategy: config.layout.strategy,
          required_rooms: activeFloor === 0
            ? ['living_room', 'dining_room', 'kitchen', 'powder_room']
            : ['master_bedroom', 'bedroom', 'bathroom'],
          zone_distribution: {
            public: config.zones.public / 100,
            private: config.zones.private / 100,
            service: config.zones.service / 100,
          },
        }),
      });

      if (!response.ok) throw new Error('Generation failed');

      const floorData = await response.json();

      setFloors(prev => {
        const existing = prev.filter(f => f.floor_number !== activeFloor);
        return [...existing, floorData].sort((a, b) => a.floor_number - b.floor_number);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExport = async () => {
    if (!project) return;

    try {
      const response = await fetch('http://localhost:8000/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: project.project_id,
          format: 'dxf',
          options: { include_dimensions: true },
        }),
      });

      const result = await response.json();
      alert(`Export initiated! Download URL: ${result.download_url}`);
    } catch (err) {
      setError('Export failed');
    }
  };

  const currentFloor = floors.find(f => f.floor_number === activeFloor);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="border-b border-gray-700/50 backdrop-blur-sm sticky top-0 z-50 bg-gray-900/80">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Floor Plan Generator</h1>
                <p className="text-xs text-gray-400">Rule-based architectural design</p>
              </div>
            </div>

            {project && (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-400">{project.filename}</span>
                <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
                  {project.area_sqm.toFixed(1)} m²
                </span>
                <button
                  onClick={handleExport}
                  className="px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg text-white text-sm font-medium hover:from-green-500 hover:to-emerald-500 transition-all"
                >
                  Export DXF
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {!project ? (
          /* Upload Section */
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-white mb-2">Get Started</h2>
              <p className="text-gray-400">Upload your plot boundary DXF file to begin generating floor plans</p>
            </div>
            <DXFUploader onUploadSuccess={handleUploadSuccess} onUploadError={handleUploadError} />

            <div className="mt-8 grid grid-cols-3 gap-6">
              {[
                { icon: '📐', title: 'Any Shape', desc: 'Supports any polygon plot boundary' },
                { icon: '🏠', title: 'Multi-Floor', desc: 'Generate floor by floor progressively' },
                { icon: '📊', title: 'Smart Scoring', desc: 'AI-powered layout optimization' },
              ].map((feature, i) => (
                <div key={i} className="p-4 bg-gray-800/50 rounded-xl border border-gray-700 text-center">
                  <div className="text-3xl mb-2">{feature.icon}</div>
                  <h3 className="font-medium text-white">{feature.title}</h3>
                  <p className="text-xs text-gray-400 mt-1">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Design Workspace */
          <div className="grid grid-cols-12 gap-6">
            {/* Left Panel - Configuration */}
            <div className="col-span-3 space-y-6">
              <ConfigurationPanel onConfigChange={handleConfigChange} projectId={project.project_id} />

              {currentFloor && (
                <ScoreDisplay score={currentFloor.score} />
              )}
            </div>

            {/* Center - Floor Plan Viewer */}
            <div className="col-span-6 space-y-4">
              <div className="flex items-center justify-between">
                <FloorSelector
                  floors={Array.from({ length: config.layout.floors }, (_, i) => i)}
                  activeFloor={activeFloor}
                  onFloorSelect={setActiveFloor}
                />

                <button
                  onClick={handleGenerateFloor}
                  disabled={isGenerating}
                  className={`px-6 py-2 rounded-lg font-medium transition-all ${isGenerating
                      ? 'bg-gray-600 cursor-not-allowed'
                      : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500'
                    } text-white`}
                >
                  {isGenerating ? (
                    <span className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      Generating...
                    </span>
                  ) : (
                    `Generate ${activeFloor === 0 ? 'Ground' : `Floor ${activeFloor}`}`
                  )}
                </button>
              </div>

              <FloorPlanViewer
                boundary={project.boundary}
                rooms={currentFloor?.rooms || []}
                staircase={currentFloor?.staircase}
                width={700}
                height={550}
              />

              {/* Floor Info */}
              {currentFloor && (
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                    <div className="text-sm text-gray-400">Rooms</div>
                    <div className="text-2xl font-bold text-white">{currentFloor.rooms.length}</div>
                  </div>
                  <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                    <div className="text-sm text-gray-400">Buildable Area</div>
                    <div className="text-2xl font-bold text-white">{currentFloor.buildable_area_sqm.toFixed(1)} m²</div>
                  </div>
                  <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                    <div className="text-sm text-gray-400">Layout Score</div>
                    <div className="text-2xl font-bold text-green-400">{Math.round(currentFloor.score.total * 100)}%</div>
                  </div>
                </div>
              )}
            </div>

            {/* Right Panel - Room List */}
            <div className="col-span-3">
              <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">Rooms</h3>

                {currentFloor && currentFloor.rooms.length > 0 ? (
                  <div className="space-y-2">
                    {currentFloor.rooms.map((room: any) => (
                      <div
                        key={room.id}
                        className="p-3 bg-gray-700/50 rounded-lg flex items-center justify-between"
                      >
                        <div>
                          <div className="text-sm font-medium text-white capitalize">
                            {room.type.replace('_', ' ')}
                          </div>
                          <div className="text-xs text-gray-400">{room.zone}</div>
                        </div>
                        <div className="text-sm text-gray-300">
                          {room.area_sqm.toFixed(1)} m²
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <p>No rooms generated yet</p>
                    <p className="text-xs mt-1">Click Generate to create floor plan</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
