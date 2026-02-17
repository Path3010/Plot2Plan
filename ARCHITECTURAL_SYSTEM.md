# Professional Residential Architect & Structural Planner

## Overview
Complete CAD floor plan generation system implementing professional Indian residential architectural and structural engineering principles.

## System Features

### 1. **Professional Plot Analysis**
- Identifies road-facing side (longest edge) for entry placement
- Analyzes corner types (narrow/wide) for optimal room placement
- Calculates structural grid feasibility (10-15 ft column spacing)
- Detects cross-ventilation opportunities (opposite walls)
- Determines parking feasibility along plot boundary

### 2. **Zoning Logic (Indian Residential Standards)**

**Public Zone** (Near Entry):
- Parking: 10×18 ft (road-facing, near entry)
- Porch: 10×8 ft (entrance vestibule)
- Living Room: 14×16 ft (center, maximum frontage)

**Semi-Private Zone** (Transitional):
- Dining Room: 10×12 ft (adjacent to living, open plan feel)

**Private Zone** (Quiet Corners):
- Master Bedroom: 12×14 ft (with attached 5×8 ft bathroom)
- Bedroom: 10×12 ft (natural light, away from public)
- Study: 10×10 ft (quiet corner)
- Pooja Room: 5×5 ft (preferably NE corner - Vastu)

**Service Zone** (Outer Walls):
- Kitchen: 8×10 ft (near dining, outer wall for exhaust)
- Utility: 4×6 ft (adjacent to kitchen, shared plumbing)
- Bathroom/Toilet: 5×8 ft or 4×6 ft (stacked vertically for plumbing efficiency)
- Store Room: 6×6 ft (narrow corners, minimal light needed)

**Circulation/Future**:
- Staircase: 5×10 ft (central spine, future expansion)
- Corridor: 3.5 ft width minimum

### 3. **Placement Order (Architectural Logic)**
System places rooms in professional architectural sequence:

1. **Parking** → Road-facing, near entry
2. **Porch** → Main entrance, 3 ft inside from entry point
3. **Living Room** → Central, 10 ft inside from porch, maximum daylight
4. **Dining Room** → Adjacent to living (side-by-side or back-to-back)
5. **Kitchen** → Near dining, outer wall for exhaust
6. **Utility** → Adjacent to kitchen, shared plumbing wall
7. **Master Bedroom** → Private corner, opposite side from entry
8. **Bedroom** → Adjacent to master (with separation for privacy)
9. **Study** → Quietest corner, away from entry and kitchen
10. **Bathroom** → Attached to master bedroom OR stacked in service core
11. **Toilet** → Service core, vertically aligned with kitchen for plumbing
12. **Staircase** → Central circulation, structural core
13. **Pooja** → NE corner (Vastu), quiet space
14. **Store** → Narrow/awkward corners, leftover space

### 4. **Structural Engineering Standards**

**Wall Thickness (Indian Building Code):**
- Exterior walls: 230 mm (9 inches) - Load-bearing
- Interior partitions: 115 mm (4.5 inches)
- Beam width: 0.75 ft

**Structural Grid:**
- Column spacing: 10-15 feet for cost-effective construction
- Plumbing stack: Toilets, bathrooms, kitchen aligned vertically
- Beam alignment: Straight runs minimize costs

### 5. **Circulation & Ventilation**

**Movement Flow:**
- Entry → Porch → Living → Dining → Bedrooms
- No dead-end corridors
- Direct paths to all major rooms
- Service core accessible without crossing private zone

**Cross-Ventilation:**
- Windows placed on opposite walls
- All habitable rooms (living, bedrooms, kitchen) have outer wall exposure
- Service rooms (kitchen, toilets) on outer walls for exhaust
- Minimum 3.5 ft corridor width for comfortable circulation

### 6. **CAD Export Features**

**Drawing Elements:**
- Double-line walls with proper thickness (230mm/115mm)
- Door swings with 90° arc representation and hinge points
- Window symbols with frame and sill details
- Furniture blocks for scale reference (beds, counters, toilets, sinks)
- Dimension lines in millimeters (Indian standard)

**Annotations:**
- Room labels with sizes in sq.ft and sq.m
- Wall dimensions with extension lines
- North arrow with circle (architectural convention)
- Professional title block with:
  - Built-up area in sq.ft and sq.m
  - Room count (excluding service spaces)
  - Compliance note: Indian Building Code
  - Wall thickness specifications
  - Scale: 1:100

