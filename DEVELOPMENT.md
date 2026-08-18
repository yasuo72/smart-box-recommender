# Development Guide

Single reference for anyone working on the Box Recommendation System.
See [REQUIREMENTS.md](file:///c:/Users/Rohit/assesment/REQUIREMENTS.md) for what we're building and [implementation_plan.md](file:///c:/Users/Rohit/assesment/implementation_plan.md) for the milestone breakdown.

---

## Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate              # Windows
# source venv/bin/activate         # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. Load sample data
python manage.py seed_data

# 5. Run tests
python manage.py test

# 6. Start dev server
python manage.py runserver
```

---

## Development Commands

| Command | Purpose |
|---|---|
| `python manage.py test` | Run full test suite |
| `python manage.py test shipping.tests.test_services` | Run service tests only |
| `python manage.py test shipping.tests.test_views` | Run API tests only |
| `python manage.py makemigrations` | Generate migrations after model changes |
| `python manage.py migrate` | Apply pending migrations |
| `python manage.py seed_data` | Populate demo products and boxes |
| `python manage.py createsuperuser` | Create admin login |
| `python manage.py shell` | Interactive Django shell |
| `python manage.py runserver` | Start dev server at `localhost:8000` |

---

## Project Structure

```
assesment/
├── manage.py
├── requirements.txt
├── REQUIREMENTS.md              # What to build (source of truth)
├── DEVELOPMENT.md               # How to build it (this file)
├── boxshipping/                 # Django project package
│   ├── settings.py              # Project settings (SQLite, DEBUG=True)
│   ├── urls.py                  # Root URL conf — includes shipping.urls
│   └── wsgi.py
└── shipping/                    # Single Django app — all domain logic
    ├── models.py                # Data models (Product, Box, Order, OrderItem)
    ├── services.py              # Business logic (recommend_box)
    ├── views.py                 # HTTP layer — thin wrappers over services
    ├── urls.py                  # App URL patterns (/api/...)
    ├── admin.py                 # Admin site registrations
    ├── management/
    │   └── commands/
    │       └── seed_data.py     # Sample data loader
    └── tests/
        ├── test_models.py       # Model constraints, __str__
        ├── test_services.py     # Recommendation algorithm
        ├── test_views.py        # API contract (status codes, JSON shape)
        └── test_integration.py  # End-to-end flows
```

**One app only.** Everything shipping-related lives in `shipping/`. No splitting into `products/`, `orders/`, `boxes/` — that's over-engineering for this scope.

---

## Architecture Rules

### Layer Responsibilities

```
Request → View → Service → Models/DB
                    ↑
              All logic here
```

| Layer | Does | Does NOT |
|---|---|---|
| **Models** (`models.py`) | Define fields, `__str__`, `Meta`, DB constraints | Contain business logic or validation rules |
| **Services** (`services.py`) | All business logic, computation, orchestration | Import `HttpRequest`/`HttpResponse` or any HTTP concepts |
| **Views** (`views.py`) | Parse request, call service, format response | Contain business logic, DB queries, or computations |

### Why This Matters

- **Testability**: Service tests run without HTTP overhead.
- **Swappability**: Views can be replaced with DRF serializers later without touching logic.
- **Readability**: Each file has one clear purpose.

### Import Direction

```
views.py → services.py → models.py
```

Never the reverse. Models don't import from services. Services don't import from views.

---

## Naming Conventions

| Element | Rule | Example |
|---|---|---|
| Models | Singular PascalCase | `Product`, `Box`, `OrderItem` |
| Fields | snake_case, self-descriptive | `max_weight`, `created_at` |
| Service functions | verb_noun | `recommend_box()` |
| View functions | verb_noun_view | `recommend_box_view()` |
| URL paths | lowercase, trailing slash | `/api/recommend/` |
| Test methods | `test_<scenario>` | `test_picks_cheapest_box_when_multiple_fit` |
| Constants | UPPER_SNAKE_CASE | `MAX_ITEMS_PER_ORDER` |

---

## Validation & Error Handling

### Input Validation → Views

Validate request shape and types before calling any service. Return `400` immediately for bad input.

```python
# Consistent error response shape
{"error": "Each item must include 'product_id' (int) and 'quantity' (positive int)."}
```

### Business Errors → Services

Services raise custom exceptions — never return HTTP responses.

```python
class NoFittingBoxError(Exception):
    """No available box can accommodate the order."""
    pass
```

Views catch these and translate to appropriate HTTP responses.

### Data Integrity → Models

Use field-level constraints (`PositiveIntegerField`, `DecimalField` with `min_value`) for things the database should enforce.

### Rules

- Every error returns structured JSON — never a bare HTML 500.
- Unexpected errors propagate naturally (Django's default 500 is fine for demo).
- Validate early, fail fast, fail clearly.

---

## Key Implementation Decisions

### Box Fitting Algorithm

- **Packing heuristic**: Single-axis stacking. Sum heights, take max of length and width across all items. This is simple, predictable, and sufficient per assumption A-2.
- **Rotation**: Both box and item dimensions are sorted before comparison, so items fit in any orientation.
- **Selection criteria**: Among all boxes that fit (dimensions + weight), pick the **lowest cost**.
- **No fit**: Return `None` with a descriptive message including the computed dimensions and weight.

### Why Not DRF (Django REST Framework)

We have a single endpoint. DRF adds serializers, viewsets, routers, permissions, and content negotiation — none of which we need. Plain `JsonResponse` + `json.loads` keeps the dependency list minimal and the code transparent.

### Why SQLite

Per assumption A-5, this is demo-scale. SQLite is zero-config, ships with Python, and handles the expected data volume. No need for PostgreSQL setup instructions in a hiring assignment.

### Seed Data as Management Command

`seed_data` uses `get_or_create` so it's idempotent — safe to run multiple times. It exists to make the demo immediately usable without manual data entry.

---

## Testing Strategy

### Layer Coverage

| Test file | What to verify | What to skip |
|---|---|---|
| `test_models.py` | Field constraints, `__str__`, model creation | ORM internals |
| `test_services.py` | Algorithm correctness, all edge cases | HTTP behaviour |
| `test_views.py` | Status codes, JSON response shape, error format | Business logic (tested in services) |
| `test_integration.py` | Full seed → request → response flow | Anything already covered above |

### Conventions

- Use `django.test.TestCase` — each test runs in a rolled-back transaction.
- Create test data in `setUp()` or in the test itself. Never depend on fixtures or `seed_data`.
- Test names read as sentences: `test_returns_none_when_all_boxes_too_small`.
- One logical assertion per test (multiple `assert` calls are fine if they verify the same thing).

---

## Environment & Dependencies

### requirements.txt

```
Django==5.1
```

That's it. No unnecessary packages. If Django does it natively, don't add a library.

### Settings

- `DEBUG = True` — this is a demo, not a deployment.
- `SECRET_KEY` in `settings.py` directly — acceptable for a non-deployed assignment.
- `DATABASES` — default SQLite, no env var needed.

---

## Code Style

- **PEP 8** — no linter config needed, just be consistent.
- **Type hints** on all service function signatures (they are the core API).
- **Docstrings** on models, service functions, and the API view. Skip trivially obvious ones.
- **Import order**: stdlib → Django → local, separated by blank lines.
- **No dead code** — don't leave commented-out blocks or unused imports.
