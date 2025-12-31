"""
Generate sample DXF plot files for testing.
Run: python create_samples.py
"""

import ezdxf


def create_sample_plot(filename: str, points: list, layer: str = "BOUNDARY"):
    """Create a sample plot DXF file."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create boundary layer
    doc.layers.add(layer, color=7)
    
    # Add closed polyline
    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': layer})
    
    doc.saveas(filename)
    print(f"Created: {filename}")


if __name__ == "__main__":
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
    
    print("\nAll sample DXF files created successfully!")
