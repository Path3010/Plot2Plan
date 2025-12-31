"""
DXF Parser Module
Handles parsing of DXF files and extraction of plot boundaries.
"""

from typing import List, Tuple, Optional
from pathlib import Path

import ezdxf
from ezdxf.entities import LWPolyline, Polyline
from shapely.geometry import Polygon, LinearRing
from shapely.validation import make_valid


class DXFParserError(Exception):
    """Exception raised for DXF parsing errors."""
    pass


class DXFParser:
    """
    Parser for DXF files containing plot boundaries.
    
    Extracts closed polygons from LWPOLYLINE and POLYLINE entities
    and converts them to shapely Polygon objects.
    """
    
    SUPPORTED_LAYERS = ["BOUNDARY", "PLOT", "SITE", "0"]
    
    def __init__(self, file_path: str | Path):
        """
        Initialize parser with DXF file path.
        
        Args:
            file_path: Path to the DXF file
        """
        self.file_path = Path(file_path)
        self.doc = None
        self.boundary_polygon: Optional[Polygon] = None
        self.raw_coordinates: List[Tuple[float, float]] = []
        
    def parse(self) -> Polygon:
        """
        Parse the DXF file and extract the plot boundary.
        
        Returns:
            shapely Polygon representing the plot boundary
            
        Raises:
            DXFParserError: If no valid boundary is found
        """
        if not self.file_path.exists():
            raise DXFParserError(f"File not found: {self.file_path}")
        
        try:
            self.doc = ezdxf.readfile(str(self.file_path))
        except Exception as e:
            raise DXFParserError(f"Failed to read DXF file: {e}")
        
        msp = self.doc.modelspace()
        
        # Try to find boundary in preferred layers first
        boundary = self._find_boundary_in_layers(msp, self.SUPPORTED_LAYERS)
        
        if boundary is None:
            # Fall back to finding the largest closed polyline
            boundary = self._find_largest_closed_polyline(msp)
        
        if boundary is None:
            raise DXFParserError("No valid boundary polygon found in DXF file")
        
        self.boundary_polygon = boundary
        return boundary
    
    def _find_boundary_in_layers(self, msp, layers: List[str]) -> Optional[Polygon]:
        """Find boundary polygon in specified layers."""
        for layer in layers:
            # Query LWPOLYLINE entities
            for entity in msp.query(f'LWPOLYLINE[layer=="{layer}"]'):
                polygon = self._lwpolyline_to_polygon(entity)
                if polygon is not None and polygon.is_valid:
                    return polygon
            
            # Query POLYLINE entities (older DXF format)
            for entity in msp.query(f'POLYLINE[layer=="{layer}"]'):
                polygon = self._polyline_to_polygon(entity)
                if polygon is not None and polygon.is_valid:
                    return polygon
        
        return None
    
    def _find_largest_closed_polyline(self, msp) -> Optional[Polygon]:
        """Find the largest closed polyline in the modelspace."""
        largest_polygon = None
        largest_area = 0
        
        for entity in msp.query('LWPOLYLINE'):
            if entity.closed:
                polygon = self._lwpolyline_to_polygon(entity)
                if polygon is not None and polygon.is_valid:
                    if polygon.area > largest_area:
                        largest_area = polygon.area
                        largest_polygon = polygon
        
        for entity in msp.query('POLYLINE'):
            if entity.is_closed:
                polygon = self._polyline_to_polygon(entity)
                if polygon is not None and polygon.is_valid:
                    if polygon.area > largest_area:
                        largest_area = polygon.area
                        largest_polygon = polygon
        
        return largest_polygon
    
    def _lwpolyline_to_polygon(self, entity: LWPolyline) -> Optional[Polygon]:
        """Convert LWPOLYLINE entity to shapely Polygon."""
        try:
            # Get vertices (x, y, start_width, end_width, bulge)
            points = [(p[0], p[1]) for p in entity.get_points()]
            
            if len(points) < 3:
                return None
            
            # Ensure polygon is closed
            if points[0] != points[-1]:
                points.append(points[0])
            
            self.raw_coordinates = points
            
            # Create polygon and validate
            polygon = Polygon(points)
            
            if not polygon.is_valid:
                polygon = make_valid(polygon)
            
            # Ensure counter-clockwise orientation (exterior ring)
            if not LinearRing(points).is_ccw:
                polygon = Polygon(list(reversed(points)))
            
            return polygon
            
        except Exception as e:
            print(f"Warning: Failed to convert LWPOLYLINE: {e}")
            return None
    
    def _polyline_to_polygon(self, entity: Polyline) -> Optional[Polygon]:
        """Convert POLYLINE entity to shapely Polygon."""
        try:
            points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
            
            if len(points) < 3:
                return None
            
            if points[0] != points[-1]:
                points.append(points[0])
            
            self.raw_coordinates = points
            polygon = Polygon(points)
            
            if not polygon.is_valid:
                polygon = make_valid(polygon)
            
            return polygon
            
        except Exception as e:
            print(f"Warning: Failed to convert POLYLINE: {e}")
            return None
    
    def get_boundary_info(self) -> dict:
        """
        Get information about the parsed boundary.
        
        Returns:
            Dictionary with boundary metadata
        """
        if self.boundary_polygon is None:
            raise DXFParserError("No boundary parsed yet. Call parse() first.")
        
        bounds = self.boundary_polygon.bounds  # (minx, miny, maxx, maxy)
        
        return {
            "coordinates": list(self.boundary_polygon.exterior.coords),
            "area_sqm": self.boundary_polygon.area,
            "area_sqft": self.boundary_polygon.area * 10.764,
            "perimeter_m": self.boundary_polygon.length,
            "bounding_box": {
                "min_x": bounds[0],
                "min_y": bounds[1],
                "max_x": bounds[2],
                "max_y": bounds[3],
            },
            "width": bounds[2] - bounds[0],
            "height": bounds[3] - bounds[1],
            "centroid": {
                "x": self.boundary_polygon.centroid.x,
                "y": self.boundary_polygon.centroid.y,
            },
            "is_convex": self.boundary_polygon.convex_hull.equals(self.boundary_polygon),
        }


# Convenience function
def parse_dxf_boundary(file_path: str | Path) -> Tuple[Polygon, dict]:
    """
    Convenience function to parse a DXF file and return boundary polygon and info.
    
    Args:
        file_path: Path to DXF file
        
    Returns:
        Tuple of (Polygon, info_dict)
    """
    parser = DXFParser(file_path)
    polygon = parser.parse()
    info = parser.get_boundary_info()
    return polygon, info
