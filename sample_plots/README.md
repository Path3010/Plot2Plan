# Sample Plot DXF Files

This directory contains sample plot boundary DXF files for testing the Floor Plan Generator.

## Generating Sample DXF Files

You can create sample DXF files using this Python script:

```python
import ezdxf

def create_sample_plot(filename, points, layer="BOUNDARY"):
    """Create a sample plot DXF file."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create boundary layer
    doc.layers.add(layer, color=7)
    
    # Add closed polyline
    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': layer})
    
    doc.saveas(filename)
    print(f"Created: {filename}")

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
```

## Sample Files

| File | Description | Area |
|------|-------------|------|
| `rectangular_15x20.dxf` | Standard rectangular plot | 300 m² |
| `l_shaped.dxf` | L-shaped corner plot | ~340 m² |
| `irregular.dxf` | Irregular polygon plot | ~350 m² |
