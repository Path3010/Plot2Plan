"""
DXF Parser Module
Handles parsing of DXF files and extraction of plot boundaries.
Supports nested boundaries (holes/cutouts) for complex plot shapes.
"""

from typing import List, Tuple, Optional
from pathlib import Path

import ezdxf
from ezdxf.entities import LWPolyline, Polyline
from shapely.geometry import Polygon, LinearRing, MultiPolygon
from shapely.validation import make_valid


def ensure_polygon(geom) -> Optional[Polygon]:
    """
    Ensure the geometry is a single Polygon.
    If it's a MultiPolygon, return the largest polygon.
    """
    if geom is None:
        return None
    if isinstance(geom, Polygon):
        return geom
    if isinstance(geom, MultiPolygon):
        # Return the largest polygon from the collection
        if len(geom.geoms) == 0:
            return None
        largest = max(geom.geoms, key=lambda p: p.area)
        return largest
    # For other geometry types, try to get the convex hull as a polygon
    try:
        return geom.convex_hull
    except:
        return None


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
        self.raw_exterior_coords: List[Tuple[float, float]] = []  # Original coords before any fixes
        self.raw_exterior_coords_unclosed: List[Tuple[float, float]] = []  # Original coords WITHOUT auto-closing
        self.holes: List[List[Tuple[float, float]]] = []
        self.raw_holes: List[List[Tuple[float, float]]] = []  # Original hole coords
        self.parsing_issues: List[dict] = []  # Issues found during parsing
        self.is_originally_closed: bool = True  # Was the boundary originally closed in DXF?
        
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
        
        # Collect all polylines (including unclosed ones)
        all_polygons = self._collect_all_polygons(msp)
        
        # If no closed polygons found, try to collect unclosed ones
        if not all_polygons:
            all_polygons = self._collect_all_polylines_lenient(msp)
        
        if not all_polygons:
            raise DXFParserError("No polylines found in DXF file")
        
        # Build polygon with holes
        boundary = self._build_polygon_with_holes(all_polygons)
        
        if boundary is None:
            raise DXFParserError("Failed to build boundary polygon")
        
        self.boundary_polygon = boundary
        return boundary
    
    def _collect_all_polylines_lenient(self, msp) -> List[Tuple[Polygon, str, List[Tuple[float, float]], List[Tuple[float, float]], bool]]:
        """
        Lenient collection - collects ALL polylines including unclosed ones.
        Used as fallback when no closed polylines are found.
        
        Returns:
            List of (polygon, layer_name, closed_coords, unclosed_coords, is_closed) tuples
        """
        polygons = []
        
        # Collect ALL LWPOLYLINE entities (closed or not)
        for entity in msp.query('LWPOLYLINE'):
            polygon, closed_coords, unclosed_coords = self._lwpolyline_to_polygon_with_coords_v2(entity)
            if polygon is not None and len(unclosed_coords) >= 3:
                layer = entity.dxf.layer.upper() if entity.dxf.layer else "0"
                is_closed = entity.closed
                # Mark if it was originally unclosed
                if not is_closed:
                    self.is_originally_closed = False
                    self.parsing_issues.append({
                        "code": "UNCLOSED_POLYLINE",
                        "message": f"Polyline on layer '{layer}' is not closed",
                        "severity": "warning"
                    })
                polygons.append((polygon, layer, closed_coords, unclosed_coords, is_closed))
        
        # Collect ALL POLYLINE entities
        for entity in msp.query('POLYLINE'):
            polygon, closed_coords, unclosed_coords = self._polyline_to_polygon_with_coords_v2(entity)
            if polygon is not None and len(unclosed_coords) >= 3:
                layer = entity.dxf.layer.upper() if entity.dxf.layer else "0"
                is_closed = entity.is_closed
                if not is_closed:
                    self.is_originally_closed = False
                    self.parsing_issues.append({
                        "code": "UNCLOSED_POLYLINE",
                        "message": f"Polyline on layer '{layer}' is not closed",
                        "severity": "warning"
                    })
                polygons.append((polygon, layer, closed_coords, unclosed_coords, is_closed))
        
        return polygons
    
    def _collect_all_polygons(self, msp) -> List[Tuple[Polygon, str, List[Tuple[float, float]]]]:
        """
        Collect all closed polylines and convert them to polygons.
        Returns list of (polygon, layer_name, raw_coords) tuples.
        
        Note: We keep invalid/self-intersecting polygons for display,
        but also create valid versions for area calculations.
        """
        polygons = []
        
        # Collect LWPOLYLINE entities
        for entity in msp.query('LWPOLYLINE'):
            if entity.closed:
                polygon, raw_coords = self._lwpolyline_to_polygon_with_coords(entity)
                if polygon is not None and len(raw_coords) >= 3:
                    layer = entity.dxf.layer.upper() if entity.dxf.layer else "0"
                    polygons.append((polygon, layer, raw_coords))
        
        # Collect POLYLINE entities (older DXF format)
        for entity in msp.query('POLYLINE'):
            if entity.is_closed:
                polygon, raw_coords = self._polyline_to_polygon_with_coords(entity)
                if polygon is not None and len(raw_coords) >= 3:
                    layer = entity.dxf.layer.upper() if entity.dxf.layer else "0"
                    polygons.append((polygon, layer, raw_coords))
        
        return polygons
    
    def _build_polygon_with_holes(self, polygons) -> Optional[Polygon]:
        """
        Build a polygon with holes from a list of polygons.
        
        Logic:
        1. Find the largest polygon (exterior boundary)
        2. Find all smaller polygons that are inside the exterior
        3. These become holes
        
        Also stores raw coordinates for accurate display of original shape.
        
        Handles both tuple formats:
        - 3-tuple: (polygon, layer, raw_coords) from closed polylines
        - 5-tuple: (polygon, layer, closed_coords, unclosed_coords, is_closed) from lenient collection
        """
        if not polygons:
            return None
        
        # Sort by area (largest first)
        polygons.sort(key=lambda x: x[0].area, reverse=True)
        
        # The largest polygon is the exterior
        first = polygons[0]
        exterior_polygon = first[0]
        exterior_layer = first[1]
        
        # Handle both tuple formats
        if len(first) == 5:
            # 5-tuple format: (polygon, layer, closed_coords, unclosed_coords, is_closed)
            closed_coords = first[2]
            unclosed_coords = first[3]
            is_closed = first[4]
            self.raw_exterior_coords = closed_coords
            self.raw_exterior_coords_unclosed = unclosed_coords
            self.is_originally_closed = is_closed
        else:
            # 3-tuple format: (polygon, layer, raw_coords)
            raw_exterior = first[2]
            self.raw_exterior_coords = raw_exterior
            self.raw_exterior_coords_unclosed = raw_exterior  # Same as closed for closed polygons
            self.is_originally_closed = True
        
        # Store processed exterior coords
        if exterior_polygon.exterior:
            exterior_coords = list(exterior_polygon.exterior.coords)
        else:
            exterior_coords = self.raw_exterior_coords
        self.exterior_coords = exterior_coords
        
        # Find holes - smaller polygons that are inside the exterior
        holes = []
        for item in polygons[1:]:
            polygon = item[0]
            layer = item[1]
            raw_hole = item[2] if len(item) >= 3 else []
            
            # Check if this polygon is inside the exterior
            try:
                is_inside = exterior_polygon.contains(polygon)
            except:
                is_inside = False
                
            if is_inside or layer in self.HOLE_LAYERS:
                # This is a hole - store raw coords for display
                self.raw_holes.append(raw_hole)
                
                # Process hole coords
                if polygon.exterior:
                    hole_coords = list(polygon.exterior.coords)
                else:
                    hole_coords = raw_hole
                # Ensure hole has opposite orientation (clockwise for holes)
                ring = LinearRing(hole_coords)
                if ring.is_ccw:
                    hole_coords = list(reversed(hole_coords))
                holes.append(hole_coords)
                self.holes.append(hole_coords)
        
        # Create polygon with holes - use raw coords for accurate display
        try:
            if holes:
                polygon = Polygon(raw_exterior, [h for h in self.raw_holes])
            else:
                polygon = Polygon(raw_exterior)
            
            # Store the original polygon without make_valid for display
            self.boundary_polygon = polygon
            
            # If invalid, we still keep the original shape but note it
            if not polygon.is_valid:
                # Create a validated version for calculations only
                validated = make_valid(polygon)
                validated = ensure_polygon(validated)
            
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
    
    def _lwpolyline_to_polygon_with_coords_v2(self, entity: LWPolyline) -> Tuple[Optional[Polygon], List[Tuple[float, float]], List[Tuple[float, float]]]:
        """
        Convert LWPOLYLINE entity to shapely Polygon, returning polygon, closed coords, and unclosed coords.
        
        Returns:
            Tuple of (polygon, closed_coordinates, unclosed_coordinates)
            - closed_coordinates: coords with closing point added if needed
            - unclosed_coordinates: original coords as they appear in DXF (for accurate display)
        """
        try:
            # Get vertices (x, y, start_width, end_width, bulge)
            points = [(p[0], p[1]) for p in entity.get_points()]
            
            if len(points) < 3:
                return None, [], []
            
            # Store original unclosed coordinates (as they appear in DXF)
            unclosed_coords = points.copy()
            
            # Create closed version for polygon
            closed_coords = points.copy()
            if closed_coords[0] != closed_coords[-1]:
                closed_coords.append(closed_coords[0])
            
            # Create polygon (needs closed ring)
            polygon = Polygon(closed_coords)
            
            return polygon, closed_coords, unclosed_coords
            
        except Exception as e:
            print(f"Warning: Failed to convert LWPOLYLINE: {e}")
            return None, [], []
    
    def _polyline_to_polygon_with_coords_v2(self, entity: Polyline) -> Tuple[Optional[Polygon], List[Tuple[float, float]], List[Tuple[float, float]]]:
        """
        Convert POLYLINE entity to shapely Polygon, returning polygon, closed coords, and unclosed coords.
        
        Returns:
            Tuple of (polygon, closed_coordinates, unclosed_coordinates)
        """
        try:
            points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
            
            if len(points) < 3:
                return None, [], []
            
            # Store original unclosed coordinates
            unclosed_coords = points.copy()
            
            # Create closed version for polygon
            closed_coords = points.copy()
            if closed_coords[0] != closed_coords[-1]:
                closed_coords.append(closed_coords[0])
            
            # Create polygon (needs closed ring)
            polygon = Polygon(closed_coords)
            
            return polygon, closed_coords, unclosed_coords
            
        except Exception as e:
            print(f"Warning: Failed to convert POLYLINE: {e}")
            return None, [], []
    
    def _lwpolyline_to_polygon_with_coords(self, entity: LWPolyline, force_close: bool = False) -> Tuple[Optional[Polygon], List[Tuple[float, float]]]:
        """
        Convert LWPOLYLINE entity to shapely Polygon, returning both polygon and raw coords.
        
        Args:
            entity: The LWPOLYLINE entity
            force_close: If True, close the polygon even if entity is not marked as closed
        
        Returns:
            Tuple of (polygon, raw_coordinates)
        """
        try:
            # Get vertices (x, y, start_width, end_width, bulge)
            points = [(p[0], p[1]) for p in entity.get_points()]
            
            if len(points) < 3:
                return None, []
            
            # Store original coordinates before any modifications
            raw_coords = points.copy()
            
            # Ensure polygon is closed (append first point if needed)
            if points[0] != points[-1]:
                points.append(points[0])
                raw_coords.append(raw_coords[0])
            
            # Create polygon WITHOUT applying make_valid (to preserve original shape)
            polygon = Polygon(points)
            
            return polygon, raw_coords
            
        except Exception as e:
            print(f"Warning: Failed to convert LWPOLYLINE: {e}")
            return None, []
    
    def _polyline_to_polygon_with_coords(self, entity: Polyline, force_close: bool = False) -> Tuple[Optional[Polygon], List[Tuple[float, float]]]:
        """
        Convert POLYLINE entity to shapely Polygon, returning both polygon and raw coords.
        
        Args:
            entity: The POLYLINE entity
            force_close: If True, close the polygon even if entity is not marked as closed
        
        Returns:
            Tuple of (polygon, raw_coordinates)
        """
        try:
            points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
            
            if len(points) < 3:
                return None, []
            
            # Store original coordinates before any modifications
            raw_coords = points.copy()
            
            # Ensure polygon is closed
            if points[0] != points[-1]:
                points.append(points[0])
                raw_coords.append(raw_coords[0])
            
            # Create polygon WITHOUT applying make_valid (to preserve original shape)
            polygon = Polygon(points)
            
            return polygon, raw_coords
            
        except Exception as e:
            print(f"Warning: Failed to convert POLYLINE: {e}")
            return None, []
    
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
            
            # Ensure we have a single Polygon (make_valid can return MultiPolygon)
            polygon = ensure_polygon(polygon)
            if polygon is None:
                return None
            
            # Ensure counter-clockwise orientation (exterior ring)
            if polygon.exterior and not LinearRing(polygon.exterior.coords).is_ccw:
                polygon = Polygon(list(reversed(list(polygon.exterior.coords))))
            
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
            
            # Ensure we have a single Polygon (make_valid can return MultiPolygon)
            polygon = ensure_polygon(polygon)
            
            return polygon
            
        except Exception as e:
            print(f"Warning: Failed to convert POLYLINE: {e}")
            return None
    
    def get_boundary_info(self) -> dict:
        """
        Get information about the parsed boundary.
        
        Returns:
            Dictionary with boundary metadata including hole information.
            Uses raw coordinates for display to preserve original shape.
        """
        if self.boundary_polygon is None:
            raise DXFParserError("No boundary parsed yet. Call parse() first.")
        
        # Use raw coordinates for display (preserves original shape)
        display_coords = self.raw_exterior_coords if self.raw_exterior_coords else list(self.boundary_polygon.exterior.coords)
        
        # Calculate bounds from raw coordinates
        if self.raw_exterior_coords:
            xs = [p[0] for p in self.raw_exterior_coords]
            ys = [p[1] for p in self.raw_exterior_coords]
            bounds = (min(xs), min(ys), max(xs), max(ys))
        else:
            bounds = self.boundary_polygon.bounds
        
        # Get hole information - use raw hole coords for display
        holes_info = []
        for i, raw_hole in enumerate(self.raw_holes):
            hole_polygon = Polygon(raw_hole)
            holes_info.append({
                "id": i,
                "coordinates": raw_hole,
                "area_sqm": abs(hole_polygon.area) if hole_polygon.is_valid else 0,
            })
        
        # Calculate area - for invalid polygons, use absolute value or convex hull
        try:
            if self.boundary_polygon.is_valid:
                area = self.boundary_polygon.area
            else:
                # For invalid polygons, calculate area using convex hull as approximation
                area = abs(self.boundary_polygon.area) if self.boundary_polygon.area != 0 else self.boundary_polygon.convex_hull.area
        except:
            area = 0
        
        # Calculate centroid
        try:
            centroid_x = self.boundary_polygon.centroid.x
            centroid_y = self.boundary_polygon.centroid.y
        except:
            # Fallback to center of bounding box
            centroid_x = (bounds[0] + bounds[2]) / 2
            centroid_y = (bounds[1] + bounds[3]) / 2
        
        return {
            "coordinates": display_coords,  # Closed coords for calculations
            "coordinates_unclosed": self.raw_exterior_coords_unclosed,  # Original unclosed coords for accurate display
            "is_originally_closed": self.is_originally_closed,  # Was boundary closed in DXF?
            "area_sqm": area,
            "area_sqft": area * 10.764,
            "gross_area_sqm": area,
            "perimeter_m": self.boundary_polygon.length if self.boundary_polygon.is_valid else 0,
            "bounding_box": {
                "min_x": bounds[0],
                "min_y": bounds[1],
                "max_x": bounds[2],
                "max_y": bounds[3],
            },
            "width": bounds[2] - bounds[0],
            "height": bounds[3] - bounds[1],
            "centroid": {
                "x": centroid_x,
                "y": centroid_y,
            },
            "is_convex": False,  # Don't check convexity for potentially invalid polygons
            "is_valid": self.boundary_polygon.is_valid,
            "has_holes": len(self.raw_holes) > 0,
            "num_holes": len(self.raw_holes),
            "holes": holes_info,
            "parsing_issues": self.parsing_issues,  # Issues found during parsing
        }
    
    def validate_boundary(self) -> dict:
        """
        Perform comprehensive validation on the parsed boundary.
        
        Returns:
            Dictionary with validation results
        """
        if self.boundary_polygon is None:
            raise DXFParserError("No boundary parsed yet. Call parse() first.")
        
        from app.core.boundary_validator import BoundaryValidator
        
        validator = BoundaryValidator(
            self.boundary_polygon, 
            auto_correct=True,
            is_originally_closed=self.is_originally_closed  # Pass original closed state
        )
        result = validator.validate()
        
        # If polygon was corrected, update our reference
        if result.was_corrected and result.corrected_polygon is not None:
            self.boundary_polygon = result.corrected_polygon
        
        return result.to_dict()


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


def parse_and_validate_dxf(file_path: str | Path) -> Tuple[Polygon, dict, dict]:
    """
    Parse a DXF file and validate the boundary.
    
    Args:
        file_path: Path to DXF file
        
    Returns:
        Tuple of (Polygon, boundary_info, validation_result)
    """
    parser = DXFParser(file_path)
    polygon = parser.parse()
    info = parser.get_boundary_info()
    validation = parser.validate_boundary()
    return polygon, info, validation

