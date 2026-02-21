"""End-to-end test for Phase 1 — DXF Upload → Boundary Extraction → Buildable Footprint."""

import urllib.request
import json
import os

BASE = "http://127.0.0.1:8000"

# Ensure test DXF exists
DXF_PATH = "uploads/test_boundary.dxf"
if not os.path.exists(DXF_PATH):
    import ezdxf
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (20, 0), (20, 15), (0, 15)], close=True)
    doc.saveas(DXF_PATH)
    print("Created test DXF (20m x 15m)")

# --- Step 1: Upload DXF ---
print("=== Step 1: Upload DXF ===")
with open(DXF_PATH, "rb") as f:
    file_data = f.read()

CRLF = b"\r\n"
BOUNDARY = b"----TestBoundary1234"
body = (
    b"--" + BOUNDARY + CRLF
    + b'Content-Disposition: form-data; name="file"; filename="test.dxf"' + CRLF
    + b"Content-Type: application/octet-stream" + CRLF + CRLF
    + file_data + CRLF
    + b"--" + BOUNDARY + b"--" + CRLF
)

req = urllib.request.Request(
    BASE + "/api/upload-boundary",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY.decode()}"},
    method="POST",
)
resp = urllib.request.urlopen(req)
upload_data = json.loads(resp.read())
print(json.dumps(upload_data, indent=2))
file_id = upload_data["file_id"]
assert upload_data["status"] == "uploaded"
assert upload_data["file_type"] == "dxf"
print("  ✓ Upload succeeded, file_id:", file_id)

# --- Step 2: Extract Boundary ---
print("\n=== Step 2: Extract Boundary ===")
req2 = urllib.request.Request(BASE + f"/api/extract-boundary/{file_id}")
resp2 = urllib.request.urlopen(req2)
extract_data = json.loads(resp2.read())
print(f"  Area: {extract_data['area']}")
print(f"  Vertices: {extract_data['num_vertices']}")
print(f"  Valid: {extract_data['is_valid']}")
print(f"  Closed: {extract_data['is_closed']}")
assert extract_data["area"] == 300.0, f"Expected 300, got {extract_data['area']}"
assert extract_data["num_vertices"] == 4
assert extract_data["is_valid"] is True
print("  ✓ Boundary extracted correctly")

# --- Step 3: Buildable Footprint ---
print("\n=== Step 3: Buildable Footprint (India MVP, 2m setback) ===")
req3 = urllib.request.Request(
    BASE + f"/api/buildable-footprint/{file_id}?region=india_mvp", method="POST"
)
resp3 = urllib.request.urlopen(req3)
fp_data = json.loads(resp3.read())
print(f"  Boundary area: {fp_data['boundary_area']}")
print(f"  Usable area:   {fp_data['usable_area']}")
print(f"  Setback:       {fp_data['setback_applied']}m")
print(f"  Coverage:      {fp_data['coverage_ratio']}")
print(f"  Preview URL:   {fp_data['preview_url']}")
assert fp_data["boundary_area"] == 300.0
assert fp_data["usable_area"] == 176.0  # (20-4)*(15-4) = 16*11 = 176
assert fp_data["setback_applied"] == 2.0
assert fp_data["is_valid"] is True
print("  ✓ Buildable footprint computed correctly")

# --- Step 4: Fetch Preview Image ---
print("\n=== Step 4: Preview Image ===")
req4 = urllib.request.Request(BASE + f"/api/boundary-preview/{file_id}")
resp4 = urllib.request.urlopen(req4)
content_type = resp4.headers.get("content-type", "")
img_bytes = resp4.read()
print(f"  Content-Type: {content_type}")
print(f"  Size: {len(img_bytes)} bytes")
assert "image/png" in content_type
assert len(img_bytes) > 1000  # reasonable PNG size
print("  ✓ Preview image served correctly")

# --- Step 5: Custom setback test ---
print("\n=== Step 5: Custom Setback (3m) ===")
req5 = urllib.request.Request(
    BASE + f"/api/buildable-footprint/{file_id}?setback=3.0", method="POST"
)
resp5 = urllib.request.urlopen(req5)
fp5 = json.loads(resp5.read())
print(f"  Usable area with 3m setback: {fp5['usable_area']}")
assert fp5["usable_area"] == 126.0  # (20-6)*(15-6) = 14*9 = 126
assert fp5["setback_applied"] == 3.0
print("  ✓ Custom setback works correctly")

print("\n" + "=" * 50)
print("*** ALL PHASE 1 TESTS PASSED ***")
print("=" * 50)
