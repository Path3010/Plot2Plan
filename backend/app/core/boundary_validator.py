"""
Boundary Validation Module
==========================

Provides comprehensive validation for plot boundary polygons.

This module validates:
1. Polygon Closure - Ensures the polygon is properly closed
2. Polygon Simplicity - Checks for self-intersections
3. Area & Bounding Box - Calculates geometric properties
4. Polygon Orientation - Detects CW/CCW winding order

Usage:
    from app.core.boundary_validator import BoundaryValidator, ValidationResult
    
    validator = BoundaryValidator(polygon)
    result = validator.validate()
    
    if result.is_valid:
        print(f"Area: {result.area_sqm} m²")
    else:
        print(f"Errors: {result.errors}")
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

from shapely.geometry import Polygon, LinearRing, Point
from shapely.validation import make_valid, explain_validity
from shapely.ops import orient


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Critical - polygon unusable
    WARNING = "warning"  # Non-critical - polygon usable with caveats
    INFO = "info"        # Informational


class OrientationType(Enum):
    """Polygon winding orientation."""
    COUNTER_CLOCKWISE = "ccw"  # Standard for exterior rings
    CLOCKWISE = "cw"           # Standard for interior rings (holes)
    INVALID = "invalid"        # Cannot determine


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    code: str
    message: str
    severity: ValidationSeverity
    details: Optional[Dict[str, Any]] = None


@dataclass
class BoundingBox:
    """Axis-aligned bounding box."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    @property
    def width(self) -> float:
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        return self.max_y - self.min_y
    
    @property
    def center(self) -> Tuple[float, float]:
        return (
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2
        )
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "min_x": self.min_x,
            "min_y": self.min_y,
            "max_x": self.max_x,
            "max_y": self.max_y,
            "width": self.width,
            "height": self.height,
            "center_x": self.center[0],
            "center_y": self.center[1],
        }


@dataclass
class ValidationResult:
    """Complete validation result for a boundary polygon."""
    
    # Overall validity
    is_valid: bool = False
    
    # Geometric properties
    is_closed: bool = False
    is_simple: bool = False  # No self-intersection
    orientation: OrientationType = OrientationType.INVALID
    
    # Calculated values
    area_sqm: float = 0.0
    area_sqft: float = 0.0
    perimeter_m: float = 0.0
    bounding_box: Optional[BoundingBox] = None
    centroid: Optional[Tuple[float, float]] = None
    num_vertices: int = 0
    
    # Hole information
    has_holes: bool = False
    num_holes: int = 0
    holes_area_sqm: float = 0.0
    
    # Shape analysis
    is_convex: bool = False
    aspect_ratio: float = 0.0  # width / height
    compactness: float = 0.0   # 4π × area / perimeter² (circle = 1.0)
    
    # Issues found during validation
    issues: List[ValidationIssue] = field(default_factory=list)
    
    # Corrected polygon (if auto-fix was applied)
    corrected_polygon: Optional[Polygon] = None
    was_corrected: bool = False
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "is_valid": self.is_valid,
            "is_closed": self.is_closed,
            "is_simple": self.is_simple,
            "orientation": self.orientation.value,
            "area_sqm": round(self.area_sqm, 3),
            "area_sqft": round(self.area_sqft, 3),
            "perimeter_m": round(self.perimeter_m, 3),
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "centroid": {"x": self.centroid[0], "y": self.centroid[1]} if self.centroid else None,
            "num_vertices": self.num_vertices,
            "has_holes": self.has_holes,
            "num_holes": self.num_holes,
            "holes_area_sqm": round(self.holes_area_sqm, 3),
            "is_convex": self.is_convex,
            "aspect_ratio": round(self.aspect_ratio, 3),
            "compactness": round(self.compactness, 3),
            "was_corrected": self.was_corrected,
            "issues": [
                {"code": i.code, "message": i.message, "severity": i.severity.value}
                for i in self.issues
            ],
        }


