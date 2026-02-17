"""Boundary extraction from images (OpenCV) and DXF files (ezdxf)."""

import cv2
import numpy as np
from shapely.geometry import Polygon
from pathlib import Path
import json


def extract_polygon_from_image(image_path: str, scale: float = 1.0) -> dict:
    """
    Extract boundary polygon from an uploaded image using OpenCV.

    Pipeline: grayscale → blur → Canny → find contours → largest → simplify.

    Returns dict with 'polygon' (list of [x,y]), 'area', 'num_vertices'.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply adaptive thresholding for better edge detection
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Morphological operations to clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    edges = cv2.Canny(blurred, 50, 150)

    # Combine threshold and edges
    combined = cv2.bitwise_or(thresh, edges)

    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        raise ValueError("No contours found in the image.")

    # Select the largest contour (assumed to be the boundary)
    main_contour = max(contours, key=cv2.contourArea)

    # Simplify using Douglas-Peucker algorithm
    epsilon = 0.01 * cv2.arcLength(main_contour, True)
    approx = cv2.approxPolyDP(main_contour, epsilon, True)

    polygon_coords = approx.squeeze().tolist()

    # Handle edge case where squeeze reduces to a single point
    if not isinstance(polygon_coords[0], list):
        polygon_coords = [polygon_coords]

    # Scale coordinates
    if scale != 1.0:
        polygon_coords = [[p[0] * scale, p[1] * scale] for p in polygon_coords]

    # Ensure polygon is closed
    if polygon_coords[0] != polygon_coords[-1]:
        polygon_coords.append(polygon_coords[0])

    # Compute area using Shapely
    try:
        shapely_poly = Polygon(polygon_coords)
        area = shapely_poly.area
    except Exception:
        area = cv2.contourArea(main_contour) * (scale ** 2)

    return {
        "polygon": polygon_coords,
        "area": round(area, 2),
        "num_vertices": len(polygon_coords) - 1,  # exclude closing vertex
    }


def extract_polygon_from_dxf(dxf_path: str) -> dict:
    """
    Extract boundary polygon from a DXF file.

    Parses LINE and LWPOLYLINE entities and merges them into a closed polygon.
    """
    import ezdxf

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    all_points = []

    # Extract from LWPOLYLINE
    for entity in msp.query("LWPOLYLINE"):
        points = list(entity.get_points(format="xy"))
        all_points.extend(points)

    # Extract from LINE
    for entity in msp.query("LINE"):
        start = (entity.dxf.start.x, entity.dxf.start.y)
        end = (entity.dxf.end.x, entity.dxf.end.y)
        all_points.extend([start, end])

    if not all_points:
        raise ValueError("No LINE or LWPOLYLINE entities found in DXF.")

    # Create a convex hull to form a closed boundary
    from shapely.geometry import MultiPoint
    mp = MultiPoint(all_points)
    hull = mp.convex_hull

    if hull.geom_type == "Polygon":
        coords = list(hull.exterior.coords)
    else:
        raise ValueError("Could not form a valid polygon from DXF entities.")

    polygon_coords = [[round(c[0], 2), round(c[1], 2)] for c in coords]

    shapely_poly = Polygon(polygon_coords)
    area = round(shapely_poly.area, 2)

    return {
        "polygon": polygon_coords,
        "area": area,
        "num_vertices": len(polygon_coords) - 1,
    }


def process_boundary_file(file_path: str, file_type: str, scale: float = 1.0) -> dict:
    """Route to appropriate processor based on file type."""
    if file_type in ("image", "png", "jpg", "jpeg"):
        return extract_polygon_from_image(file_path, scale)
    elif file_type in ("dxf",):
        return extract_polygon_from_dxf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
