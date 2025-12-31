# Floor Plan Generator

A web-based architectural residential floor plan generator that takes plot boundary DXF files as input and generates multi-floor house plans using rule-based logic.

## 🚀 Features

- **DXF Input**: Upload any polygon-shaped plot boundary
- **Multi-Floor Generation**: Progressive floor-by-floor generation (Ground → Upper floors)
- **Zone-Based Planning**: Public, Private, Service zone allocation
- **Layout Strategies**: Compact, L-Shape, Courtyard configurations
- **Smart Scoring**: Layout evaluation based on area usage, ventilation, circulation
- **DXF Export**: Single file with all floors in separate layers

## 📁 Project Structure

```
FloorPlan Generation/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/routes/        # API endpoints
│   │   ├── core/              # Core generation engine
│   │   │   ├── dxf_parser.py
│   │   │   ├── setback_engine.py
│   │   │   ├── zone_allocator.py
│   │   │   ├── room_generator.py
│   │   │   ├── staircase_handler.py
│   │   │   ├── layout_scorer.py
│   │   │   └── dxf_exporter.py
│   │   ├── models/
│   │   ├── rules/
│   │   └── main.py            # FastAPI entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js React frontend
│   ├── src/
│   │   ├── app/page.tsx       # Main application
│   │   ├── components/        # UI components
│   │   └── services/api.ts    # API client
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - REST API framework
- **shapely** - Geometry processing
- **ezdxf** - DXF read/write
- **pydantic** - Data validation

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Canvas API** - Floor plan rendering

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or pnpm

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Using Docker

```bash
# Build and run both services
docker-compose up --build
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload DXF file |
| `/api/generate/setback` | POST | Calculate buildable area |
| `/api/generate/floor/{n}` | POST | Generate floor N |
| `/api/export` | POST | Export to DXF |
| `/api/rules/rooms` | GET | Get room catalog |
| `/api/rules/strategies` | GET | Get layout strategies |

## 🎯 Development Phases

- [x] **Phase 1**: Project Setup & DXF Handling
- [ ] **Phase 2**: Setback & Buildable Area
- [ ] **Phase 3**: Zone Allocation
- [ ] **Phase 4**: Room Generation
- [ ] **Phase 5**: Staircase & Circulation
- [ ] **Phase 6**: Layout Scoring
- [ ] **Phase 7**: Multi-Floor Generation
- [ ] **Phase 8**: Amenity Placement
- [ ] **Phase 9**: DXF Export
- [ ] **Phase 10**: Desktop Conversion (PySide6)

## 📝 Usage

1. **Upload**: Drag & drop your plot boundary DXF file
2. **Configure**: Set setbacks, layout strategy, and zone distribution
3. **Generate**: Click to generate floor plans one at a time
4. **Review**: Check scores and room placements
5. **Export**: Download complete DXF with all floors

## 🔧 Configuration

### Environment Variables

Backend (`.env`):
```
DEBUG=true
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["http://localhost:3000"]
```

Frontend (`.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📄 License

MIT License - see LICENSE file for details.
