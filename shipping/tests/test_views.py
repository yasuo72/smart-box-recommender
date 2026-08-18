"""
Tests for the recommendation API endpoint.

Tests HTTP contract: status codes, JSON shape, error format.
Business logic correctness is already tested in test_services.py.
"""

import json
from decimal import Decimal

from django.test import TestCase, Client

from shipping.models import Box, Product


class RecommendBoxViewTests(TestCase):
    """Test suite for POST /api/recommend/."""

    def setUp(self):
        self.client = Client()
        self.url = "/api/recommend/"

        # Create a product and a box for happy-path tests.
        self.product = Product.objects.create(
            name="Widget", length=Decimal("10"), width=Decimal("5"),
            height=Decimal("3"), weight=Decimal("0.5"),
        )
        self.box = Box.objects.create(
            name="Standard Box", length=Decimal("30"), width=Decimal("20"),
            height=Decimal("15"), max_weight=Decimal("10"), cost=Decimal("3.50"),
        )

    def _post(self, data):
        """Helper to POST JSON to the recommend endpoint."""
        return self.client.post(
            self.url,
            data=json.dumps(data),
            content_type="application/json",
        )

    # --- Index View ---

    def test_index_view_renders_successfully(self):
        """GET / should render the index.html template with 200 OK."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Warehouse Box Recommendation Assistant")
        self.assertContains(response, "Widget")

    # --- Happy path ---

    def test_returns_200_with_recommended_box(self):
        """A valid order should return 200 with box details."""
        response = self._post({
            "items": [{"product_id": self.product.pk, "quantity": 1}]
        })

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("recommended_box", body)
        self.assertIsNotNone(body["recommended_box"])
        self.assertEqual(body["recommended_box"]["name"], "Standard Box")
        self.assertIn("order_id", body)

    def test_response_includes_all_box_fields(self):
        """The recommended_box object should contain all expected fields."""
        response = self._post({
            "items": [{"product_id": self.product.pk, "quantity": 1}]
        })

        box_data = response.json()["recommended_box"]
        expected_fields = {"id", "name", "length", "width", "height", "max_weight", "cost"}
        self.assertEqual(set(box_data.keys()), expected_fields)

    def test_returns_null_box_when_no_fit(self):
        """When no box fits, recommended_box is null with a message."""
        # Create a very large product
        big = Product.objects.create(
            name="Giant", length=Decimal("200"), width=Decimal("200"),
            height=Decimal("200"), weight=Decimal("0.5"),
        )

        response = self._post({
            "items": [{"product_id": big.pk, "quantity": 1}]
        })

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body["recommended_box"])
        self.assertIn("message", body)
        self.assertIn("No available box", body["message"])

    # --- Method validation ---

    def test_rejects_get_request(self):
        """GET requests should return 405 Method Not Allowed."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    # --- Body validation ---

    def test_rejects_invalid_json(self):
        """Malformed JSON should return 400."""
        response = self.client.post(
            self.url, data="not json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_rejects_missing_items_key(self):
        """Request without 'items' key should return 400."""
        response = self._post({"products": []})
        self.assertEqual(response.status_code, 400)
        self.assertIn("items", response.json()["error"])

    def test_rejects_empty_items_list(self):
        """Empty items list should return 400."""
        response = self._post({"items": []})
        self.assertEqual(response.status_code, 400)

    def test_rejects_invalid_product_id(self):
        """Non-existent product_id should return 400."""
        response = self._post({
            "items": [{"product_id": 99999, "quantity": 1}]
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("99999", response.json()["error"])

    def test_rejects_missing_quantity(self):
        """Item without quantity should return 400."""
        response = self._post({
            "items": [{"product_id": self.product.pk}]
        })
        self.assertEqual(response.status_code, 400)

    def test_rejects_zero_quantity(self):
        """Zero quantity should return 400."""
        response = self._post({
            "items": [{"product_id": self.product.pk, "quantity": 0}]
        })
        self.assertEqual(response.status_code, 400)

    def test_rejects_negative_quantity(self):
        """Negative quantity should return 400."""
        response = self._post({
            "items": [{"product_id": self.product.pk, "quantity": -1}]
        })
        self.assertEqual(response.status_code, 400)

    def test_rejects_non_integer_product_id(self):
        """String product_id should return 400."""
        response = self._post({
            "items": [{"product_id": "abc", "quantity": 1}]
        })
        self.assertEqual(response.status_code, 400)
