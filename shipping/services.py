"""
Box recommendation service.

Pure business logic — no HTTP concepts. Given an order's items,
recommends the lowest-cost box that fits all items by dimensions and weight.

Packing heuristic (Assumption A-2):
    Items are packed along one principal axis. To support realistic packing
    (e.g., stacking flat items by thickness, or bundling long items side-by-side),
    the algorithm computes candidate envelopes across 3 single-axis packing strategies:
      1. Short-Axis Stacking (thickness accumulation — standard for books, laptops, clothing)
      2. Mid-Axis Stacking (width accumulation — side-by-side row)
      3. Long-Axis Stacking (length accumulation — end-to-end alignment)
    Both order envelopes and box dimensions are sorted before comparison so items
    can fit in any 3D rotation.
"""

from decimal import Decimal
from typing import List, NamedTuple, Optional, Tuple

from shipping.models import Box, OrderItem


class RecommendationResult(NamedTuple):
    """Result of a box recommendation attempt."""
    box: Optional[Box]
    total_weight: Decimal
    required_dims: Tuple[Decimal, Decimal, Decimal]  # strictly sorted (small, mid, large)
    message: str


def _compute_candidate_envelopes(
    items: List[OrderItem],
) -> Tuple[Decimal, List[Tuple[Decimal, Decimal, Decimal]]]:
    """
    Compute total weight and candidate 1-axis packing envelopes for order items.

    Evaluates 3 single-axis packing orientations:
        - Axis 0 (Shortest axis): sum d0, max d1, max d2 (stack flat items by thickness)
        - Axis 1 (Middle axis): max d0, sum d1, max d2 (bundle side-by-side by width)
        - Axis 2 (Longest axis): max d0, max d1, sum d2 (align end-to-end by length)

    Returns:
        (total_weight, candidate_envelopes) where candidate envelopes are
        strictly sorted ascending (d0 <= d1 <= d2) and ordered by compactness
        (bounding volume, max dimension, sum of dimensions).
    """
    total_weight = Decimal("0")

    # Strategy 0: Accumulate along shortest axis (dims[0])
    s0_sum_d0, s0_max_d1, s0_max_d2 = Decimal("0"), Decimal("0"), Decimal("0")
    # Strategy 1: Accumulate along middle axis (dims[1])
    s1_max_d0, s1_sum_d1, s1_max_d2 = Decimal("0"), Decimal("0"), Decimal("0")
    # Strategy 2: Accumulate along longest axis (dims[2])
    s2_max_d0, s2_max_d1, s2_sum_d2 = Decimal("0"), Decimal("0"), Decimal("0")

    for item in items:
        product = item.product
        dims = sorted([product.length, product.width, product.height])
        qty = Decimal(str(item.quantity))

        total_weight += product.weight * qty

        # Strategy 0: Short-axis stacking
        s0_sum_d0 += dims[0] * qty
        s0_max_d1 = max(s0_max_d1, dims[1])
        s0_max_d2 = max(s0_max_d2, dims[2])

        # Strategy 1: Mid-axis stacking
        s1_max_d0 = max(s1_max_d0, dims[0])
        s1_sum_d1 += dims[1] * qty
        s1_max_d2 = max(s1_max_d2, dims[2])

        # Strategy 2: Long-axis stacking
        s2_max_d0 = max(s2_max_d0, dims[0])
        s2_max_d1 = max(s2_max_d1, dims[1])
        s2_sum_d2 += dims[2] * qty

    # Create strictly sorted (small, mid, large) tuples for each strategy
    env0 = tuple(sorted([s0_sum_d0, s0_max_d1, s0_max_d2]))
    env1 = tuple(sorted([s1_max_d0, s1_sum_d1, s1_max_d2]))
    env2 = tuple(sorted([s2_max_d0, s2_max_d1, s2_sum_d2]))

    # Deduplicate candidate envelopes while preserving order
    candidates = []
    seen = set()
    for env in [env0, env1, env2]:
        if env not in seen:
            seen.add(env)
            candidates.append(env)

    # Sort candidates by compactness: bounding volume -> max dimension -> sum of dimensions
    candidates.sort(key=lambda e: (e[0] * e[1] * e[2], e[2], e[0] + e[1] + e[2]))

    return total_weight, candidates


def _box_fits(
    box: Box,
    candidate_envelopes: List[Tuple[Decimal, Decimal, Decimal]],
    total_weight: Decimal,
) -> Optional[Tuple[Decimal, Decimal, Decimal]]:
    """
    Check if a box can accommodate items under any candidate stacking envelope.

    Returns:
        The first fitting envelope (most compact), or None if no candidate fits.
    """
    if total_weight > box.max_weight:
        return None

    box_dims = sorted([box.length, box.width, box.height])

    for env in candidate_envelopes:
        # Element-wise comparison: both tuples are guaranteed sorted ascending
        if all(req <= box_dim for req, box_dim in zip(env, box_dims)):
            return env

    return None


def recommend_box(items: List[OrderItem]) -> RecommendationResult:
    """
    Recommend the lowest-cost box that fits all items in the order.

    Args:
        items: List of OrderItem instances (must have product and quantity).

    Returns:
        RecommendationResult with the recommended box (or None if no fit).
    """
    if not items:
        return RecommendationResult(
            box=None,
            total_weight=Decimal("0"),
            required_dims=(Decimal("0"), Decimal("0"), Decimal("0")),
            message="Order has no items.",
        )

    total_weight, candidate_envelopes = _compute_candidate_envelopes(items)
    default_dims = candidate_envelopes[0]  # Most compact envelope for failure reporting

    # Fetch all boxes, ordered by cost (cheapest first).
    all_boxes = Box.objects.all().order_by("cost")

    for box in all_boxes:
        fitting_env = _box_fits(box, candidate_envelopes, total_weight)
        if fitting_env is not None:
            return RecommendationResult(
                box=box,
                total_weight=total_weight,
                required_dims=fitting_env,
                message=f"Recommended: {box.name}",
            )

    # No box fits.
    return RecommendationResult(
        box=None,
        total_weight=total_weight,
        required_dims=default_dims,
        message=(
            f"No available box can fit this order. "
            f"Total weight: {total_weight} kg, "
            f"required dimensions: {default_dims[0]}×{default_dims[1]}×{default_dims[2]} cm."
        ),
    )
