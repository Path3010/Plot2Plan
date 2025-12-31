"""
DXF Exporter Module - Exports floor plans to DXF format with layers.
"""

from typing import List, Dict, Any
from pathlib import Path
import ezdxf
from shapely.geometry import Polygon


# Layer configuration
DXF_LAYERS = {
    "PLOT_BOUNDARY": {"color": 7},
    "SETBACK_LINE": {"color": 8},
    "GF_WALLS": {"color": 1},
    "GF_DOORS": {"color": 3},
    "GF_WINDOWS": {"color": 5},
    "GF_ROOMS": {"color": 7},
    "FF_WALLS": {"color": 1},
    "FF_DOORS": {"color": 3},
    "STAIRCASE": {"color": 6},
    "AMENITIES": {"color": 4},
    "ANNOTATIONS": {"color": 2},
}


class DXFExporter:
    """Exports floor plans to DXF. TODO: Full implementation Phase 9"""
    
    def __init__(self):
        self.doc = None
        self.msp = None
    
    def create_document(self) -> ezdxf.document.Drawing:
        self.doc = ezdxf.new('R2010')
        self.msp = self.doc.modelspace()
        for name, config in DXF_LAYERS.items():
            self.doc.layers.add(name, color=config['color'])
        return self.doc
    
    def add_polygon(self, polygon: Polygon, layer: str):
        if self.msp is None:
            self.create_document()
        coords = list(polygon.exterior.coords)
        self.msp.add_lwpolyline(coords, dxfattribs={'layer': layer})
    
    def add_text(self, text: str, x: float, y: float, layer: str, height: float = 0.3):
        if self.msp is None:
            self.create_document()
        self.msp.add_text(text, dxfattribs={'layer': layer, 'height': height, 'insert': (x, y)})
    
    def save(self, path: str):
        if self.doc:
            self.doc.saveas(path)
    
    def export_project(self, project: Dict[str, Any], output_path: str):
        self.create_document()
        if 'boundary' in project:
            self.add_polygon(Polygon(project['boundary']), 'PLOT_BOUNDARY')
        self.save(output_path)
        return output_path
