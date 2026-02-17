"""
CAD File Generation using ezdxf.

Generates DXF files with proper layers: WALLS, DOORS, WINDOWS, ROOMS.
"""

import ezdxf
from ezdxf.enums import TextEntityAlignment
from pathlib import Path
import math


def generate_dxf(plan: dict, output_path: str) -> str:
    """
    Generate a DXF file from the floor plan data.

    Args:
        plan: Dict containing 'boundary', 'rooms', 'walls', 'doors', 'windows'.
        output_path: Path to save the DXF file.

    Returns:
        Path to the generated DXF file.
    """
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Create layers
    doc.layers.add("BOUNDARY", color=7)  # White
    doc.layers.add("WALLS", color=1)      # Red
    doc.layers.add("DOORS", color=3)      # Green
    doc.layers.add("WINDOWS", color=5)    # Blue
    doc.layers.add("ROOMS", color=2)      # Yellow
    doc.layers.add("DIMENSIONS", color=6) # Magenta
    doc.layers.add("LABELS", color=4)     # Cyan

    # Draw boundary
    boundary = plan.get("boundary", [])
    if boundary and len(boundary) >= 3:
        msp.add_lwpolyline(
            [(p[0], p[1]) for p in boundary],
            close=True,
            dxfattribs={"layer": "BOUNDARY", "lineweight": 50},
        )

    # Draw rooms
    for room in plan.get("rooms", []):
        polygon = room.get("polygon", [])
        if polygon and len(polygon) >= 3:
            # Draw room outline
            msp.add_lwpolyline(
                [(p[0], p[1]) for p in polygon],
                close=True,
                dxfattribs={"layer": "WALLS", "lineweight": 35},
            )

            # Add room label
            centroid = room.get("centroid", [0, 0])
            label = room.get("label", "")
            area = room.get("actual_area", 0)

            msp.add_text(
                label,
                height=1.5,
                dxfattribs={
                    "layer": "LABELS",
                    "insert": (centroid[0], centroid[1] + 1),
                },
            ).set_placement(
                (centroid[0], centroid[1] + 1),
                align=TextEntityAlignment.MIDDLE_CENTER,
            )

            # Add area text
            msp.add_text(
                f"{area:.0f} sq ft",
                height=1.0,
                dxfattribs={
                    "layer": "LABELS",
                    "insert": (centroid[0], centroid[1] - 1.5),
                },
            ).set_placement(
                (centroid[0], centroid[1] - 1.5),
                align=TextEntityAlignment.MIDDLE_CENTER,
            )

    # Draw doors
    for door in plan.get("doors", []):
        pos = door.get("position", [0, 0])
        width = door.get("width", 3.0)

        # Draw door as an arc (opening sweep)
        msp.add_arc(
            center=(pos[0], pos[1]),
            radius=width / 2,
            start_angle=0,
            end_angle=90,
            dxfattribs={"layer": "DOORS"},
        )

        # Draw door line
        msp.add_line(
            start=(pos[0], pos[1]),
            end=(pos[0] + width / 2, pos[1]),
            dxfattribs={"layer": "DOORS"},
        )

    # Draw windows
    for window in plan.get("windows", []):
        pos = window.get("position", [0, 0])
        width = window.get("width", 3.0)

        # Draw window as a double line
        hw = width / 2
        msp.add_line(
            start=(pos[0] - hw, pos[1] - 0.25),
            end=(pos[0] + hw, pos[1] - 0.25),
            dxfattribs={"layer": "WINDOWS", "lineweight": 25},
        )
        msp.add_line(
            start=(pos[0] - hw, pos[1] + 0.25),
            end=(pos[0] + hw, pos[1] + 0.25),
            dxfattribs={"layer": "WINDOWS", "lineweight": 25},
        )

    # Add title block
    boundary_coords = plan.get("boundary", [])
    if boundary_coords:
        min_x = min(p[0] for p in boundary_coords)
        max_y = max(p[1] for p in boundary_coords)
        msp.add_text(
            "FLOOR PLAN",
            height=3.0,
            dxfattribs={
                "layer": "LABELS",
                "insert": (min_x, max_y + 10),
            },
        )
        msp.add_text(
            f"Total Area: {plan.get('total_area', 0):.0f} sq ft",
            height=1.5,
            dxfattribs={
                "layer": "LABELS",
                "insert": (min_x, max_y + 5),
            },
        )

    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(output_path)
    return output_path