class BoundaryValidator:
    """
    Comprehensive validator for plot boundary polygons.
    
    Performs the following validations:
    1. Closure check - Is the polygon properly closed?
    2. Simplicity check - Are there any self-intersections?
    3. Area calculation - What is the polygon area?
    4. Bounding box - What are the extents?
    5. Orientation detection - Is it CW or CCW?
    6. Shape analysis - Convexity, aspect ratio, compactness
    
    Can optionally auto-correct minor issues.
    """
    
    # Minimum area threshold (in square meters) - below this is likely an error
    MIN_AREA_THRESHOLD = 1.0
    
    # Maximum reasonable plot size (in square meters) - sanity check
    MAX_AREA_THRESHOLD = 100000.0  # 10 hectares
    
    # Minimum number of vertices for a valid polygon
    MIN_VERTICES = 3
    
    def __init__(self, polygon: Polygon, auto_correct: bool = True, is_originally_closed: bool = True):
        """
        Initialize validator with a polygon.
        
        Args:
            polygon: The shapely Polygon to validate
            auto_correct: If True, attempt to fix minor issues
            is_originally_closed: Whether the boundary was closed in the original DXF file
        """
        self.original_polygon = polygon
        self.polygon = polygon
        self.auto_correct = auto_correct
        self.is_originally_closed = is_originally_closed  # Track original state from DXF
        self.result = ValidationResult()
        
    def validate(self) -> ValidationResult:
        """
        Perform all validations and return results.
        
        Returns:
            ValidationResult with all findings
        """
        # Reset result
        self.result = ValidationResult()
        
        # Step 1: Check closure
        self._check_closure()
        
        # Step 2: Check simplicity (self-intersection)
        self._check_simplicity()
        
        # Step 3: Calculate area and bounding box
        self._calculate_geometry()
        
        # Step 4: Detect orientation
        self._detect_orientation()
        
        # Step 5: Analyze shape properties
        self._analyze_shape()
        
        # Step 6: Check holes if any
        self._check_holes()
        
        # Step 7: Sanity checks
        self._sanity_checks()
        
        # Determine overall validity
        self.result.is_valid = len(self.result.errors) == 0
        
        return self.result
    
    def _check_closure(self) -> None:
        """
        Check if the polygon is properly closed.
        
        Uses the is_originally_closed flag from the DXF parser, which indicates
        whether the polyline was marked as closed in the original DXF file.
        """
        try:
            exterior = self.polygon.exterior
            coords = list(exterior.coords)
            
            if len(coords) < 3:
                self.result.issues.append(ValidationIssue(
                    code="INSUFFICIENT_VERTICES",
                    message=f"Polygon has only {len(coords)} vertices, minimum 3 required",
                    severity=ValidationSeverity.ERROR,
                    details={"vertex_count": len(coords)}
                ))
                return
            
            # Use the original closed state from DXF parsing
            # This is more accurate than checking coordinates (which may have been auto-closed)
            is_closed = self.is_originally_closed
            
            self.result.is_closed = is_closed
            
            # Calculate vertices (closed polygon repeats first point, so subtract 1)
            first_point = coords[0]
            last_point = coords[-1]
            tolerance = 1e-6
            coords_match = (
                abs(first_point[0] - last_point[0]) < tolerance and
                abs(first_point[1] - last_point[1]) < tolerance
            )
            self.result.num_vertices = len(coords) - 1 if coords_match else len(coords)
            
            if not is_closed:
                self.result.issues.append(ValidationIssue(
                    code="POLYGON_NOT_CLOSED",
                    message="Boundary is not closed in the DXF file",
                    severity=ValidationSeverity.ERROR,  # Error, not warning
                    details={
                        "original_state": "unclosed",
                        "auto_closed_for_calculations": True
                    }
                ))
                
                # Mark as corrected since we auto-close for calculations
                self.result.was_corrected = True
                self.result.corrected_polygon = self.polygon
                    
        except Exception as e:
            self.result.issues.append(ValidationIssue(
                code="CLOSURE_CHECK_FAILED",
                message=f"Failed to check polygon closure: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))
    
    def _check_simplicity(self) -> None:
        """
        Check if the polygon is simple (no self-intersections).
        
        A simple polygon does not intersect itself.
        """
        try:
            # Check if the polygon is valid according to shapely
            is_valid = self.polygon.is_valid
            is_simple = self.polygon.exterior.is_simple
            
            self.result.is_simple = is_simple and is_valid
            
            if not is_valid:
                # Get detailed explanation of why it's invalid
                explanation = explain_validity(self.polygon)
                
                self.result.issues.append(ValidationIssue(
                    code="POLYGON_INVALID",
                    message=f"Polygon is geometrically invalid: {explanation}",
                    severity=ValidationSeverity.ERROR,
                    details={"shapely_explanation": explanation}
                ))
                
                # Auto-correct: try to fix the polygon
                if self.auto_correct:
                    try:
                        fixed_polygon = make_valid(self.polygon)
                        if isinstance(fixed_polygon, Polygon) and fixed_polygon.is_valid:
                            self.polygon = fixed_polygon
                            self.result.was_corrected = True
                            self.result.corrected_polygon = self.polygon
                            self.result.is_simple = True
                            
                            self.result.issues.append(ValidationIssue(
                                code="POLYGON_AUTO_CORRECTED",
                                message="Polygon was automatically corrected",
                                severity=ValidationSeverity.INFO
                            ))
                    except Exception:
                        pass
                        
            elif not is_simple:
                self.result.issues.append(ValidationIssue(
                    code="SELF_INTERSECTION",
                    message="Polygon has self-intersecting edges",
                    severity=ValidationSeverity.ERROR
                ))
                
        except Exception as e:
            self.result.issues.append(ValidationIssue(
                code="SIMPLICITY_CHECK_FAILED",
                message=f"Failed to check polygon simplicity: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))
    
    def _calculate_geometry(self) -> None:
        """
        Calculate geometric properties: area, bounding box, perimeter, centroid.
        """
        try:
            # Area
            self.result.area_sqm = self.polygon.area
            self.result.area_sqft = self.polygon.area * 10.764
            
            # Perimeter
            self.result.perimeter_m = self.polygon.length
            
            # Bounding box
            bounds = self.polygon.bounds  # (minx, miny, maxx, maxy)
            self.result.bounding_box = BoundingBox(
                min_x=bounds[0],
                min_y=bounds[1],
                max_x=bounds[2],
                max_y=bounds[3]
            )
            
            # Centroid
            centroid = self.polygon.centroid
            self.result.centroid = (centroid.x, centroid.y)
            
        except Exception as e:
            self.result.issues.append(ValidationIssue(
                code="GEOMETRY_CALCULATION_FAILED",
                message=f"Failed to calculate geometric properties: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))
    
    def _detect_orientation(self) -> None:
        """
        Detect the winding order (orientation) of the polygon.
        
        Counter-clockwise (CCW) is the standard for exterior rings.
        Clockwise (CW) is used for interior rings (holes).
        
        Uses the Shoelace formula to determine orientation.
        """
        try:
            exterior = self.polygon.exterior
            
            # LinearRing.is_ccw returns True if counter-clockwise
            if exterior.is_ccw:
                self.result.orientation = OrientationType.COUNTER_CLOCKWISE
            else:
                self.result.orientation = OrientationType.CLOCKWISE
                
                # Exterior should be CCW - this is non-standard
                self.result.issues.append(ValidationIssue(
                    code="CLOCKWISE_EXTERIOR",
                    message="Exterior ring has clockwise orientation (should be counter-clockwise)",
                    severity=ValidationSeverity.WARNING,
                    details={"current": "cw", "expected": "ccw"}
                ))
                
                # Auto-correct: orient to standard CCW
                if self.auto_correct:
                    self.polygon = orient(self.polygon, sign=1.0)  # 1.0 = CCW
                    self.result.was_corrected = True
                    self.result.corrected_polygon = self.polygon
                    self.result.orientation = OrientationType.COUNTER_CLOCKWISE
                    
        except Exception as e:
            self.result.orientation = OrientationType.INVALID
            self.result.issues.append(ValidationIssue(
                code="ORIENTATION_DETECTION_FAILED",
                message=f"Failed to detect polygon orientation: {str(e)}",
                severity=ValidationSeverity.WARNING
            ))
    
    def _analyze_shape(self) -> None:
        """
        Analyze shape properties: convexity, aspect ratio, compactness.
        """
        try:
            # Convexity check
            convex_hull = self.polygon.convex_hull
            self.result.is_convex = self.polygon.equals(convex_hull)
            
            # Aspect ratio (width / height)
            if self.result.bounding_box:
                bbox = self.result.bounding_box
                if bbox.height > 0:
                    self.result.aspect_ratio = bbox.width / bbox.height
                else:
                    self.result.aspect_ratio = 0.0
            
            # Compactness (isoperimetric quotient)
            # Circle has compactness of 1.0, other shapes less
            # Formula: 4π × area / perimeter²
            import math
            if self.result.perimeter_m > 0:
                self.result.compactness = (
                    4 * math.pi * self.result.area_sqm / 
                    (self.result.perimeter_m ** 2)
                )
            
            # Check for extremely elongated shapes
            if self.result.aspect_ratio > 10 or self.result.aspect_ratio < 0.1:
                self.result.issues.append(ValidationIssue(
                    code="EXTREME_ASPECT_RATIO",
                    message=f"Polygon has extreme aspect ratio ({self.result.aspect_ratio:.2f})",
                    severity=ValidationSeverity.WARNING,
                    details={"aspect_ratio": self.result.aspect_ratio}
                ))
                
        except Exception as e:
            self.result.issues.append(ValidationIssue(
                code="SHAPE_ANALYSIS_FAILED",
                message=f"Failed to analyze shape properties: {str(e)}",
                severity=ValidationSeverity.WARNING
            ))
    
    def _check_holes(self) -> None:
        """
        Validate interior rings (holes) if any exist.
        """
        try:
            interiors = list(self.polygon.interiors)
            
            if len(interiors) > 0:
                self.result.has_holes = True
                self.result.num_holes = len(interiors)
                
                # Calculate total hole area
                total_hole_area = 0.0
                for interior in interiors:
                    hole_polygon = Polygon(interior.coords)
                    total_hole_area += hole_polygon.area
                    
                    # Check hole orientation (should be CW)
                    if interior.is_ccw:
                        self.result.issues.append(ValidationIssue(
                            code="HOLE_WRONG_ORIENTATION",
                            message="Hole has counter-clockwise orientation (should be clockwise)",
                            severity=ValidationSeverity.WARNING
                        ))
                        
                self.result.holes_area_sqm = total_hole_area
                
                # Check if holes are too large
                if total_hole_area > self.result.area_sqm * 0.8:
                    self.result.issues.append(ValidationIssue(
                        code="EXCESSIVE_HOLE_AREA",
                        message="Holes occupy more than 80% of the polygon area",
                        severity=ValidationSeverity.WARNING,
                        details={
                            "hole_area": total_hole_area,
                            "total_area": self.result.area_sqm + total_hole_area,
                            "percentage": total_hole_area / (self.result.area_sqm + total_hole_area) * 100
                        }
                    ))
                    
        except Exception as e:
            self.result.issues.append(ValidationIssue(
                code="HOLE_CHECK_FAILED",
                message=f"Failed to check holes: {str(e)}",
                severity=ValidationSeverity.WARNING
            ))
    
    def _sanity_checks(self) -> None:
        """
        Perform sanity checks on the polygon properties.
        """
        # Check minimum area
        if self.result.area_sqm < self.MIN_AREA_THRESHOLD:
            self.result.issues.append(ValidationIssue(
                code="AREA_TOO_SMALL",
                message=f"Polygon area ({self.result.area_sqm:.2f} m²) is below minimum threshold ({self.MIN_AREA_THRESHOLD} m²)",
                severity=ValidationSeverity.WARNING,
                details={"area": self.result.area_sqm, "threshold": self.MIN_AREA_THRESHOLD}
            ))
        
        # Check maximum area
        if self.result.area_sqm > self.MAX_AREA_THRESHOLD:
            self.result.issues.append(ValidationIssue(
                code="AREA_TOO_LARGE",
                message=f"Polygon area ({self.result.area_sqm:.2f} m²) exceeds maximum threshold ({self.MAX_AREA_THRESHOLD} m²)",
                severity=ValidationSeverity.WARNING,
                details={"area": self.result.area_sqm, "threshold": self.MAX_AREA_THRESHOLD}
            ))
        
        # Check minimum vertices
        if self.result.num_vertices < self.MIN_VERTICES:
            self.result.issues.append(ValidationIssue(
                code="TOO_FEW_VERTICES",
                message=f"Polygon has only {self.result.num_vertices} vertices, minimum {self.MIN_VERTICES} required",
                severity=ValidationSeverity.ERROR,
                details={"vertices": self.result.num_vertices, "minimum": self.MIN_VERTICES}
            ))


# Convenience function
def validate_boundary(polygon: Polygon, auto_correct: bool = True) -> ValidationResult:
    """
    Convenience function to validate a boundary polygon.
    
    Args:
        polygon: The shapely Polygon to validate
        auto_correct: If True, attempt to fix minor issues
        
    Returns:
        ValidationResult with all findings
    """
    validator = BoundaryValidator(polygon, auto_correct=auto_correct)
    return validator.validate()
