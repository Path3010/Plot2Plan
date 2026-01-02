"""
Generate sample DXF plot files for testing.
Run: python create_samples.py

Includes various shapes:
- Rectangular, L-shaped, irregular, square, wide plots
- Doughnut shape (with inner hole/courtyard)
- Validation test files (self-intersecting, tiny, huge, etc.)
"""

import ezdxf
import math


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


def create_self_intersecting_plot(filename: str, points: list, layer: str = "BOUNDARY"):
    """
    Create a self-intersecting polygon (figure-8 / bowtie shape).
    This is used to test validation - it should fail the simplicity check.
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    doc.layers.add(layer, color=7)
    
    # Add closed polyline - the crossing happens automatically
    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': layer})
    
    doc.saveas(filename)
    print(f"Created: {filename} (self-intersecting - should fail validation)")


def create_unclosed_plot(filename: str, points: list, layer: str = "BOUNDARY"):
    """
    Create a plot with an UNCLOSED polyline (not marked as closed).
    This is used to test the parser's ability to handle and auto-close unclosed boundaries.
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    doc.layers.add(layer, color=7)
    
    # Add polyline WITHOUT close=True (unclosed)
    msp.add_lwpolyline(points, close=False, dxfattribs={'layer': layer})
    
    doc.saveas(filename)
    print(f"Created: {filename} (UNCLOSED polyline - should trigger warning)")


def create_star_polygon(
    filename: str,
    outer_radius: float = 15,
    inner_radius: float = 7,
    num_points: int = 5,
    layer: str = "BOUNDARY"
):
    """
    Create a star-shaped polygon.
    
    Args:
        filename: Output DXF filename
        outer_radius: Radius of outer points
        inner_radius: Radius of inner points
        num_points: Number of star points
        layer: Layer name
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    doc.layers.add(layer, color=7)
    
    # Generate star points alternating between outer and inner radius
    points = []
    angle_step = 360 / (num_points * 2)
    
    for i in range(num_points * 2):
        angle = math.radians(i * angle_step - 90)  # Start from top
        radius = outer_radius if i % 2 == 0 else inner_radius
        x = radius * math.cos(angle) + outer_radius  # Offset to positive coords
        y = radius * math.sin(angle) + outer_radius
        points.append((x, y))
    
    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': layer})
    
    doc.saveas(filename)
    print(f"Created: {filename} (star shape with {num_points} points)")


# ============================================================================
# Main Script
# ============================================================================

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
    
    # ========================================
    # Validation Test Cases
    # ========================================
    print("\n--- Creating Validation Test Files ---")
    
    # Test 1: Self-intersecting polygon (figure-8 / bowtie shape)
    # This should FAIL validation (is_simple = false)
    create_self_intersecting_plot(
        "validation_test_self_intersecting.dxf",
        # Bowtie shape - lines cross in the middle
        points=[(0, 0), (10, 10), (0, 10), (10, 0)]
    )
    
    # Test 2: Clockwise oriented polygon
    # This should trigger WARNING (orientation = cw, should be ccw)
    create_sample_plot(
        "validation_test_clockwise.dxf",
        # Clockwise rectangle (reverse order)
        points=[(0, 0), (0, 15), (20, 15), (20, 0)]
    )
    
    # Test 3: Extreme aspect ratio (very narrow)
    # This should trigger WARNING (extreme aspect ratio)
    create_sample_plot(
        "validation_test_narrow.dxf",
        # Very narrow: 50m x 2m = aspect ratio of 25
        points=[(0, 0), (50, 0), (50, 2), (0, 2)]
    )
    
    # Test 4: Very small area
    # This should trigger WARNING (area too small)
    create_sample_plot(
        "validation_test_tiny.dxf",
        # Tiny: 0.5m x 0.5m = 0.25 sqm (below 1.0 threshold)
        points=[(0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5)]
    )
    
    # Test 5: Concave polygon (L-shape is concave)
    # This should show is_convex = false (INFO, not error)
    create_sample_plot(
        "validation_test_concave.dxf",
        # Concave L-shape
        points=[(0, 0), (15, 0), (15, 10), (5, 10), (5, 20), (0, 20)]
    )
    
    # Test 6: Very large area
    # This should trigger WARNING (area too large)
    create_sample_plot(
        "validation_test_huge.dxf",
        # Huge: 500m x 500m = 250,000 sqm (above 100,000 threshold)
        points=[(0, 0), (500, 0), (500, 500), (0, 500)]
    )
    
    # Test 7: Triangle (minimum vertices)
    # This should pass (3 vertices is minimum)
    create_sample_plot(
        "validation_test_triangle.dxf",
        points=[(0, 0), (20, 0), (10, 15)]
    )
    
    # Test 8: Complex polygon with many vertices
    # Creates a star shape
    create_star_polygon(
        "validation_test_star.dxf",
        outer_radius=15,
        inner_radius=7,
        num_points=6
    )
    
    # Test 9: Unclosed boundary
    # This should trigger WARNING (unclosed polyline - will be auto-closed)
    create_unclosed_plot(
        "validation_test_unclosed.dxf",
        # Rectangle but NOT closed in DXF
        points=[(0, 0), (20, 0), (20, 15), (0, 15)]
    )
    
    # Test 10: Unclosed L-shape
    # More complex unclosed shape
    create_unclosed_plot(
        "validation_test_unclosed_lshape.dxf",
        points=[(0, 0), (18, 0), (18, 10), (8, 10), (8, 18), (0, 18)]
    )
    
    # ========================================
    # Summary
    # ========================================
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
    print("\nValidation test files:")
    print("  - validation_test_self_intersecting.dxf (should FAIL - self-intersection)")
    print("  - validation_test_clockwise.dxf (should WARN - wrong orientation)")
    print("  - validation_test_narrow.dxf (should WARN - extreme aspect ratio)")
    print("  - validation_test_tiny.dxf (should WARN - area too small)")
    print("  - validation_test_concave.dxf (should show is_convex=false)")
    print("  - validation_test_huge.dxf (should WARN - area too large)")
    print("  - validation_test_triangle.dxf (minimum 3 vertices)")
    print("  - validation_test_star.dxf (complex shape with many vertices)")
    print("  - validation_test_unclosed.dxf (should WARN - unclosed boundary)")
    print("  - validation_test_unclosed_lshape.dxf (should WARN - unclosed L-shape)")

