# Implementation Plan — Box Recommendation System

Based on [REQUIREMENTS.md](file:///c:/Users/Rohit/assesment/REQUIREMENTS.md).

---

## Milestone 1 — Project Scaffolding & Data Models

**Goal**: Runnable Django project with the database schema in place.

**What to do**:

1. Initialise Django project (`boxshipping`) and app (`shipping`).
2. Define models:

#### [NEW] shipping/models.py

| Model | Fields |
|---|---|
| `Product` | `name` (CharField), `length`, `width`, `height`, `weight` (all DecimalField) |
| `Box` | `name` (CharField), `length`, `width`, `height`, `max_weight` (DecimalField), `cost` (DecimalField) |
| `Order` | `created_at` (DateTimeField, auto) |
| `OrderItem` | `order` (FK → Order), `product` (FK → Product), `quantity` (PositiveIntegerField) |

3. Run `makemigrations` and `migrate`.

**Verification**: `python manage.py check` passes, tables exist in SQLite, models can be created via Django shell.

**Covers**: FR-1, FR-2, FR-3, NFR-1

---

## Milestone 2 — Recommendation Service + Unit Tests

**Goal**: Pure-Python recommendation logic that is fully tested before any HTTP layer exists.

#### [NEW] shipping/services.py

- Function `recommend_box(order) → Box | None`
- Logic:
  1. Compute total weight of the order (sum of `product.weight × quantity`).
  2. Compute required volume envelope — use a simple single-axis stacking heuristic:
     - For each item (respecting quantity), collect individual dimensions.
     - Sort items largest-first for better packing.
     - Sum the largest dimension (height) across items; take the max of the other two dimensions (length, width) across items.
  3. Filter boxes: box dimensions must accommodate the envelope in **any orientation** (sort both box dims and envelope dims, compare element-wise). Box `max_weight ≥ total_weight`.
  4. From eligible boxes, pick the one with the **lowest cost**.
  5. Return `None` if no box fits.

#### [NEW] shipping/tests/test_services.py

| Test case | Verifies |
|---|---|
| Single product fits smallest box | Happy path |
| Multiple products (quantity > 1) | Weight and dimension stacking |
| No box large enough | Returns `None` with reason |
| No box heavy enough | Returns `None` with reason |
| Multiple boxes fit → cheapest chosen | Cost-optimality |
| Item can fit if box is rotated | Orientation-agnostic matching |

**Verification**: `python manage.py test shipping.tests.test_services` — all pass.

**Covers**: FR-4, NFR-2, NFR-4 (isolated service layer)

---

## Milestone 3 — API Endpoint

**Goal**: Warehouse team (or any client) can POST an order and receive a box recommendation.

#### [NEW] shipping/views.py

- `recommend_box_view` — accepts JSON, calls the service, returns JSON.

**Request** (`POST /api/recommend/`):
```json
{
  "items": [
    {"product_id": 1, "quantity": 2},
    {"product_id": 3, "quantity": 1}
  ]
}
```

**Response** (200):
```json
{
  "recommended_box": {
    "id": 5,
    "name": "Medium Box",
    "length": 40,
    "width": 30,
    "height": 25,
    "max_weight": 10,
    "cost": 3.50
  }
}
```

**Response** (200, no fit):
```json
{
  "recommended_box": null,
  "message": "No available box can fit this order. Total weight: 15 kg, required dimensions: 50×30×40 cm."
}
```

**Error** (400 — bad input):
```json
{
  "error": "Invalid product_id: 99"
}
```

#### [MODIFY] shipping/urls.py / boxshipping/urls.py

Wire up `POST /api/recommend/`.

**Verification**: `python manage.py test shipping.tests.test_views` — test the endpoint via Django test client.

**Covers**: FR-5, NFR-3

---

## Milestone 4 — Django Admin & Seed Data

**Goal**: Warehouse team can manage products and boxes through the admin; demo data available.

#### [NEW] shipping/admin.py

- Register `Product`, `Box`, `Order`, `OrderItem` with the admin site.
- `OrderItem` as inline on `Order`.

#### [NEW] shipping/management/commands/seed_data.py

- Management command `python manage.py seed_data` to populate a handful of sample products and boxes for demo/testing.

**Verification**: Start dev server, log into `/admin/`, create/edit/delete products and boxes. Run `seed_data`, confirm records exist.

**Covers**: FR-6

---

## Milestone 5 — Integration Tests & Polish

**Goal**: End-to-end confidence and clean handoff.

#### [NEW] shipping/tests/test_integration.py

- Seed data → POST `/api/recommend/` → assert correct box returned.
- Edge case: empty items list → 400.
- Edge case: zero quantity → 400.

#### Polish

- Add `README.md` with setup instructions, API usage, and example curl commands.
- Confirm `python manage.py test` runs all tests green.
- Review code for docstrings and clean imports.

**Verification**: `python manage.py test` — full suite passes.

**Covers**: NFR-2, NFR-3, NFR-4

---

## File Map (projected)

```
assesment/
├── REQUIREMENTS.md
├── README.md                          # Milestone 5
├── manage.py                          # Milestone 1
├── boxshipping/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py                        # Milestone 3
│   └── wsgi.py
└── shipping/
    ├── __init__.py
    ├── models.py                      # Milestone 1
    ├── services.py                    # Milestone 2
    ├── views.py                       # Milestone 3
    ├── urls.py                        # Milestone 3
    ├── admin.py                       # Milestone 4
    ├── management/
    │   └── commands/
    │       └── seed_data.py           # Milestone 4
    └── tests/
        ├── __init__.py
        ├── test_services.py           # Milestone 2
        ├── test_views.py              # Milestone 3
        └── test_integration.py        # Milestone 5
```

---

## Requirement Traceability

| Requirement | Milestone |
|---|---|
| FR-1 Product Catalogue | 1 |
| FR-2 Box Inventory | 1 |
| FR-3 Order Representation | 1 |
| FR-4 Box Recommendation | 2 |
| FR-5 API / Interface | 3 |
| FR-6 Data Management | 4 |
| NFR-1 Django | 1 |
| NFR-2 Correctness | 2, 5 |
| NFR-3 Clarity | 3 |
| NFR-4 Maintainability | 2, 5 |
