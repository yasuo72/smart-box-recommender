"""
Data models for the box recommendation system.

Four models: Product, Box, Order, OrderItem.
See data_model_design.md for schema rationale.
"""

from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    """A physical product with dimensions and weight."""

    name = models.CharField(max_length=200)
    length = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)],
        help_text="Length in cm"
    )
    width = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)],
        help_text="Width in cm"
    )
    height = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)],
        help_text="Height in cm"
    )
    weight = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)],
        help_text="Weight in kg"
    )

    def __str__(self):
        return f"{self.name} ({self.length}×{self.width}×{self.height} cm, {self.weight} kg)"

    class Meta:
        ordering = ["name"]


class Box(models.Model):
    """A shipping box with internal dimensions, weight capacity, and cost."""

    name = models.CharField(max_length=200)
    length = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)],
        help_text="Internal length in cm"
    )
    width = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)],
        help_text="Internal width in cm"
    )
    height = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)],
        help_text="Internal height in cm"
    )
    max_weight = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)],
        help_text="Maximum weight capacity in kg"
    )
    cost = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
        help_text="Cost per box"
    )

    def __str__(self):
        return (
            f"{self.name} ({self.length}×{self.width}×{self.height} cm, "
            f"max {self.max_weight} kg, ${self.cost})"
        )

    class Meta:
        ordering = ["cost"]
        verbose_name_plural = "boxes"


class Order(models.Model):
    """A customer order that needs a box recommendation."""

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk} ({self.created_at:%Y-%m-%d})"

    class Meta:
        ordering = ["-created_at"]


class OrderItem(models.Model):
    """A line item in an order: references a product with a quantity."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of this product in the order"
    )

    def __str__(self):
        return f"{self.quantity}× {self.product.name} in Order #{self.order_id}"

    class Meta:
        ordering = ["id"]
