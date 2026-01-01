"""
DXF Parser Module
Handles parsing of DXF files and extraction of plot boundaries.
Supports nested boundaries (holes/cutouts) for complex plot shapes.
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
    
    Supports nested boundaries (holes) - the largest polygon becomes
    the exterior boundary, and smaller polygons inside it become holes.
    """
    
    SUPPORTED_LAYERS = ["BOUNDARY", "PLOT", "SITE", "0"]
    HOLE_LAYERS = ["HOLE", "CUTOUT", "INNER", "VOID"]
    
    def __init__(self, file_path: str | Path):
        """
        Initialize parser with DXF file path.
        
        Args:
            file_path: Path to the DXF file
        """
        self.file_path = Path(file_path)
        self.doc = None
        self.boundary_polygon: Optional[Polygon] = None
        self.exterior_coords: List[Tuple[float, float]] = []
        self.holes: List[List[Tuple[float, float]]] = []
        
    def parse(self) -> Polygon:
        """
        Parse the DXF file and extract the plot boundary with holes.
        
        Returns:
            shapely Polygon representing the plot boundary (with holes if any)
            
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
        
        # Collect all closed polylines
        all_polygons = self._collect_all_polygons(msp)
        
        if not all_polygons:
            raise DXFParserError("No valid boundary polygon found in DXF file")
        
        # Build polygon with holes
        boundary = self._build_polygon_with_holes(all_polygons)
        
        if boundary is None:
            raise DXFParserError("Failed to build valid boundary polygon")
        
        self.boundary_polygon = boundary
        return boundary
    
    def _collect_all_polygons(self, msp) -> List[Tuple[Polygon, str]]:
        """
        Collect all closed polylines and convert them to polygons.
        Returns list of (polygon, layer_name) tuples.
        """
        polygons = []
        
        # Collect LWPOLYLINE entities
        for entity in msp.query('LWPOLYLINE'):
            if entity.closed:
                polygon = self._lwpolyline_to_polygon(entity)
                if polygon is not None and polygon.is_valid and polygon.area > 0.1:
                    layer = entity.dxf.layer.upper() if entity.dxf.layer else "0"
                    polygons.append((polygon, layer))
        
        # Collect POLYLINE entities (older DXF format)
        for entity in msp.query('POLYLINE'):
            if entity.is_closed:
                polygon = self._polyline_to_polygon(entity)
                if polygon is not None and polygon.is_valid and polygon.area > 0.1:
                    layer = entity.dxf.layer.upper() if entity.dxf.layer else "0"
                    polygons.append((polygon, layer))
        
        return polygons
    
    def _build_polygon_with_holes(self, polygons: List[Tuple[Polygon, str]]) -> Optional[Polygon]:
        """
        Build a polygon with holes from a list of polygons.
        
        Logic:
        1. Find the largest polygon (exterior boundary)
        2. Find all smaller polygons that are inside the exterior
        3. These become holes
        """
        if not polygons:
            return None
        
        # Sort by area (largest first)
        polygons.sort(key=lambda x: x[0].area, reverse=True)
        
        # The largest polygon is the exterior
        exterior_polygon, exterior_layer = polygons[0]
        exterior_coords = list(exterior_polygon.exterior.coords)
        self.exterior_coords = exterior_coords
        
        # Find holes - smaller polygons that are inside the exterior
        holes = []
        for polygon, layer in polygons[1:]:
            # Check if this polygon is inside the exterior
            if exterior_polygon.contains(polygon) or layer in self.HOLE_LAYERS:
                # This is a hole
                hole_coords = list(polygon.exterior.coords)
                # Ensure hole has opposite orientation (clockwise for holes)
                ring = LinearRing(hole_coords)
                if ring.is_ccw:
                    hole_coords = list(reversed(hole_coords))
                holes.append(hole_coords)
                self.holes.append(hole_coords)
        
        # Create polygon with holes
        try:
            if holes:
                polygon = Polygon(exterior_coords, holes)
            else:
                polygon = Polygon(exterior_coords)
            
            if not polygon.is_valid:
                polygon = make_valid(polygon)
            
            return polygon
            
        except Exception as e:
            print(f"Warning: Failed to create polygon with holes: {e}")
            # Fall back to exterior only
            return Polygon(exterior_coords)
    
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
            Dictionary with boundary metadata including hole information
        """
        if self.boundary_polygon is None:
            raise DXFParserError("No boundary parsed yet. Call parse() first.")
        
        bounds = self.boundary_polygon.bounds  # (minx, miny, maxx, maxy)
        
        # Get hole information
        holes_info = []
        for i, interior in enumerate(self.boundary_polygon.interiors):
            hole_polygon = Polygon(interior.coords)
            holes_info.append({
                "id": i,
                "coordinates": list(interior.coords),
                "area_sqm": hole_polygon.area,
            })
        
        return {
            "coordinates": list(self.boundary_polygon.exterior.coords),
            "area_sqm": self.boundary_polygon.area,  # Area minus holes
            "area_sqft": self.boundary_polygon.area * 10.764,
            "gross_area_sqm": Polygon(self.boundary_polygon.exterior.coords).area,  # Without subtracting holes
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
            "has_holes": len(self.holes) > 0,
            "num_holes": len(self.holes),
            "holes": holes_info,
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
