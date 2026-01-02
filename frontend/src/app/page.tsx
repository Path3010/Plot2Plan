'use client';

import { useState } from 'react';
import DXFUploader from '@/components/DXFUploader';
import FloorPlanViewer from '@/components/FloorPlanViewer';
import ConfigurationPanel from '@/components/ConfigurationPanel';
import ScoreDisplay from '@/components/ScoreDisplay';
import FloorSelector from '@/components/FloorSelector';
import ValidationDisplay from '@/components/ValidationDisplay';

interface HoleData {
  id: number;
  coordinates: [number, number][];
  area_sqm: number;
}

interface ValidationData {
  is_valid: boolean;
  is_closed: boolean;
  is_simple: boolean;
  orientation: string;
  is_convex: boolean;
  aspect_ratio: number;
  compactness: number;
  num_vertices: number;
  was_corrected: boolean;
  issues: { code: string; message: string; severity: string }[];
}

interface ProjectData {
  project_id: string;
  filename: string;
  boundary: [number, number][];
  boundary_unclosed?: [number, number][];  // Original unclosed boundary for display
  is_originally_closed?: boolean;  // Was boundary closed in DXF?
  holes?: HoleData[];
  has_holes?: boolean;
  area_sqm: number;
  area_sqft: number;
  validation?: ValidationData;
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

    // Check if boundary has validation errors before generating
    if (project.validation && !project.validation.is_valid) {
      const errorMessages = project.validation.issues
        .filter(i => i.severity === 'error')
        .map(i => i.message)
        .join(', ');

      setError(`Cannot generate floor plan: ${errorMessages || 'Boundary has validation errors. Please upload a valid DXF file.'}`);
      return;
    }

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
    <div style={{ minHeight: '100vh' }}>
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo-icon">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div className="logo-text">
              <h1>Floor Plan Generator</h1>
              <p>Rule-based architectural design</p>
            </div>
          </div>

          {project && (
            <div className="header-actions">
              <div className="file-badge">
                <span className="file-name">{project.filename}</span>
                <span className="area-badge">{project.area_sqm.toFixed(1)} m²</span>
              </div>
              <button onClick={handleExport} className="btn btn-success">
                <svg style={{ width: 16, height: 16 }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Export DXF
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {error && (
          <div className="error-alert">
            <strong>Error:</strong> {error}
          </div>
        )}

        {!project ? (
          /* Upload Section */
          <div className="welcome-section">
            <h2 className="welcome-title">Get Started</h2>
            <p className="welcome-subtitle">Upload your plot boundary DXF file to begin generating floor plans</p>
            <DXFUploader onUploadSuccess={handleUploadSuccess} onUploadError={handleUploadError} />

            <div className="feature-grid">
              {[
                { icon: '📐', title: 'Any Shape', desc: 'Supports any polygon plot boundary' },
                { icon: '🏠', title: 'Multi-Floor', desc: 'Generate floor by floor progressively' },
                { icon: '📊', title: 'Smart Scoring', desc: 'AI-powered layout optimization' },
              ].map((feature, i) => (
                <div key={i} className="feature-card">
                  <div className="feature-icon">{feature.icon}</div>
                  <h3 className="feature-title">{feature.title}</h3>
                  <p className="feature-desc">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Design Workspace */
          <div className="workspace-grid">
            {/* Left Panel - Configuration */}
            <div className="panel-left">
              <ConfigurationPanel onConfigChange={handleConfigChange} projectId={project.project_id} />

              {project.validation && (
                <ValidationDisplay validation={project.validation} />
              )}

              {currentFloor && (
                <ScoreDisplay score={currentFloor.score} />
              )}
            </div>

            {/* Center - Floor Plan Viewer */}
            <div className="panel-center">
              <div className="center-header">
                <FloorSelector
                  floors={Array.from({ length: config.layout.floors }, (_, i) => i)}
                  activeFloor={activeFloor}
                  onFloorSelect={setActiveFloor}
                />

                <button
                  onClick={handleGenerateFloor}
                  disabled={isGenerating || (project?.validation && !project.validation.is_valid)}
                  className="btn btn-primary"
                  style={{
                    opacity: (project?.validation && !project.validation.is_valid) ? 0.6 : 1,
                    cursor: (project?.validation && !project.validation.is_valid) ? 'not-allowed' : 'pointer',
                  }}
                  title={
                    (project?.validation && !project.validation.is_valid) 
                      ? 'Fix boundary validation errors before generating' 
                      : undefined
                  }
                >
                  {isGenerating ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{
                        width: '16px',
                        height: '16px',
                        border: '2px solid rgba(255,255,255,0.3)',
                        borderTopColor: 'white',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                      }}></div>
                      Generating...
                    </span>
                  ) : (project?.validation && !project.validation.is_valid) ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      ⚠️ Fix Errors First
                    </span>
                  ) : (
                    `Generate ${activeFloor === 0 ? 'Ground Floor' : `Floor ${activeFloor}`}`
                  )}
                </button>
              </div>

              <FloorPlanViewer
                boundary={project.boundary}
                boundaryUnclosed={project.boundary_unclosed}
                isOriginallyClosed={project.is_originally_closed}
                holes={project.holes}
                rooms={currentFloor?.rooms || []}
                staircase={currentFloor?.staircase}
                width={750}
                height={500}
              />

              {/* Floor Stats */}
              {currentFloor && (
                <div className="stats-grid">
                  <div className="stat-card">
                    <div className="stat-label">Rooms</div>
                    <div className="stat-value">{currentFloor.rooms.length}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Buildable Area</div>
                    <div className="stat-value">{currentFloor.buildable_area_sqm.toFixed(1)} m²</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Layout Score</div>
                    <div className="stat-value success">{Math.round(currentFloor.score.total * 100)}%</div>
                  </div>
                </div>
              )}
            </div>

            {/* Right Panel - Room List */}
            <div className="panel-right">
              <div className="card">
                <div className="card-header">
                  <h3>
                    <svg style={{ width: 18, height: 18, color: 'var(--primary-500)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                    </svg>
                    Rooms
                  </h3>
                </div>
                <div className="card-body">
                  {currentFloor && currentFloor.rooms.length > 0 ? (
                    <div>
                      {currentFloor.rooms.map((room: any) => (
                        <div key={room.id} className={`room-item ${room.zone}`}>
                          <div>
                            <div className="room-name">{room.type.replace('_', ' ')}</div>
                            <div className="room-zone">{room.zone}</div>
                          </div>
                          <div className="room-area">{room.area_sqm.toFixed(1)} m²</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">
                      <p>No rooms generated yet</p>
                      <p className="hint">Click Generate to create floor plan</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
