"""
Box recommendation service.

Pure business logic — no HTTP concepts. Given an order's items,
recommends the lowest-cost box that fits all items by dimensions and weight.

Packing heuristic (Assumption A-2):
    Items are stacked along one axis. Heights are summed, the maximum
    length and width across all items define the footprint. Both item
    and box dimensions are sorted before comparison so items can fit
    in any orientation.
"""

from decimal import Decimal
from typing import List, NamedTuple, Optional, Tuple

from shipping.models import Box, OrderItem


class RecommendationResult(NamedTuple):
    """Result of a box recommendation attempt."""
    box: Optional[Box]
    total_weight: Decimal
    required_dims: Tuple[Decimal, Decimal, Decimal]  # sorted (small, mid, large)
    message: str


def _compute_order_envelope(
    items: List[OrderItem],
) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
    """
    Compute the total weight and dimension envelope for a list of order items.

    Packing strategy:
        - Each item's 3 dimensions are sorted smallest-to-largest.
        - dim1 (smallest) and dim2 (middle) take the MAX across all items
          (these define the footprint).
        - dim3 (largest) is SUMMED across all items × quantity
          (items are stacked along the tallest axis).

    Returns:
        (total_weight, dim1, dim2, dim3) where dims are sorted ascending.
    """
    total_weight = Decimal("0")
    max_dim1 = Decimal("0")  # smallest dimension (max across items)
    max_dim2 = Decimal("0")  # middle dimension (max across items)
    sum_dim3 = Decimal("0")  # largest dimension (summed, stacking axis)

    for item in items:
        product = item.product
        dims = sorted([product.length, product.width, product.height])

        total_weight += product.weight * item.quantity

        max_dim1 = max(max_dim1, dims[0])
        max_dim2 = max(max_dim2, dims[1])
        sum_dim3 += dims[2] * item.quantity

    return total_weight, max_dim1, max_dim2, sum_dim3


def _box_fits(
    box: Box,
    required_dims: Tuple[Decimal, Decimal, Decimal],
    total_weight: Decimal,
) -> bool:
    """Check if a box can accommodate the required dimensions and weight."""
    box_dims = sorted([box.length, box.width, box.height])

    # Element-wise comparison: each required dimension must fit
    # within the corresponding box dimension (both sorted ascending).
    dims_fit = all(
        req <= box_dim
        for req, box_dim in zip(required_dims, box_dims)
    )

    weight_fits = total_weight <= box.max_weight

    return dims_fit and weight_fits


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

    total_weight, dim1, dim2, dim3 = _compute_order_envelope(items)
    required_dims = (dim1, dim2, dim3)

    # Fetch all boxes, ordered by cost (cheapest first).
    all_boxes = Box.objects.all().order_by("cost")

    for box in all_boxes:
        if _box_fits(box, required_dims, total_weight):
            return RecommendationResult(
                box=box,
                total_weight=total_weight,
                required_dims=required_dims,
                message=f"Recommended: {box.name}",
            )

    # No box fits.
    return RecommendationResult(
        box=None,
        total_weight=total_weight,
        required_dims=required_dims,
        message=(
            f"No available box can fit this order. "
            f"Total weight: {total_weight} kg, "
            f"required dimensions: {dim1}×{dim2}×{dim3} cm."
        ),
    )
