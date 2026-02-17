"""
3D Model Generation.

Extrudes 2D floor plan walls to 3D, adds roof, exports as glTF.
"""

import trimesh
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from pathlib import Path


WALL_HEIGHT = 10.0  # feet
WALL_THICKNESS = 0.5  # feet


def _polygon_to_3d_extrusion(coords: list, height: float, z_base: float = 0.0) -> trimesh.Trimesh:
    """Extrude a 2D polygon to a 3D solid."""
    if not coords or len(coords) < 3:
        return trimesh.Trimesh()

    try:
        poly = Polygon(coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if isinstance(poly, MultiPolygon):
            poly = max(poly.geoms, key=lambda g: g.area)
        if poly.is_empty or poly.area < 0.1:
            return trimesh.Trimesh()

        # Create extrusion
        mesh = trimesh.creation.extrude_polygon(poly, height)

        # Translate to z_base
        if z_base != 0.0:
            mesh.apply_translation([0, 0, z_base])

        return mesh
    except Exception:
        return trimesh.Trimesh()


def _create_wall_mesh(room_coords: list, height: float = WALL_HEIGHT) -> trimesh.Trimesh:
    """Create 3D wall mesh from a room polygon by extruding its boundary."""
    if not room_coords or len(room_coords) < 3:
        return trimesh.Trimesh()

    try:
        poly = Polygon(room_coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if isinstance(poly, MultiPolygon):
            poly = max(poly.geoms, key=lambda g: g.area)

        # Create wall profile: buffer the boundary
        wall_profile = poly.boundary.buffer(WALL_THICKNESS / 2)

        if wall_profile.is_empty:
            return trimesh.Trimesh()

        if isinstance(wall_profile, MultiPolygon):
            meshes = []
            for geom in wall_profile.geoms:
                if geom.area > 0.1:
                    mesh = trimesh.creation.extrude_polygon(geom, height)
                    meshes.append(mesh)
            if meshes:
                return trimesh.util.concatenate(meshes)
            return trimesh.Trimesh()

        mesh = trimesh.creation.extrude_polygon(wall_profile, height)
        return mesh
    except Exception:
        return trimesh.Trimesh()


def _create_floor(boundary_coords: list) -> trimesh.Trimesh:
    """Create a flat floor from boundary polygon."""
    if not boundary_coords or len(boundary_coords) < 3:
        return trimesh.Trimesh()

    try:
        poly = Polygon(boundary_coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if isinstance(poly, MultiPolygon):
            poly = max(poly.geoms, key=lambda g: g.area)

        # Thin extrusion for the floor
        mesh = trimesh.creation.extrude_polygon(poly, 0.5)
        mesh.apply_translation([0, 0, -0.5])
        return mesh
    except Exception:
        return trimesh.Trimesh()


def _create_roof(boundary_coords: list, height: float = WALL_HEIGHT) -> trimesh.Trimesh:
    """Create a flat roof from boundary polygon at wall height."""
    if not boundary_coords or len(boundary_coords) < 3:
        return trimesh.Trimesh()

    try:
        poly = Polygon(boundary_coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if isinstance(poly, MultiPolygon):
            poly = max(poly.geoms, key=lambda g: g.area)

        mesh = trimesh.creation.extrude_polygon(poly, 0.3)
        mesh.apply_translation([0, 0, height])
        return mesh
    except Exception:
        return trimesh.Trimesh()


def generate_3d_model(plan: dict, output_path: str) -> str:
    """
    Generate a 3D model (glTF) from floor plan data.

    Args:
        plan: Dict with 'boundary', 'rooms', 'walls', 'doors', 'windows'.
        output_path: Path to save the glTF file.

    Returns:
        Path to the generated file.
    """
    meshes = []

    boundary = plan.get("boundary", [])

    # Create floor
    floor = _create_floor(boundary)
    if floor.vertices.shape[0] > 0:
        floor.visual = trimesh.visual.ColorVisuals(
            mesh=floor,
            face_colors=[200, 200, 200, 255],
        )
        meshes.append(floor)

    # Create outer boundary walls
    outer_walls = _create_wall_mesh(boundary)
    if outer_walls.vertices.shape[0] > 0:
        outer_walls.visual = trimesh.visual.ColorVisuals(
            mesh=outer_walls,
            face_colors=[220, 220, 220, 255],
        )
        meshes.append(outer_walls)

    # Create room walls
    room_colors = {
        "living": [180, 220, 240, 255],
        "master_bedroom": [240, 200, 180, 255],
        "bedroom": [220, 210, 190, 255],
        "kitchen": [200, 240, 200, 255],
        "bathroom": [190, 210, 240, 255],
        "dining": [240, 230, 200, 255],
        "study": [210, 200, 230, 255],
        "hallway": [230, 230, 230, 255],
    }

    for room in plan.get("rooms", []):
        polygon = room.get("polygon", [])
        if polygon and len(polygon) >= 3:
            wall_mesh = _create_wall_mesh(polygon, WALL_HEIGHT * 0.9)
            if wall_mesh.vertices.shape[0] > 0:
                color = room_colors.get(room.get("room_type", ""), [200, 200, 200, 255])
                wall_mesh.visual = trimesh.visual.ColorVisuals(
                    mesh=wall_mesh,
                    face_colors=color,
                )
                meshes.append(wall_mesh)

    # Create roof
    roof = _create_roof(boundary)
    if roof.vertices.shape[0] > 0:
        roof.visual = trimesh.visual.ColorVisuals(
            mesh=roof,
            face_colors=[180, 160, 140, 255],
        )
        meshes.append(roof)

    if not meshes:
        raise ValueError("No valid geometry could be generated for 3D model.")

    # Combine all meshes
    scene = trimesh.Scene(meshes)

    # Export
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if output_path.endswith(".glb") or output_path.endswith(".gltf"):
        scene.export(output_path, file_type="glb")
    elif output_path.endswith(".obj"):
        scene.export(output_path, file_type="obj")
    else:
        output_path = output_path + ".glb"
        scene.export(output_path, file_type="glb")

    return output_path
