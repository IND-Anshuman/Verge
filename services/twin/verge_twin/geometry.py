"""Dependency-free planar polygon geometry for plant-layout validation.

Commissioning step 1 (spec §14.5) imports a plant layout and must answer three
questions with zero external dependencies — so it runs on an air-gapped OT box
with no GEOS/shapely install (P2 sovereign-by-default):

  * do any two zones **overlap** (interiors intersect)? — a layout error;
  * do two zones **touch** (share a boundary)? — that is their adjacency, which
    the SIMOPS detector relies on (spec §5 Pillar 4);
  * what area does a zone cover? — used for the coverage/gap report.

Polygons follow the GeoJSON convention: a polygon is a list of linear rings,
the first ring is the exterior and any remaining rings are holes. A ring is a
list of ``(x, y)`` vertices; the closing vertex may be present or omitted.

The predicates are exact for the rectilinear zone layouts plants actually draw
and robust for general simple polygons. They are not a general CG library —
they are exactly what the commissioning validator needs, and nothing more.
"""

from __future__ import annotations

from collections.abc import Sequence

Point = tuple[float, float]
Ring = Sequence[Point]
Polygon = Sequence[Ring]

# Coordinates are lon/lat degrees; ~1e-9 deg is well below any real sensor's
# position error, so it is a safe "same point" tolerance.
EPS = 1e-9


def _close(ring: Ring) -> list[Point]:
    """Return the ring as an explicitly closed vertex list (last == first)."""
    pts = [(float(x), float(y)) for x, y in ring]
    if len(pts) >= 2 and (abs(pts[0][0] - pts[-1][0]) > EPS or abs(pts[0][1] - pts[-1][1]) > EPS):
        pts.append(pts[0])
    return pts


def signed_area(ring: Ring) -> float:
    """Shoelace signed area. Positive = counter-clockwise winding."""
    pts = _close(ring)
    acc = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:], strict=False):
        acc += x1 * y2 - x2 * y1
    return acc / 2.0


def ring_area(ring: Ring) -> float:
    return abs(signed_area(ring))


def polygon_area(polygon: Polygon) -> float:
    """Exterior area minus the area of every hole."""
    if not polygon:
        return 0.0
    rings = list(polygon)
    return ring_area(rings[0]) - sum(ring_area(h) for h in rings[1:])


def bbox(polygon: Polygon) -> tuple[float, float, float, float]:
    """Axis-aligned bounding box (minx, miny, maxx, maxy) of the exterior ring."""
    xs = [p[0] for p in polygon[0]]
    ys = [p[1] for p in polygon[0]]
    return min(xs), min(ys), max(xs), max(ys)


def _bbox_disjoint(a: Polygon, b: Polygon) -> bool:
    ax0, ay0, ax1, ay1 = bbox(a)
    bx0, by0, bx1, by1 = bbox(b)
    return ax1 < bx0 - EPS or bx1 < ax0 - EPS or ay1 < by0 - EPS or by1 < ay0 - EPS


def _orient(a: Point, b: Point, c: Point) -> float:
    """Cross product of (b-a) x (c-a). >0 CCW, <0 CW, ~0 collinear."""
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: Point, b: Point, p: Point) -> bool:
    """Is collinear point p within the closed segment ab?"""
    if abs(_orient(a, b, p)) > EPS:
        return False
    return (
        min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS
        and min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS
    )


def segments_properly_cross(a: Point, b: Point, c: Point, d: Point) -> bool:
    """Do segments ab and cd cross at an interior point of both?

    Endpoint touches and collinear overlaps return False — those are *contact*
    (adjacency), not a crossing (overlap).
    """
    d1 = _orient(c, d, a)
    d2 = _orient(c, d, b)
    d3 = _orient(a, b, c)
    d4 = _orient(a, b, d)
    return ((d1 > EPS) != (d2 > EPS)) and ((d3 > EPS) != (d4 > EPS)) and all(
        abs(d) > EPS for d in (d1, d2, d3, d4)
    )


def _edges(polygon: Polygon) -> list[tuple[Point, Point]]:
    out: list[tuple[Point, Point]] = []
    for ring in polygon:
        pts = _close(ring)
        out.extend(zip(pts, pts[1:], strict=False))
    return out


