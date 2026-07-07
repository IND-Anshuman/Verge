"""Geometry predicates that back layout validation (spec §14.5 step 1)."""

from __future__ import annotations

from verge_twin import geometry as g

# Unit square and its rightward neighbour sharing the x=1 edge.
UNIT = [[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]]
RIGHT = [[(1.0, 0.0), (2.0, 0.0), (2.0, 1.0), (1.0, 1.0)]]
FAR = [[(5.0, 5.0), (6.0, 5.0), (6.0, 6.0), (5.0, 6.0)]]
OVERLAP = [[(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)]]
CONTAINED = [[(0.25, 0.25), (0.75, 0.25), (0.75, 0.75), (0.25, 0.75)]]
CORNER = [[(1.0, 1.0), (2.0, 1.0), (2.0, 2.0), (1.0, 2.0)]]


def test_area_is_orientation_independent():
    assert g.polygon_area(UNIT) == 1.0
    ccw = [[(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]]
    cw = [[(0.0, 0.0), (0.0, 2.0), (2.0, 2.0), (2.0, 0.0)]]
    assert g.polygon_area(ccw) == g.polygon_area(cw) == 4.0


def test_area_subtracts_holes():
    with_hole = [
        [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)],
        [(1.0, 1.0), (2.0, 1.0), (2.0, 2.0), (1.0, 2.0)],
    ]
    assert g.polygon_area(with_hole) == 16.0 - 1.0


def test_point_in_polygon_interior_and_boundary():
    assert g.point_in_polygon((0.5, 0.5), UNIT)
    assert not g.point_in_polygon((1.5, 0.5), UNIT)
    assert g.point_in_polygon((1.0, 0.5), UNIT, boundary=True)
    assert not g.point_in_polygon((1.0, 0.5), UNIT, boundary=False)


def test_shared_edge_is_adjacency_not_overlap():
    assert not g.polygons_overlap(UNIT, RIGHT)
    assert g.polygons_touch(UNIT, RIGHT)


def test_shared_corner_is_adjacency():
    assert not g.polygons_overlap(UNIT, CORNER)
    assert g.polygons_touch(UNIT, CORNER)


def test_real_overlap_detected():
    assert g.polygons_overlap(UNIT, OVERLAP)
    assert g.polygons_overlap(UNIT, CONTAINED)  # containment counts


def test_disjoint_zones_neither_touch_nor_overlap():
    assert not g.polygons_overlap(UNIT, FAR)
    assert not g.polygons_touch(UNIT, FAR)


def test_corner_intrusion_overlap_without_edge_midpoint_probe():
    # b's corner (0.9,0.9) is strictly inside the unit square: a real overlap the
    # old centroid-nudge probe could miss. Vertex-containment must catch it.
    b = [[(0.9, 0.9), (1.9, 0.9), (1.9, 1.9), (0.9, 1.9)]]
    assert g.polygons_overlap(UNIT, b)


def test_non_convex_L_shape_overlap_and_notch():
    L = [[(0.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.0, 1.0), (1.0, 3.0), (0.0, 3.0)]]
    # A square sitting in the L's notch is outside the L — must NOT overlap,
    # even though it is inside the L's bounding box (non-convex correctness).
    in_notch = [[(1.5, 1.5), (2.5, 1.5), (2.5, 2.5), (1.5, 2.5)]]
    assert not g.polygons_overlap(L, in_notch)
    # A square straddling the L's bottom arm truly overlaps.
    on_arm = [[(2.5, 0.5), (3.5, 0.5), (3.5, 1.5), (2.5, 1.5)]]
    assert g.polygons_overlap(L, on_arm)


def test_unclosed_ring_is_handled_like_closed():
    open_ring = [[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]]
    closed_ring = [[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]]
    assert g.polygon_area(open_ring) == g.polygon_area(closed_ring)
