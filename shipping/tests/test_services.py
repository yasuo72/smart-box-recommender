"""
Tests for the box recommendation service.

Tests the core business logic without any HTTP layer.
Each test creates its own data — no fixtures, no seed_data dependency.
"""

from decimal import Decimal

from django.test import TestCase

from shipping.models import Box, Order, OrderItem, Product
from shipping.services import recommend_box


class RecommendBoxTests(TestCase):
    """Test suite for the recommend_box() service function."""

    def _create_product(self, name="Widget", length=10, width=5, height=3, weight=0.5):
        """Helper to create a product with sensible defaults."""
        return Product.objects.create(
            name=name,
            length=Decimal(str(length)),
            width=Decimal(str(width)),
            height=Decimal(str(height)),
            weight=Decimal(str(weight)),
        )

    def _create_box(self, name="Box", length=20, width=15, height=10, max_weight=5, cost=3):
        """Helper to create a box with sensible defaults."""
        return Box.objects.create(
            name=name,
            length=Decimal(str(length)),
            width=Decimal(str(width)),
            height=Decimal(str(height)),
            max_weight=Decimal(str(max_weight)),
            cost=Decimal(str(cost)),
        )

    def _create_order_with_items(self, *product_qty_pairs):
        """
        Helper to create an order with items.

        Args:
            product_qty_pairs: tuples of (product, quantity)

        Returns:
            List of OrderItem instances.
        """
        order = Order.objects.create()
        items = []
        for product, qty in product_qty_pairs:
            item = OrderItem.objects.create(order=order, product=product, quantity=qty)
            items.append(item)
        return items

    # --- Happy path ---

    def test_single_product_fits_in_box(self):
        """A single product should be placed in the smallest fitting box."""
        product = self._create_product(length=10, width=5, height=3, weight=0.5)
        box = self._create_box(length=20, width=15, height=10, max_weight=5, cost=3)
        items = self._create_order_with_items((product, 1))

        result = recommend_box(items)

        self.assertEqual(result.box, box)
        self.assertEqual(result.total_weight, Decimal("0.5"))

    def test_picks_cheapest_box_when_multiple_fit(self):
        """When multiple boxes fit, the cheapest one should be selected."""
        product = self._create_product(length=10, width=5, height=3, weight=0.5)
        expensive_box = self._create_box(name="Expensive", length=30, width=20, height=15, max_weight=10, cost=8)
        cheap_box = self._create_box(name="Cheap", length=20, width=15, height=10, max_weight=5, cost=2)

        items = self._create_order_with_items((product, 1))
        result = recommend_box(items)

        self.assertEqual(result.box, cheap_box)

    def test_multiple_products_with_quantity(self):
        """Weight and stacking dimensions should account for quantity."""
        product = self._create_product(length=10, width=5, height=3, weight=0.5)
        # Product dims sorted: [3, 5, 10]. With qty=3, stacked dim = 10*3 = 30.
        # Envelope: (3, 5, 30). Box must have sorted dims >= (3, 5, 30).
        box = self._create_box(length=30, width=15, height=10, max_weight=5, cost=3)

        items = self._create_order_with_items((product, 3))
        result = recommend_box(items)

        self.assertEqual(result.box, box)
        self.assertEqual(result.total_weight, Decimal("1.5"))

    def test_mixed_products_in_order(self):
        """An order with different products should sum weights and stack correctly."""
        widget = self._create_product(name="Widget", length=10, width=5, height=3, weight=0.5)
        gadget = self._create_product(name="Gadget", length=8, width=6, height=4, weight=1.0)
        box = self._create_box(length=20, width=15, height=10, max_weight=5, cost=3)

        items = self._create_order_with_items((widget, 1), (gadget, 1))
        result = recommend_box(items)

        # Dims sorted per item: widget [3,5,10], gadget [4,6,8]
        # Envelope: max(3,4)=4, max(5,6)=6, sum(10,8)=18... too tall for box height 10
        # But box dims sorted: [10,15,20], envelope sorted: [4,6,18] → 18 > 20? No, 18 <= 20 ✓
        # Wait: envelope = (4, 6, 18), box = (10, 15, 20) → 4<=10, 6<=15, 18<=20 → fits
        self.assertEqual(result.box, box)
        self.assertEqual(result.total_weight, Decimal("1.5"))

    # --- Rotation ---

    def test_item_fits_when_box_is_rotated(self):
        """
        A tall, narrow product should fit in a wide, short box
        when the box is effectively 'rotated' (dimension-sorted matching).
        """
        # Product: 2×2×15 (tall and narrow)
        product = self._create_product(length=2, width=2, height=15, weight=0.3)
        # Box: 20×3×3 (long and narrow — product fits if laid on its side)
        box = self._create_box(length=20, width=3, height=3, max_weight=5, cost=2)

        items = self._create_order_with_items((product, 1))
        result = recommend_box(items)

        # Product dims sorted: [2, 2, 15], Box dims sorted: [3, 3, 20]
        # 2<=3, 2<=3, 15<=20 → fits
        self.assertEqual(result.box, box)

    # --- No fit scenarios ---

    def test_returns_none_when_no_box_large_enough(self):
        """When the order is too large for any box, result.box should be None."""
        product = self._create_product(length=100, width=100, height=100, weight=0.5)
        self._create_box(length=20, width=15, height=10, max_weight=50, cost=3)

        items = self._create_order_with_items((product, 1))
        result = recommend_box(items)

        self.assertIsNone(result.box)
        self.assertIn("No available box", result.message)

    def test_returns_none_when_no_box_strong_enough(self):
        """When the total weight exceeds all boxes, result.box should be None."""
        product = self._create_product(length=5, width=5, height=5, weight=10)
        self._create_box(length=20, width=15, height=10, max_weight=5, cost=3)

        items = self._create_order_with_items((product, 1))
        result = recommend_box(items)

        self.assertIsNone(result.box)
        self.assertIn("No available box", result.message)

    def test_returns_none_when_quantity_exceeds_weight(self):
        """High quantity pushing weight over capacity should result in no fit."""
        product = self._create_product(length=2, width=2, height=1, weight=1)
        self._create_box(length=20, width=15, height=20, max_weight=5, cost=3)

        items = self._create_order_with_items((product, 10))  # 10 kg > 5 kg max
        result = recommend_box(items)

        self.assertIsNone(result.box)
        self.assertEqual(result.total_weight, Decimal("10"))

    def test_returns_none_when_stacking_exceeds_dimensions(self):
        """Many items stacked should exceed box height even if single item fits."""
        product = self._create_product(length=5, width=5, height=5, weight=0.1)
        self._create_box(length=10, width=10, height=10, max_weight=50, cost=3)

        items = self._create_order_with_items((product, 5))
        # Stacked: 5*5 = 25 cm along largest dim, box max dim = 10 → no fit
        result = recommend_box(items)

        self.assertIsNone(result.box)

    # --- Edge cases ---

    def test_empty_items_list(self):
        """An empty items list should return None with an appropriate message."""
        result = recommend_box([])

        self.assertIsNone(result.box)
        self.assertIn("no items", result.message)

    def test_exact_fit(self):
        """A product that exactly matches box dimensions should fit."""
        product = self._create_product(length=10, width=15, height=20, weight=5)
        box = self._create_box(length=20, width=15, height=10, max_weight=5, cost=3)

        items = self._create_order_with_items((product, 1))
        result = recommend_box(items)

        # Product sorted: [10,15,20], Box sorted: [10,15,20] → exact fit
        self.assertEqual(result.box, box)

    def test_result_includes_dimensions_and_weight(self):
        """The result should include computed total weight and required dimensions."""
        product = self._create_product(length=10, width=5, height=3, weight=0.5)
        self._create_box(length=20, width=15, height=10, max_weight=5, cost=3)

        items = self._create_order_with_items((product, 2))
        result = recommend_box(items)

        self.assertEqual(result.total_weight, Decimal("1.0"))
        # Product dims sorted: [3, 5, 10]. With qty=2: envelope = (3, 5, 20)
        self.assertEqual(result.required_dims, (Decimal("3"), Decimal("5"), Decimal("20")))

    def test_no_boxes_in_database(self):
        """When no boxes exist at all, result.box should be None."""
        product = self._create_product(length=5, width=5, height=5, weight=0.5)
        items = self._create_order_with_items((product, 1))

        result = recommend_box(items)

        self.assertIsNone(result.box)
        self.assertIn("No available box", result.message)
