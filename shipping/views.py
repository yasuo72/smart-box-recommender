"""
API views for the box recommendation system.

Thin HTTP layer — parses requests, calls services, formats responses.
No business logic lives here.
"""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from shipping.models import Product, Box, Order, OrderItem
from shipping.services import recommend_box


def index_view(request):
    """Render the interactive warehouse dashboard frontend."""
    products = Product.objects.all().order_by("name")
    boxes = Box.objects.all().order_by("cost")
    return render(request, "shipping/index.html", {
        "products": products,
        "boxes": boxes,
    })



@csrf_exempt
@require_POST
def recommend_box_view(request):
    """
    Recommend the best shipping box for an order.

    POST /api/recommend/
    Body: {"items": [{"product_id": int, "quantity": int}, ...]}

    Returns:
        200: {"recommended_box": {...}} or {"recommended_box": null, "message": "..."}
        400: {"error": "..."}
    """
    # --- Parse JSON body ---
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON in request body."}, status=400)

    # --- Validate top-level structure ---
    if not isinstance(data, dict) or "items" not in data:
        return JsonResponse(
            {"error": "Request body must be a JSON object with an 'items' key."},
            status=400,
        )

    raw_items = data["items"]

    if not isinstance(raw_items, list) or len(raw_items) == 0:
        return JsonResponse(
            {"error": "'items' must be a non-empty list."},
            status=400,
        )

    # --- Validate and resolve each item ---
    order = Order.objects.create()
    order_items = []

    for i, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, dict):
            order.delete()
            return JsonResponse(
                {"error": f"Item at index {i} must be a JSON object."},
                status=400,
            )

        product_id = raw_item.get("product_id")
        quantity = raw_item.get("quantity")

        if product_id is None or quantity is None:
            order.delete()
            return JsonResponse(
                {"error": f"Item at index {i} must include 'product_id' and 'quantity'."},
                status=400,
            )

        if not isinstance(product_id, int) or product_id <= 0:
            order.delete()
            return JsonResponse(
                {"error": f"Item at index {i}: 'product_id' must be a positive integer."},
                status=400,
            )

        if not isinstance(quantity, int) or quantity <= 0:
            order.delete()
            return JsonResponse(
                {"error": f"Item at index {i}: 'quantity' must be a positive integer."},
                status=400,
            )

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            order.delete()
            return JsonResponse(
                {"error": f"Invalid product_id: {product_id}"},
                status=400,
            )

        item = OrderItem.objects.create(order=order, product=product, quantity=quantity)
        order_items.append(item)

    # --- Call service ---
    result = recommend_box(order_items)

    # --- Format response ---
    if result.box is not None:
        return JsonResponse({
            "order_id": order.pk,
            "recommended_box": {
                "id": result.box.pk,
                "name": result.box.name,
                "length": float(result.box.length),
                "width": float(result.box.width),
                "height": float(result.box.height),
                "max_weight": float(result.box.max_weight),
                "cost": float(result.box.cost),
            },
        })
    else:
        return JsonResponse({
            "order_id": order.pk,
            "recommended_box": None,
            "message": result.message,
        })
