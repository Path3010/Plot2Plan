"""Quick quality check for the slicing floorplan generator."""
from services.layout_engine.slicing import generate_slicing_candidate, ARCH_ADJACENCY

room_specs = [
    {"room_type": "living",         "target_area": 224},
    {"room_type": "master_bedroom", "target_area": 168},
    {"room_type": "bedroom",        "target_area": 120},
    {"room_type": "kitchen",        "target_area": 80},
    {"room_type": "bathroom",       "target_area": 40},
    {"room_type": "dining",         "target_area": 120},
]

rooms, score = generate_slicing_candidate(
    room_specs, 30.0, 40.0, sa_iterations=800, seed=42
)

print(f"Score: {score:.4f}")
print(f"Rooms: {len(rooms)}")
total_area = 0
for r in rooms:
    p = r["polygon"]
    bx, by, bxx, byy = p.bounds
    w, h = bxx - bx, byy - by
    ar = max(w / h, h / w) if min(w, h) > 0.01 else 99.0
    total_area += p.area
    ta = r["target_area"]
    print(f"  {r['room_type']:20s}  area={p.area:7.1f}  target={ta:7.1f}  dims={w:.1f} x {h:.1f}  AR={ar:.2f}")

coverage = total_area / (30.0 * 40.0)
print(f"\nTotal room area: {total_area:.1f} / {30.0*40.0:.1f}  coverage={coverage:.2%}")
print()

# Now run the full LayoutGenerator pipeline
from shapely.geometry import box
from services.layout_engine import LayoutGenerator

boundary = box(0, 0, 30, 40)
reqs = [
    {"room_type": "living", "size": 15},
    {"room_type": "master_bedroom", "size": 13},
    {"room_type": "bedroom", "size": 11},
    {"room_type": "kitchen", "size": 9},
    {"room_type": "bathroom", "size": 6},
    {"room_type": "dining", "size": 11},
]

gen = LayoutGenerator(
    boundary=boundary,
    room_requirements=reqs,
    desired_adjacencies=ARCH_ADJACENCY,
)
result = gen.generate(n_candidates=100, method="mixed")

print(f"=== LayoutGenerator Results ===")
print(f"Candidates: {result['candidates_generated']} generated, {result['candidates_valid']} valid")
print(f"Best score: {result['score']}")
print(f"Rooms in best layout: {len(result['best_layout'])}")
for r in result["best_layout"]:
    coords = r["polygon"]
    if len(coords) >= 3:
        from shapely.geometry import Polygon
        poly = Polygon(coords)
        bx, by, bxx, byy = poly.bounds
        w, h = bxx - bx, byy - by
        ar = max(w / h, h / w) if min(w, h) > 0.01 else 99.0
        print(f"  {r['room_type']:20s}  area={poly.area:7.1f}  dims={w:.1f} x {h:.1f}  AR={ar:.2f}")
