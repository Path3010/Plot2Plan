"""
Generate sample DXF plot files for testing.
Run: python create_samples.py

Includes various shapes:
- Rectangular, L-shaped, irregular, square, wide plots
- Doughnut shape (with inner hole/courtyard)
"""

import ezdxf


def create_sample_plot(filename: str, points: list, layer: str = "BOUNDARY"):
    """Create a sample plot DXF file with a single boundary."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create boundary layer
    doc.layers.add(layer, color=7)
    
    # Add closed polyline
    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': layer})
    
    doc.saveas(filename)
    print(f"Created: {filename}")


def create_doughnut_plot(
    filename: str, 
    outer_points: list, 
    inner_points: list,
    outer_layer: str = "BOUNDARY",
    inner_layer: str = "HOLE"
):
    """
    Create a doughnut-shaped plot DXF file with an inner hole/courtyard.
    
    Args:
        filename: Output DXF filename
        outer_points: Points defining the outer boundary
        inner_points: Points defining the inner hole (courtyard)
        outer_layer: Layer name for outer boundary
        inner_layer: Layer name for inner hole
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create layers with different colors
    doc.layers.add(outer_layer, color=7)  # White for boundary
    doc.layers.add(inner_layer, color=1)  # Red for hole
    
    # Add outer boundary (plot perimeter)
    msp.add_lwpolyline(outer_points, close=True, dxfattribs={'layer': outer_layer})
    
    # Add inner hole (courtyard/void)
    msp.add_lwpolyline(inner_points, close=True, dxfattribs={'layer': inner_layer})
    
    doc.saveas(filename)
    print(f"Created: {filename} (doughnut with hole)")


def create_plot_with_multiple_holes(
    filename: str,
    outer_points: list,
    holes: list,
    outer_layer: str = "BOUNDARY",
    hole_layer: str = "HOLE"
):
    """
    Create a plot with multiple inner holes.
    
    Args:
        filename: Output DXF filename
        outer_points: Points defining the outer boundary
        holes: List of point lists, each defining a hole
        outer_layer: Layer name for outer boundary
        hole_layer: Layer name for holes
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create layers
    doc.layers.add(outer_layer, color=7)
    doc.layers.add(hole_layer, color=1)
    
    # Add outer boundary
    msp.add_lwpolyline(outer_points, close=True, dxfattribs={'layer': outer_layer})
    
    # Add holes
    for hole_points in holes:
        msp.add_lwpolyline(hole_points, close=True, dxfattribs={'layer': hole_layer})
    
    doc.saveas(filename)
    print(f"Created: {filename} (with {len(holes)} hole(s))")


if __name__ == "__main__":
    # ========================================
    # Basic Shapes (no holes)
    # ========================================
    
    # Rectangular plot: 15m x 20m
    create_sample_plot(
        "rectangular_15x20.dxf",
        [(0, 0), (15, 0), (15, 20), (0, 20)]
    )
    
    # L-shaped plot
    create_sample_plot(
        "l_shaped.dxf",
        [(0, 0), (20, 0), (20, 12), (12, 12), (12, 20), (0, 20)]
    )
    
    # Irregular plot
    create_sample_plot(
        "irregular.dxf",
        [(0, 0), (18, 2), (20, 15), (15, 22), (5, 20), (-2, 10)]
    )
    
    # Square plot: 18m x 18m
    create_sample_plot(
        "square_18x18.dxf",
        [(0, 0), (18, 0), (18, 18), (0, 18)]
    )
    
    # Wide rectangular: 25m x 12m
    create_sample_plot(
        "wide_25x12.dxf",
        [(0, 0), (25, 0), (25, 12), (0, 12)]
    )
    
    # ========================================
    # Shapes with Holes (Nested Boundaries)
    # ========================================
    
    # Doughnut shape: 20m x 20m outer, 8m x 8m inner courtyard
    create_doughnut_plot(
        "doughnut_courtyard.dxf",
        outer_points=[(0, 0), (20, 0), (20, 20), (0, 20)],
        inner_points=[(6, 6), (14, 6), (14, 14), (6, 14)]  # 8x8m courtyard in center
    )
    
    # Rectangular with small courtyard: 18m x 24m with 4m x 6m hole
    create_doughnut_plot(
        "rectangular_with_courtyard.dxf",
        outer_points=[(0, 0), (18, 0), (18, 24), (0, 24)],
        inner_points=[(7, 9), (11, 9), (11, 15), (7, 15)]  # 4x6m courtyard
    )
    
    # U-shaped plot (simulated with large rectangular hole on one side)
    # Creates a U-shape by having a rectangular hole at the top
    create_doughnut_plot(
        "u_shaped.dxf",
        outer_points=[(0, 0), (20, 0), (20, 18), (0, 18)],
        inner_points=[(5, 8), (15, 8), (15, 18), (5, 18)]  # Top section removed
    )
    
    # Large plot with multiple courtyards (2 holes)
    create_plot_with_multiple_holes(
        "twin_courtyards.dxf",
        outer_points=[(0, 0), (30, 0), (30, 20), (0, 20)],
        holes=[
            [(4, 5), (11, 5), (11, 15), (4, 15)],   # Left courtyard
            [(19, 5), (26, 5), (26, 15), (19, 15)]  # Right courtyard
        ]
    )
    
    # Complex shape: Hexagonal outer with square hole
    import math
    hex_radius = 12
    hex_points = [
        (hex_radius * math.cos(math.radians(angle)), hex_radius * math.sin(math.radians(angle)))
        for angle in range(0, 360, 60)
    ]
    # Offset to positive coordinates
    hex_offset = [(p[0] + 15, p[1] + 15) for p in hex_points]
    
    create_doughnut_plot(
        "hexagon_with_courtyard.dxf",
        outer_points=hex_offset,
        inner_points=[(12, 12), (18, 12), (18, 18), (12, 18)]  # 6x6m square courtyard
    )
    
    print("\n" + "=" * 50)
    print("All sample DXF files created successfully!")
    print("=" * 50)
    print("\nBasic shapes (no holes):")
    print("  - rectangular_15x20.dxf")
    print("  - l_shaped.dxf")
    print("  - irregular.dxf")
    print("  - square_18x18.dxf")
    print("  - wide_25x12.dxf")
    print("\nShapes with holes:")
    print("  - doughnut_courtyard.dxf (square with central courtyard)")
    print("  - rectangular_with_courtyard.dxf")
    print("  - u_shaped.dxf (U-shape via hole)")
    print("  - twin_courtyards.dxf (2 internal courtyards)")
    print("  - hexagon_with_courtyard.dxf (hexagonal with square hole)")
