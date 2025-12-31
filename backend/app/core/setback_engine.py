"""
Setback Engine Module
Calculates buildable area by applying setback rules to plot boundaries.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
import numpy as np


@dataclass
class SetbackConfig:
    """Configuration for setback distances."""
    front: float = 3.0    # meters
    back: float = 2.0     # meters
    left: float = 1.5     # meters
    right: float = 1.5    # meters
    
    def to_dict(self) -> dict:
        return {
            "front": self.front,
            "back": self.back,
            "left": self.left,
            "right": self.right,
        }


class SetbackEngine:
    """
    Engine for calculating buildable area from plot boundary and setback rules.
    
    The setback calculation considers:
    - Different setback distances for each side (front, back, left, right)
    - Plot orientation (which side faces the street)
    - Variable setbacks for common walls
    """
    
    def __init__(
        self,
        plot_boundary: Polygon,
        front_direction: str = "S",  # N, S, E, W - which direction faces the street
    ):
        """
        Initialize the setback engine.
        
        Args:
            plot_boundary: Plot boundary as shapely Polygon
            front_direction: Direction that the front of the plot faces
        """
        self.plot_boundary = plot_boundary
        self.front_direction = front_direction.upper()
        self.buildable_area: Optional[Polygon] = None
        
    def calculate_buildable_area(self, config: SetbackConfig) -> Polygon:
        """
        Calculate the buildable area by applying setback rules.
        
        For simple rectangular plots, this applies different offsets to each edge.
        For complex polygons, uses a simplified buffer approach.
        
        Args:
            config: SetbackConfig with distances for each side
            
        Returns:
            Polygon representing the buildable area
        """
        if self._is_approximately_rectangular():
            self.buildable_area = self._calculate_rectangular_setback(config)
        else:
            # For complex shapes, use uniform buffer as approximation
            # TODO: Implement edge-specific setbacks for complex polygons
            min_setback = min(config.front, config.back, config.left, config.right)
            self.buildable_area = self.plot_boundary.buffer(-min_setback)
        
        return self.buildable_area
    
    def _is_approximately_rectangular(self, tolerance: float = 0.1) -> bool:
        """Check if the plot boundary is approximately rectangular."""
        coords = list(self.plot_boundary.exterior.coords)
        
        # Rectangular polygons have 5 points (4 corners + closing point)
        if len(coords) != 5:
            return False
        
        # Check if angles are approximately 90 degrees
        for i in range(4):
            p1 = np.array(coords[i])
            p2 = np.array(coords[(i + 1) % 4])
            p3 = np.array(coords[(i + 2) % 4])
            
            v1 = p1 - p2
            v2 = p3 - p2
            
            # Normalize vectors
            v1_norm = v1 / np.linalg.norm(v1)
            v2_norm = v2 / np.linalg.norm(v2)
            
            # Dot product should be ~0 for perpendicular vectors
            dot = abs(np.dot(v1_norm, v2_norm))
            if dot > tolerance:
                return False
        
        return True
    
    def _calculate_rectangular_setback(self, config: SetbackConfig) -> Polygon:
        """
        Calculate setback for rectangular plot with different distances per edge.
        """
        bounds = self.plot_boundary.bounds  # (minx, miny, maxx, maxy)
        minx, miny, maxx, maxy = bounds
        
        # Map setbacks based on front direction
        setback_map = self._get_setback_mapping(config)
        
        # Calculate new bounds with setbacks
        new_minx = minx + setback_map["left"]
        new_maxx = maxx - setback_map["right"]
        new_miny = miny + setback_map["bottom"]
        new_maxy = maxy - setback_map["top"]
        
        # Ensure we don't get invalid geometry
        if new_minx >= new_maxx or new_miny >= new_maxy:
            # Return a minimal polygon at centroid if setbacks are too large
            centroid = self.plot_boundary.centroid
            return centroid.buffer(0.1)
        
        return Polygon([
            (new_minx, new_miny),
            (new_maxx, new_miny),
            (new_maxx, new_maxy),
            (new_minx, new_maxy),
            (new_minx, new_miny),
        ])
    
    def _get_setback_mapping(self, config: SetbackConfig) -> Dict[str, float]:
        """
        Map setback configuration to actual edges based on front direction.
        
        Returns dict with keys: top, bottom, left, right
        """
        # Map based on which direction is the "front" (facing street)
        mappings = {
            "N": {
                "top": config.front,     # North edge is front
                "bottom": config.back,
                "left": config.left,
                "right": config.right,
            },
            "S": {
                "bottom": config.front,  # South edge is front
                "top": config.back,
                "left": config.left,
                "right": config.right,
            },
            "E": {
                "right": config.front,   # East edge is front
                "left": config.back,
                "top": config.left,
                "bottom": config.right,
            },
            "W": {
                "left": config.front,    # West edge is front
                "right": config.back,
                "top": config.right,
                "bottom": config.left,
            },
        }
        
        return mappings.get(self.front_direction, mappings["S"])
    
    def get_setback_polygons(self, config: SetbackConfig) -> Dict[str, Polygon]:
        """
        Get individual setback zone polygons for visualization.
        
        Returns:
            Dict with front, back, left, right setback zones
        """
        if self.buildable_area is None:
            self.calculate_buildable_area(config)
        
        # Calculate the setback zones (area between plot boundary and buildable area)
        setback_zone = self.plot_boundary.difference(self.buildable_area)
        
        return {
            "total_setback": setback_zone,
            "buildable": self.buildable_area,
        }
    
    def get_coverage_stats(self, config: SetbackConfig) -> dict:
        """
        Get statistics about the buildable area and coverage.
        
        Args:
            config: SetbackConfig to use
            
        Returns:
            Dict with coverage statistics
        """
        if self.buildable_area is None:
            self.calculate_buildable_area(config)
        
        plot_area = self.plot_boundary.area
        buildable_area = self.buildable_area.area
        setback_area = plot_area - buildable_area
        
        return {
            "plot_area_sqm": plot_area,
            "plot_area_sqft": plot_area * 10.764,
            "buildable_area_sqm": buildable_area,
            "buildable_area_sqft": buildable_area * 10.764,
            "setback_area_sqm": setback_area,
            "coverage_ratio": buildable_area / plot_area if plot_area > 0 else 0,
            "max_coverage_allowed": 0.60,  # From rules
            "coverage_status": "OK" if (buildable_area / plot_area) <= 0.60 else "EXCEEDS_LIMIT",
        }


# Convenience function
def calculate_setback(
    plot_boundary: Polygon,
    front: float = 3.0,
    back: float = 2.0,
    left: float = 1.5,
    right: float = 1.5,
    front_direction: str = "S",
) -> Tuple[Polygon, dict]:
    """
    Convenience function to calculate buildable area.
    
    Returns:
        Tuple of (buildable_polygon, stats_dict)
    """
    config = SetbackConfig(front=front, back=back, left=left, right=right)
    engine = SetbackEngine(plot_boundary, front_direction)
    buildable = engine.calculate_buildable_area(config)
    stats = engine.get_coverage_stats(config)
    return buildable, stats
