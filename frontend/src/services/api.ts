const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface BoundingBox {
  min_x: number;
  min_y: number;
  max_x: number;
  max_y: number;
}

export interface UploadResponse {
  project_id: string;
  filename: string;
  boundary: [number, number][];
  area_sqm: number;
  area_sqft: number;
  bounding_box: BoundingBox;
  is_valid: boolean;
  message: string;
}

export interface SetbackConfig {
  front: number;
  back: number;
  left: number;
  right: number;
}

export interface FloorGenerationRequest {
  project_id: string;
  strategy: 'compact' | 'l_shape' | 'courtyard';
  required_rooms: string[];
  zone_distribution?: {
    public: number;
    private: number;
    service: number;
  };
}

export interface Room {
  id: string;
  type: string;
  zone: string;
  polygon: [number, number][];
  area_sqm: number;
  doors?: { position: number[]; width: number }[];
  windows?: { position: number[]; width: number }[];
}

export interface FloorData {
  floor_number: number;
  floor_name: string;
  buildable_area_sqm: number;
  rooms: Room[];
  staircase?: {
    type: string;
    polygon: [number, number][];
    entry_direction: string;
  };
  score: {
    total: number;
    area_efficiency: number;
    ventilation: number;
    circulation: number;
    adjacency: number;
  };
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  async uploadDxf(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async calculateSetback(projectId: string, config: SetbackConfig) {
    const response = await fetch(`${this.baseUrl}/api/generate/setback?project_id=${projectId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      throw new Error(`Setback calculation failed: ${response.statusText}`);
    }

    return response.json();
  }

  async generateFloor(floorNumber: number, request: FloorGenerationRequest): Promise<FloorData> {
    const response = await fetch(`${this.baseUrl}/api/generate/floor/${floorNumber}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Floor generation failed: ${response.statusText}`);
    }

    return response.json();
  }

  async exportProject(projectId: string) {
    const response = await fetch(`${this.baseUrl}/api/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: projectId,
        format: 'dxf',
        options: {
          include_dimensions: true,
          include_furniture: false,
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getRoomCatalog() {
    const response = await fetch(`${this.baseUrl}/api/rules/rooms`);
    return response.json();
  }

  async getLayoutStrategies() {
    const response = await fetch(`${this.baseUrl}/api/rules/strategies`);
    return response.json();
  }

  async healthCheck() {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }
}

export const api = new ApiService();
