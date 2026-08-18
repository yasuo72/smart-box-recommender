# Box Recommendation System

A Django-based system that recommends the most cost-effective shipping box for an ecommerce order based on product dimensions and weight.

## Quick Start

```bash
# 1. Clone and enter the project
cd assesment

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate              # Windows
# source venv/bin/activate         # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up database
python manage.py migrate

# 5. Load sample data
python manage.py seed_data

# 6. Run tests
python manage.py test

# 7. Start dev server
python manage.py runserver
```

## API Usage

### Recommend a Box

**Endpoint**: `POST /api/recommend/`

**Request**:
```bash
curl -X POST http://localhost:8000/api/recommend/ \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}]}'
```

**Success Response** (200):
```json
{
  "order_id": 1,
  "recommended_box": {
    "id": 2,
    "name": "Medium Box",
    "length": 35.0,
    "width": 25.0,
    "height": 15.0,
    "max_weight": 5.0,
    "cost": 3.0
  }
}
```

**No Fit Response** (200):
```json
{
  "order_id": 2,
  "recommended_box": null,
  "message": "No available box can fit this order. Total weight: 15 kg, required dimensions: 25×50×120 cm."
}
```

**Validation Error** (400):
```json
{
  "error": "Invalid product_id: 99"
}
```

## Admin Interface

Access Django admin at `http://localhost:8000/admin/` to manage products and boxes.

Create a superuser first:
```bash
python manage.py createsuperuser
```

## How the Recommendation Works

1. **Compute total weight**: Sum `product.weight × quantity` for all items.
2. **Compute dimension envelope**: Items are stacked along their largest dimension. The other two dimensions take the maximum across all items.
3. **Match boxes**: Both item envelope and box dimensions are sorted, then compared element-wise. This allows items to fit in any orientation.
4. **Select cheapest**: Among all boxes that fit (dimensions + weight), the lowest-cost box is returned.

## Project Structure

```
├── manage.py
├── requirements.txt
├── boxshipping/            # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── shipping/               # Main app
    ├── models.py           # Product, Box, Order, OrderItem
    ├── services.py         # Recommendation algorithm
    ├── views.py            # API endpoint
    ├── urls.py             # URL routing
    ├── admin.py            # Admin registrations
    ├── management/
    │   └── commands/
    │       └── seed_data.py
    └── tests/
        ├── test_services.py
        ├── test_views.py
        └── test_integration.py
```

## Running Tests

```bash
# All tests (50 tests across unit, view, integration, and stress suites)
python manage.py test

# By layer
python manage.py test shipping.tests.test_services      # Business logic (13 tests)
python manage.py test shipping.tests.test_views          # API contract & validation (12 tests)
python manage.py test shipping.tests.test_integration    # End-to-end database flows (7 tests)
python manage.py test shipping.tests.test_stress         # Adversarial & boundary stress tests (18 tests)
```

## Documentation & Submission Deliverables

- [REQUIREMENTS.md](file:///c:/Users/Rohit/assesment/REQUIREMENTS.md) — Source-of-truth functional & non-functional requirements.
- [AI_USAGE.md](file:///c:/Users/Rohit/assesment/AI_USAGE.md) — Tools, prompts, accepted/rejected design decisions, AI mistakes, verification steps.
- [TEST_OUTPUT.md](file:///c:/Users/Rohit/assesment/TEST_OUTPUT.md) — Captured terminal output of the test run (50/50 passing).
- [DEVELOPMENT.md](file:///c:/Users/Rohit/assesment/DEVELOPMENT.md) — Architecture rules, conventions, and design decisions.
- [LEARNINGS.md](file:///c:/Users/Rohit/assesment/LEARNINGS.md) — Candidate reflections and personal takeaways.

## Tech Stack

- Python 3.9+
- Django 4.2 (LTS)
- SQLite (default)
