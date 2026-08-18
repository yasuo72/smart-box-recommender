"""
Stress tests — adversarial cases designed to break the recommendation logic.

Each test targets a specific assumption or boundary condition with realistic
ecommerce scenarios. If any of these fail, the algorithm has a real bug.
"""

from decimal import Decimal

from django.test import TestCase

from shipping.models import Box, Order, OrderItem, Product
from shipping.services import recommend_box


class StressTests(TestCase):
    """Adversarial tests for the recommendation algorithm."""

    def _product(self, name="P", length=10, width=5, height=3, weight=0.5):
        return Product.objects.create(
            name=name, length=Decimal(str(length)), width=Decimal(str(width)),
            height=Decimal(str(height)), weight=Decimal(str(weight)),
        )

    def _box(self, name="B", length=20, width=15, height=10, max_weight=5, cost=3):
        return Box.objects.create(
            name=name, length=Decimal(str(length)), width=Decimal(str(width)),
            height=Decimal(str(height)), max_weight=Decimal(str(max_weight)),
            cost=Decimal(str(cost)),
        )

    def _items(self, *product_qty_pairs):
        order = Order.objects.create()
        return [
            OrderItem.objects.create(order=order, product=p, quantity=q)
            for p, q in product_qty_pairs
        ]

    # ── Boundary dimensions ──────────────────────────────────────────

    def test_off_by_one_hundredth_too_large(self):
        """Product 10.01 cm should NOT fit in a box with 10.00 cm max."""
        product = self._product(length=10.01, width=5, height=3, weight=0.1)
        self._box(length=10, width=5, height=3, max_weight=5, cost=1)

        result = recommend_box(self._items((product, 1)))
        self.assertIsNone(result.box, "10.01 should not fit in 10.00")

    def test_off_by_one_hundredth_fits(self):
        """Product 9.99 cm should fit in a box with 10.00 cm."""
        product = self._product(length=9.99, width=5, height=3, weight=0.1)
        box = self._box(length=10, width=5, height=3, max_weight=5, cost=1)

        result = recommend_box(self._items((product, 1)))
        self.assertEqual(result.box, box)

    def test_weight_exactly_at_limit(self):
        """Total weight exactly equal to max_weight should fit."""
        product = self._product(weight=5.00, length=5, width=5, height=5)
        box = self._box(max_weight=5.00, length=10, width=10, height=10, cost=1)

        result = recommend_box(self._items((product, 1)))
        self.assertEqual(result.box, box, "Exact weight match should fit (<=, not <)")

    def test_weight_one_hundredth_over_limit(self):
        """Total weight 5.01 kg should NOT fit in box with 5.00 kg limit."""
        product = self._product(weight=5.01, length=5, width=5, height=5)
        self._box(max_weight=5.00, length=10, width=10, height=10, cost=1)

        result = recommend_box(self._items((product, 1)))
        self.assertIsNone(result.box, "5.01 should not fit in 5.00 max")

    # ── Rotation traps ───────────────────────────────────────────────

    def test_product_needs_rotation_to_fit(self):
        """
        A yoga mat (180×60×1 cm) in a box (65×5×185 cm).
        Only fits if dimensions are sorted and compared correctly.
        """
        mat = self._product(name="Yoga Mat", length=180, width=60, height=1, weight=1.5)
        box = self._box(name="Long Flat", length=65, width=5, height=185, max_weight=5, cost=4)
        # Sorted: mat [1, 60, 180], box [5, 65, 185] → 1<=5, 60<=65, 180<=185 ✓

        result = recommend_box(self._items((mat, 1)))
        self.assertEqual(result.box, box)

    def test_rotation_cannot_save_one_oversized_dimension(self):
        """
        A surfboard (200×60×10 cm) in a box (100×100×100 cm).
        Even rotated, 200 > 100 in the largest dimension.
        """
        surfboard = self._product(name="Surfboard", length=200, width=60, height=10, weight=3)
        self._box(name="Big Cube", length=100, width=100, height=100, max_weight=20, cost=10)
        # Sorted: surfboard [10, 60, 200], box [100, 100, 100] → 200 > 100 ✗

        result = recommend_box(self._items((surfboard, 1)))
        self.assertIsNone(result.box)

    def test_two_dimensions_fit_third_does_not(self):
        """
        Monitor (60×40×5 cm) in box (50×50×50 cm).
        Two dims fit, but 60 > 50 in largest. No rotation helps.
        """
        monitor = self._product(name="Monitor", length=60, width=40, height=5, weight=4)
        self._box(name="Cube", length=50, width=50, height=50, max_weight=20, cost=5)
        # Sorted: monitor [5, 40, 60], box [50, 50, 50] → 60 > 50 ✗

        result = recommend_box(self._items((monitor, 1)))
        self.assertIsNone(result.box)

    # ── Quantity stacking traps ──────────────────────────────────────

    def test_single_item_fits_but_quantity_two_does_not(self):
        """
        One book (20×15×3 cm) fits in box (25×20×5 cm).
        Two books stacked = 6 cm tall > 5 cm box height. Should fail.
        """
        book = self._product(name="Book", length=20, width=15, height=3, weight=0.4)
        self._box(name="Slim", length=25, width=20, height=5, max_weight=5, cost=2)
        # 1 book sorted: [3, 15, 20], stacked dim = 20. Box sorted: [5, 20, 25] → 20<=25 ✓
        # 2 books: envelope [3, 15, 40]. Box sorted: [5, 20, 25] → 40 > 25 ✗

        result_one = recommend_box(self._items((book, 1)))
        self.assertIsNotNone(result_one.box, "Single book should fit")

        result_two = recommend_box(self._items((book, 2)))
        self.assertIsNone(result_two.box, "Two books stacked should NOT fit")

    def test_quantity_pushes_weight_over_but_not_dimensions(self):
        """
        5 USB drives (5×2×1 cm, 0.05 kg each) = 0.25 kg, stack height 5 cm.
        Box: 10×10×10 cm, max_weight 0.20 kg. Dimensions fit, weight doesn't.
        """
        usb = self._product(name="USB Drive", length=5, width=2, height=1, weight=0.05)
        self._box(name="Tiny", length=10, width=10, height=10, max_weight=0.20, cost=1)

        result = recommend_box(self._items((usb, 5)))
        self.assertIsNone(result.box, "Weight 0.25 > 0.20 max")

    def test_high_quantity_stacking_overflow(self):
        """
        10 thin notebooks (25×20×0.5 cm, 0.2 kg).
        Stacked: largest dim is 25, ×10 = 250 cm. No realistic box fits.
        """
        notebook = self._product(name="Notebook", length=25, width=20, height=0.5, weight=0.2)
        self._box(name="XL", length=60, width=40, height=35, max_weight=20, cost=8)
        # Sorted: [0.5, 20, 25]. Stacked dim = 25*10 = 250. Envelope: [0.5, 20, 250]
        # Box sorted: [35, 40, 60]. 250 > 60 ✗

        result = recommend_box(self._items((notebook, 10)))
        self.assertIsNone(result.box)

    # ── Multiple boxes — cost selection ──────────────────────────────

    def test_skips_cheaper_box_that_doesnt_fit(self):
        """
        Cheap box is too small, expensive box fits. Must pick expensive.
        """
        product = self._product(length=30, width=20, height=10, weight=2)
        self._box(name="Cheap Small", length=25, width=15, height=8, max_weight=5, cost=1)
        big_box = self._box(name="Expensive Big", length=40, width=30, height=20, max_weight=10, cost=7)

        result = recommend_box(self._items((product, 1)))
        self.assertEqual(result.box, big_box, "Should skip cheap box that doesn't fit")

    def test_zero_cost_box_is_valid(self):
        """A free sample box (cost=0) should be selected if it fits."""
        product = self._product(length=5, width=3, height=2, weight=0.1)
        free_box = self._box(name="Free Sample", length=10, width=10, height=5, max_weight=1, cost=0)
        self._box(name="Paid", length=10, width=10, height=5, max_weight=1, cost=2)

        result = recommend_box(self._items((product, 1)))
        self.assertEqual(result.box, free_box, "Zero-cost box should be chosen")

    def test_same_cost_different_sizes(self):
        """When two boxes cost the same, either is acceptable (both fit)."""
        product = self._product(length=5, width=5, height=5, weight=0.5)
        self._box(name="A", length=10, width=10, height=10, max_weight=5, cost=3)
        self._box(name="B", length=20, width=20, height=20, max_weight=10, cost=3)

        result = recommend_box(self._items((product, 1)))
        self.assertIsNotNone(result.box, "One of the equal-cost boxes should be picked")
        self.assertEqual(float(result.box.cost), 3.0)

    # ── Mixed products in one order ──────────────────────────────────

    def test_mixed_products_weight_overflow(self):
        """
        Laptop (2 kg) + Monitor Stand (3.5 kg) + Keyboard (0.9 kg) = 6.4 kg.
        Box max_weight = 5 kg. Dimensions might fit but weight doesn't.
        """
        laptop = self._product(name="Laptop", length=36, width=25, height=2, weight=2.0)
        stand = self._product(name="Stand", length=50, width=25, height=12, weight=3.5)
        keyboard = self._product(name="Keyboard", length=45, width=15, height=4, weight=0.9)
        self._box(name="Large", length=60, width=40, height=30, max_weight=5, cost=5)

        result = recommend_box(self._items((laptop, 1), (stand, 1), (keyboard, 1)))
        self.assertIsNone(result.box, "Combined weight 6.4 > 5.0 max")
        self.assertEqual(result.total_weight, Decimal("6.4"))

    def test_mixed_products_dims_overflow_but_weight_ok(self):
        """
        Two tall lamps (15×15×45 cm, 1 kg each). Stacked largest dim = 45+45 = 90 cm.
        Box max dim = 60 cm. Weight is fine (2 kg < 10 kg).
        """
        lamp = self._product(name="Desk Lamp", length=15, width=15, height=45, weight=1.0)
        self._box(name="Tall Box", length=20, width=20, height=60, max_weight=10, cost=6)
        # Lamp sorted: [15, 15, 45]. Two lamps: envelope [15, 15, 90].
        # Box sorted: [20, 20, 60]. 90 > 60 ✗

        result = recommend_box(self._items((lamp, 2)))
        self.assertIsNone(result.box)

    # ── Degenerate shapes ────────────────────────────────────────────

    def test_paper_thin_product(self):
        """A poster (60×40×0.01 cm) should fit in a flat box."""
        poster = self._product(name="Poster", length=60, width=40, height=0.01, weight=0.1)
        flat_box = self._box(name="Flat Mailer", length=65, width=45, height=1, max_weight=1, cost=2)

        result = recommend_box(self._items((poster, 1)))
        self.assertEqual(result.box, flat_box)

    def test_cube_product_in_cube_box_exact(self):
        """A perfect cube in a same-size cube box — all dimensions equal."""
        cube = self._product(name="Cube", length=10, width=10, height=10, weight=1)
        cube_box = self._box(name="Cube Box", length=10, width=10, height=10, max_weight=1, cost=3)

        result = recommend_box(self._items((cube, 1)))
        self.assertEqual(result.box, cube_box)

    def test_very_long_narrow_product(self):
        """A fishing rod (1×1×150 cm) needs a box with at least 150 cm in one dim."""
        rod = self._product(name="Fishing Rod", length=1, width=1, height=150, weight=0.5)
        short_box = self._box(name="Short", length=100, width=20, height=20, max_weight=5, cost=3)
        long_box = self._box(name="Long", length=160, width=5, height=5, max_weight=5, cost=6)

        result = recommend_box(self._items((rod, 1)))
        self.assertEqual(result.box, long_box, "Only the long box can accommodate 150 cm")
