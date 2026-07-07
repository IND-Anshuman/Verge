"""Property/fuzz tests for the safety-critical polygon predicates.

Zone adjacency (polygons_touch) feeds SIMOPS conflict detection and zone overlap
(polygons_overlap) is a commissioning layout error — both must be exactly right.
For axis-aligned rectangles (what plant layouts overwhelmingly are) the truth is
analytic, so we fuzz thousands of random rectangle pairs and assert the geometry
functions match ground truth, plus general invariants.
"""

from __future__ import annotations

import random

from verge_twin import geometry as g

SEED = 20260707


def _rect(x0, y0, w, h):
    return [[(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]]


def _analytic(ax0, ay0, aw, ah, bx0, by0, bw, bh):
    """Ground-truth (overlap, touch) for two axis-aligned rectangles."""
    x_len = min(ax0 + aw, bx0 + bw) - max(ax0, bx0)
    y_len = min(ay0 + ah, by0 + bh) - max(ay0, by0)
    overlap = x_len > 0 and y_len > 0
    closed_intersect = x_len >= 0 and y_len >= 0
    touch = closed_intersect and not overlap
    return overlap, touch


def test_fuzz_rectangles_match_analytic_truth():
    rng = random.Random(SEED)
    for _ in range(4000):
        a = [rng.randint(0, 8) for _ in range(2)] + [rng.randint(1, 5) for _ in range(2)]
        b = [rng.randint(0, 8) for _ in range(2)] + [rng.randint(1, 5) for _ in range(2)]
        pa, pb = _rect(*a), _rect(*b)
        overlap, touch = _analytic(*a, *b)
        assert g.polygons_overlap(pa, pb) is overlap, (a, b, "overlap")
        assert g.polygons_touch(pa, pb) is touch, (a, b, "touch")
        # overlap and touch are mutually exclusive by construction.
        assert not (g.polygons_overlap(pa, pb) and g.polygons_touch(pa, pb))


def test_overlap_is_symmetric_and_reflexive():
    rng = random.Random(SEED + 1)
    for _ in range(1000):
        a = [rng.randint(0, 6) for _ in range(2)] + [rng.randint(1, 4) for _ in range(2)]
        b = [rng.randint(0, 6) for _ in range(2)] + [rng.randint(1, 4) for _ in range(2)]
        pa, pb = _rect(*a), _rect(*b)
        assert g.polygons_overlap(pa, pb) == g.polygons_overlap(pb, pa)  # symmetric
        assert g.polygons_touch(pa, pb) == g.polygons_touch(pb, pa)
        assert g.polygons_overlap(pa, pa)  # a rectangle overlaps itself


def test_sub_rectangle_sharing_an_edge_is_an_overlap():
    # The case a vertex-only containment test misses: inner shares the left edge
    # of the outer but its interior is inside — must be detected as overlap.
    outer = _rect(0, 0, 2, 2)
    inner_shared_edge = _rect(0, 0, 1, 2)  # shares x=0 edge, interior inside outer
    assert g.polygons_overlap(outer, inner_shared_edge)


def test_identical_rectangles_overlap():
    r = _rect(1, 1, 3, 2)
    assert g.polygons_overlap(r, r)
