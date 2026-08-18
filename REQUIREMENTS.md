# Requirements — Box Recommendation System

## Context

We operate an ecommerce platform. When a customer places an order, the warehouse team needs to know which shipping box should be used. Each product has dimensions and weight. Each box has internal dimensions, maximum weight capacity, and cost. The system recommends the most suitable box for an order.

---

## Functional Requirements

### FR-1 Product Catalogue

- Store products with their **length**, **width**, **height**, and **weight**.
- Each product must have a human-readable name or SKU for identification.

### FR-2 Box Inventory

- Store available shipping boxes with **internal length**, **internal width**, **internal height**, **maximum weight capacity**, and **cost**.
- Each box must have a human-readable name or identifier.

### FR-3 Order Representation

- An order consists of **one or more products** (with quantities).
- The system must accept an order as input to the recommendation engine.

### FR-4 Box Recommendation

- Given an order, the system must recommend the **most suitable box**.
- "Most suitable" means the **lowest-cost box** that can physically contain the order items (all items fit within internal dimensions) **and** support the total weight (total weight ≤ max weight capacity).
- If **no single box** can fit the order, the system must clearly indicate that.

### FR-5 API / Interface

- Expose the recommendation logic through a **Django-based interface** (API endpoint and/or admin-driven workflow) so it can be invoked programmatically or by the warehouse team.

### FR-6 Data Management

- Provide a way to **create, read, update, and delete** products and boxes (Django Admin is sufficient).

---

## Non-Functional Requirements

### NFR-1 Technology Stack

- The system must be built with **Django** (Python).

### NFR-2 Correctness

- The recommendation algorithm must never suggest a box that is too small or exceeds weight capacity.

### NFR-3 Clarity

- When no box fits, the response must include a clear, actionable message (not a silent failure or 500 error).

### NFR-4 Maintainability

- Code should follow standard Django project conventions (apps, models, views/serializers, URL routing).
- The recommendation logic should be isolated in its own service/utility layer, separate from views.

---

## Assumptions

| # | Assumption |
|---|-----------|
| A-1 | Products are treated as **rectangular cuboids**; irregular shapes are not considered. |
| A-2 | Items in an order are **packed along one axis** (stacked/placed without complex 3-D bin-packing optimisation). A reasonable packing heuristic is acceptable. |
| A-3 | The box set is **small enough** (tens to low hundreds) that iterating over all boxes per request is performant — no need for advanced indexing or caching. |
| A-4 | All dimensions and weights use **consistent units** (e.g., cm and kg) — unit conversion is not required. |
| A-5 | A single **SQLite** database (Django default) is sufficient for this scope. |

---

## Constraints

| # | Constraint |
|---|-----------|
| C-1 | The system is a **small/demo-scale** project — production deployment, scaling, and CI/CD are not in scope. |
| C-2 | The recommendation must select from **existing boxes only**; the system does not design custom boxes. |
| C-3 | An order ships in **one box** — multi-box splitting is not required. |

---

## Out of Scope

- User authentication and authorisation beyond Django's built-in admin.
- Payment processing, order lifecycle management, or inventory tracking.
- Real-time carrier rate lookups or shipping label generation.
- Advanced 3-D bin-packing algorithms (NP-hard optimisation).
- Multi-box shipment splitting.
- Frontend customer-facing UI (admin + API is sufficient).
- Internationalisation / multi-currency.
