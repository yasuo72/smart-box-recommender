# 📦 Smart Box Recommender

[![Django CI](https://github.com/yasuo72/smart-box-recommender/actions/workflows/ci.yml/badge.svg)](https://github.com/yasuo72/smart-box-recommender/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/Django-4.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![Tests](https://img.shields.io/badge/Tests-51%20passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)]()

> A robust, service-oriented Django application that analyzes multi-item ecommerce orders and recommends the most cost-effective shipping box based on physical dimensions, item orientations, stacking envelopes, and maximum weight capacities.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture & Design](#-architecture--design)
- [Packing Algorithm & Trade-offs](#-packing-algorithm--trade-offs)
- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [Interactive Frontend Assistant](#-interactive-frontend-assistant)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Repository & Submission Deliverables](#-repository--submission-deliverables)

---

## 🔍 Overview

When a customer places an ecommerce order containing multiple products, warehouse fulfillment teams need to know the optimal shipping box to select. Choosing a box that is too small damages goods, while choosing a box that is unnecessarily large or expensive inflates shipping overhead.

**Smart Box Recommender** solves this by:
1. Aggregating multi-item product quantities, weights, and 3D dimensions.
2. Computing a conservative stacking envelope and total order mass.
3. Evaluating warehouse box inventory using an orientation-agnostic comparison technique.
4. Selecting the lowest-cost box that satisfies both volumetric constraints and weight limits.

---

## ✨ Key Features

- **Isolated Service Layer**: Business logic lives strictly in `shipping/services.py`, fully decoupled from HTTP views for testability and portability.
- **Orientation-Agnostic 3D Fitting**: Employs an element-wise sorted dimension check to evaluate item orientations without brute-force matrix rotations.
- **Decimal Precision**: Built using `DecimalField` and database validation constraints to eliminate floating-point precision issues at boundary thresholds (e.g., `10.00 cm` vs. `10.01 cm`).
- **RESTful API**: Clean JSON endpoint with detailed validation and structured error feedback.
- **Interactive Warehouse Dashboard**: Modern, responsive Vanilla CSS web UI for warehouse operators to build orders and test packaging recommendations in real-time.
- **Automated CI/CD**: Matrix testing on Python 3.9, 3.10, 3.11, and 3.12 via GitHub Actions.

---

## 🏗 Architecture & Design

The project follows a clean 3-tier architectural separation:

```text
┌─────────────────────────────────────────────────────────┐
│                     HTTP / Views                        │
│          (shipping/views.py & index.html)               │
│  - JSON request parsing & validation (HTTP 200/400/405) │
│  - Formats responses & renders dashboard                │
└───────────────────────────┬─────────────────────────────┘
                            │ Calls pure Python function
┌───────────────────────────▼─────────────────────────────┐
│                    Service Layer                        │
│                (shipping/services.py)                   │
│  - Stacking heuristic & envelope calculation            │
│  - Element-wise dimension sorting (3D rotation)         │
│  - Cost-optimal box selection                           │
└───────────────────────────┬─────────────────────────────┘
                            │ Queries schema
┌───────────────────────────▼─────────────────────────────┐
│                     Data Layer                          │
│                (shipping/models.py)                     │
│  - Product, Box, Order, OrderItem models                │
│  - DecimalField precision & database constraints        │
└─────────────────────────────────────────────────────────┘
```

---

## 📐 Packing Algorithm & Trade-offs

### 1. Dimension Sorting for 3D Rotation
A rectangular cuboid can be rotated into 6 spatial orientations. Rather than generating all permutations, both the item's computed envelope dimensions and the candidate box's internal dimensions are sorted in ascending order:
$$\text{item} = [d_1, d_2, d_3], \quad \text{box} = [b_1, b_2, b_3] \quad (\text{where } d_1 \le d_2 \le d_3 \text{ and } b_1 \le b_2 \le b_3)$$
The box accommodates the item if and only if:
$$d_1 \le b_1 \land d_2 \le b_2 \land d_3 \le b_3 \land W_{\text{total}} \le W_{\text{box\_max}}$$

### 2. Single-Axis Stacking Heuristic
- **Strategy**: Items are stacked along their tallest dimension (heights summed), while the base footprint takes the maximum length and width across all items.
- **Trade-off**: This approach is conservative and deterministic. While it may occasionally recommend a slightly larger box compared to complex 3D bin-packing (NP-hard), it guarantees that items will physically fit and provides predictable packaging behavior for warehouse staff.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ (Python 3.9 through 3.12 supported)
- Git

### Installation & Run

```bash
# 1. Clone the repository
git clone https://github.com/yasuo72/smart-box-recommender.git
cd smart-box-recommender

# 2. Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Populate sample products & boxes
python manage.py seed_data

# 6. Run the test suite
python manage.py test

# 7. Start the local server
python manage.py runserver
```

The application will be live at `http://127.0.0.1:8000/`.

---

## 📡 API Documentation

### `POST /api/recommend/`
Recommends the best shipping box for a list of items.

#### Request Headers
| Header | Value |
|---|---|
| `Content-Type` | `application/json` |

#### Request Body
```json
{
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 4, "quantity": 1 }
  ]
}
```

#### Success Response (`200 OK`)
```json
{
  "order_id": 1,
  "recommended_box": {
    "id": 3,
    "name": "Large Box",
    "length": 50.0,
    "width": 35.0,
    "height": 25.0,
    "max_weight": 10.0,
    "cost": 5.5
  }
}
```

#### No-Fit Response (`200 OK`)
```json
{
  "order_id": 2,
  "recommended_box": null,
  "message": "No available box can fit this order. Total weight: 15.5 kg, required dimensions: 25×50×120 cm."
}
```

#### Error Response (`400 Bad Request`)
```json
{
  "error": "Item at index 0: 'product_id' must be a positive integer."
}
```

---

## 🖥 Interactive Frontend Assistant

Access the interactive web UI at **`http://localhost:8000/`**:

- **Order Builder**: Select catalog products, customize quantities, and view live order lines.
- **Packaging Visualizer**: Immediate visual breakdown of recommended box, cost, max weight, and stacking envelope.
- **Inventory Reference**: Real-time warehouse box catalog table.
- **Django Admin**: Manage products, boxes, and historical orders at `http://localhost:8000/admin/`.

---

## 🧪 Testing & Quality Assurance

The project includes **51 automated tests** covering multiple testing layers:

```bash
# Run all tests
python manage.py test -v 2

# Run by layer
python manage.py test shipping.tests.test_services      # Business logic & algorithm (13 tests)
python manage.py test shipping.tests.test_views          # API contract & validation (13 tests)
python manage.py test shipping.tests.test_integration    # End-to-end database persistence (7 tests)
python manage.py test shipping.tests.test_stress         # Boundary & adversarial cases (18 tests)
```

### Stress Testing Coverage
- **Boundary Decimals**: `10.00 cm` vs `10.01 cm`, `5.00 kg` vs `5.01 kg`.
- **Rotation Traps**: Products fitting only in specific rotated orientations (e.g., yoga mats, fishing rods).
- **Quantity Overflows**: Single-item fit vs. multi-item height/weight capacity breaches.
- **Equal-Cost & Zero-Cost Boxes**: Tiebreaker resolution and free sample box handling.

Full test execution logs are available in [`TEST_OUTPUT.md`](TEST_OUTPUT.md).

---

## 📚 Repository & Submission Deliverables

| Deliverable | Description | Link |
|---|---|---|
| **Requirements** | Source-of-truth functional & non-functional requirements | [`REQUIREMENTS.md`](REQUIREMENTS.md) |
| **AI Usage Report** | Transparent report covering prompts, accepted/rejected designs, and AI mistakes | [`AI_USAGE.md`](AI_USAGE.md) |
| **Learnings** | Personal reflection on heuristics, architecture, and environment constraints | [`LEARNINGS.md`](LEARNINGS.md) |
| **Test Run Output** | Captured terminal output showing 51/51 passing tests | [`TEST_OUTPUT.md`](TEST_OUTPUT.md) |
| **Engineering Guide** | Architecture rules, conventions, and implementation decisions | [`DEVELOPMENT.md`](DEVELOPMENT.md) |
| **Conversation Transcript** | Full, chronological session transcript | [`chat-transcript.md`](chat-transcript.md) |
| **CI/CD Pipeline** | GitHub Actions multi-version Python test workflow | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |

---

## 📄 License

This project is licensed under the MIT License.