**Layer Organization:**
- BOUNDARY (white/gray, lineweight 70)
- WALLS (black, lineweight 50)
- WALL_INNER (gray, lineweight 25) - Inner line for double-line effect
- DOORS (green, lineweight 30)
- WINDOWS (blue, lineweight 30)
- FURNITURE (gray, lineweight 25)
- DIMENSIONS (magenta, lineweight 10)
- LABELS (red, text)

## API Usage

### Generate Floor Plan
```
POST /api/floorplan/generate
Content-Type: application/json

{
  "boundary_polygon": [[x1, y1], [x2, y2], ...],
  "rooms": [
    {"room_type": "living", "quantity": 1},
    {"room_type": "master_bedroom", "quantity": 1},
    {"room_type": "bedroom", "quantity": 2},
    {"room_type": "kitchen", "quantity": 1},
    {"room_type": "bathroom", "quantity": 1},
    {"room_type": "toilet", "quantity": 1}
  ],
  "total_area": 1500  // optional, in sq.ft
}
```

### Response Includes:
- `rooms`: Array of placed rooms with polygons, areas, labels
- `walls`: Double-line wall segments with thickness
- `doors`: Door positions with swing arcs
- `windows`: Window positions with frames
- `furniture`: Furniture symbols (beds, counters, etc.)
- `dimensions`: Wall dimension annotations
- `design_thinking`: Architectural analysis metadata
  - `approach`: "Professional Residential Architect + Structural Engineer"
  - `plot_analysis`: Plot dimensions, type, structural feasibility
  - `parking_provided`: Boolean
  - `zones_used`: List of zones (public/private/service)
  - `placement_order`: Room placement sequence
  - `rooms_placed`: Success rate

### Export to DXF
```
POST /api/floorplan/export
Content-Type: application/json

{
  "floor_plan": { /* floor plan data from generate endpoint */ },
  "project_id": "uuid"
}
```

Returns DXF file for download - compatible with AutoCAD, BricsCAD, LibreCAD, etc.

## Design Principles Summary

1. **Entry from longest edge** (road-facing)
2. **Public spaces near entry** (living, porch)
3. **Service core on outer walls** (kitchen, toilets) for plumbing
4. **Private bedrooms at quiet corners** (away from road noise)
5. **Living room gets maximum frontage** (14×16 ft on longest wall)
6. **Dining connects living and kitchen** (transition space)
7. **Toilets stacked vertically** (plumbing efficiency)
8. **Master bedroom opposite from entry** (privacy)
9. **Pooja in quiet corner** (preferably NE - Vastu)
10. **Store/utility in narrow corners** (minimal light needed)
11. **Staircase in central spine** (efficient circulation, future expansion)
12. **3.5 ft corridors minimum** (comfortable circulation)
13. **Cross-ventilation planned** (windows on opposite walls)
14. **Structural column grid** (10-15 ft spacing)

## Benefits

✅ **Realistic Construction Plans** - Follows real architectural logic, not random room placement  
✅ **Indian Building Code Compliance** - Wall thickness, room sizes, structural standards  
✅ **Structural Feasibility** - Column grid, plumbing stack, beam alignment considered  
✅ **Comfortable Living** - Proper zoning, privacy, ventilation, circulation  
✅ **Cost-Effective** - Plumbing stacked, straight beam runs, efficient material use  
✅ **Professional CAD Output** - Ready for contractor/architect review  
✅ **Vastu-Friendly** - Pooja placement, entry considerations  

## Example Request

```python
import requests

response = requests.post('http://localhost:8000/api/floorplan/generate', json={
    "boundary_polygon": [
        [0, 0], [60, 0], [60, 40], [0, 40], [0, 0]
    ],
    "rooms": [
        {"room_type": "living", "quantity": 1},
        {"room_type": "dining", "quantity": 1},
        {"room_type": "kitchen", "quantity": 1},
        {"room_type": "master_bedroom", "quantity": 1},
        {"room_type": "bedroom", "quantity": 2},
        {"room_type": "bathroom", "quantity": 1},
        {"room_type": "toilet", "quantity": 1},
        {"room_type": "porch", "quantity": 1},
        {"room_type": "parking", "quantity": 1}
    ],
    "total_area": 2400  # sq.ft
})

floor_plan = response.json()
print(f"Generated {len(floor_plan['rooms'])} rooms")
print(f"Design approach: {floor_plan['design_thinking']['approach']}")
```

---

**Built with:** FastAPI, Shapely, ezdxf, OpenCV  
**Standards:** Indian Building Code, Professional Architectural Practice  
**Author:** NakshaNirman (CAD Floor Plan Generator)
