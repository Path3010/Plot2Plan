"""
Layout Engine for Floor Plan Generation.

Provides grid-based and treemap-based subdivision of arbitrary polygons
into room layouts. All geometry uses Shapely polygons.
"""

from .generator import LayoutGenerator

__all__ = ["LayoutGenerator"]