def point_in_polygon(pt: Point, polygon: Polygon, *, boundary: bool = True) -> bool:
    """Ray-cast containment. ``boundary`` controls whether a point exactly on an
    edge counts as inside (True) or outside (False)."""
    for a, b in _edges(polygon):
        if _on_segment(a, b, pt):
            return boundary
    x, y = pt
    inside = False
    for ring in polygon:
        pts = _close(ring)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:], strict=False):
            if (y1 > y) != (y2 > y):
                x_cross = x1 + (y - y1) / (y2 - y1) * (x2 - x1)
                if x < x_cross:
                    inside = not inside
    return inside


def polygons_overlap(a: Polygon, b: Polygon) -> bool:
    """True iff the polygon **interiors** intersect (a real area overlap).

    Two zones that merely share an edge or a corner do NOT overlap — that is
    adjacency. Overlap means one intrudes into the other and is a layout error.
    """
    if _bbox_disjoint(a, b):
        return False
    for a0, a1 in _edges(a):
        for b0, b1 in _edges(b):
            if segments_properly_cross(a0, a1, b0, b1):
                return True
    # No *proper* edge crossing. This still covers two real overlap shapes:
    #   (1) collinear-boundary overlaps (axis-aligned zones sharing an edge-line
    #       while their interiors intersect) — the bounding-box intersection has
    #       positive area and its midpoint is strictly inside both;
    #   (2) full containment (one zone inside the other, even sharing an edge) —
    #       a guaranteed interior point of the inner is strictly inside the outer.
    # Both probes are hole-aware via point_in_polygon (a point in a hole is out).
    ax0, ay0, ax1, ay1 = bbox(a)
    bx0, by0, bx1, by1 = bbox(b)
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 - ix0 > EPS and iy1 - iy0 > EPS:
        mid = ((ix0 + ix1) / 2.0, (iy0 + iy1) / 2.0)
        if point_in_polygon(mid, a, boundary=False) and point_in_polygon(
            mid, b, boundary=False
        ):
            return True
    ia, ib = _interior_point(a), _interior_point(b)
    if ia is not None and point_in_polygon(ia, b, boundary=False):
        return True
    return ib is not None and point_in_polygon(ib, a, boundary=False)


def _interior_point(polygon: Polygon) -> Point | None:
    """A point guaranteed strictly inside a simple polygon (None if degenerate).

    Uses the centroid of an 'ear' triangle: for a simple polygon at least one
    vertex is convex, and the centroid of its triangle is interior. We accept the
    first ear-centroid that tests strictly inside (handles reflex vertices)."""
    pts = _close(polygon[0])[:-1]  # unique vertices
    n = len(pts)
    if n < 3:
        return None
    for i in range(n):
        a, b, c = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        centroid = ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0)
        if point_in_polygon(centroid, polygon, boundary=False):
            return centroid
    return None


def _collinear_overlap_len(a: Point, b: Point, c: Point, d: Point) -> float:
    """Length of the shared collinear overlap of segments ab and cd (0 if none)."""
    if abs(_orient(a, b, c)) > EPS or abs(_orient(a, b, d)) > EPS:
        return 0.0  # not collinear
    # Project onto the dominant axis to order the four points.
    horizontal = abs(b[0] - a[0]) >= abs(b[1] - a[1])
    key = (lambda p: p[0]) if horizontal else (lambda p: p[1])
    a0, a1 = sorted((a, b), key=key)
    b0, b1 = sorted((c, d), key=key)
    lo = max(key(a0), key(b0))
    hi = min(key(a1), key(b1))
    return max(0.0, hi - lo)


def polygons_touch(a: Polygon, b: Polygon) -> bool:
    """True iff two polygons share a boundary point/edge but do NOT overlap.

    This is the adjacency relation SIMOPS conflict detection uses: two zones are
    adjacent iff they touch. Shared edges (rectilinear zones) and shared corners
    both count; overlapping polygons are a layout error, not adjacency, so they
    are excluded here even if they also happen to share an edge.
    """
    if _bbox_disjoint(a, b) or polygons_overlap(a, b):
        return False
    a_edges = _edges(a)
    b_edges = _edges(b)
    for a0, a1 in a_edges:
        for b0, b1 in b_edges:
            if _collinear_overlap_len(a0, a1, b0, b1) > EPS:
                return True
            # shared vertex / vertex-on-edge contact
            if _on_segment(a0, a1, b0) or _on_segment(a0, a1, b1):
                return True
            if _on_segment(b0, b1, a0) or _on_segment(b0, b1, a1):
                return True
    return False
