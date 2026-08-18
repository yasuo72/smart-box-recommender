"""Django admin configuration for the shipping app."""

from django.contrib import admin

from shipping.models import Box, Order, OrderItem, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "length", "width", "height", "weight")
    search_fields = ("name",)


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ("name", "length", "width", "height", "max_weight", "cost")
    list_filter = ("cost",)
    search_fields = ("name",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    raw_id_fields = ("product",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("pk", "created_at")
    inlines = [OrderItemInline]
    readonly_fields = ("created_at",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity")
    list_filter = ("order",)
