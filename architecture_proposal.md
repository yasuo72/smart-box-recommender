# Architecture Proposal — Box Recommendation System

Based on [REQUIREMENTS.md](file:///c:/Users/Rohit/assesment/REQUIREMENTS.md). The goal: separate business logic from HTTP so the recommendation engine can be tested without spinning up a server.

---

## The Problem in Architecture Terms

The assignment asks us to do three things:

1. **Store** products and boxes (CRUD)
2. **Compute** which box fits an order at lowest cost (business logic)
3. **Expose** this over HTTP (API)

These are three distinct concerns. If we mix them into one fat `views.py`, we get code that can only be tested through HTTP requests, is hard to read, and is painful to change. The fix is simple: give each concern its own file.

---

## Proposed Layers

```
┌──────────────────────────────────────────────┐
│                   views.py                    │  HTTP boundary
│  Parse request → call service → format JSON   │
└──────────────────┬───────────────────────────┘
                   │ calls
┌──────────────────▼───────────────────────────┐
│                 services.py                   │  Business logic
│  recommend_box(): filter, sort, select        │
└──────────────────┬───────────────────────────┘
                   │ queries
┌──────────────────▼───────────────────────────┐
│                 models.py                     │  Data layer
│  Product, Box, Order, OrderItem               │
└──────────────────────────────────────────────┘
```

### Layer 1: Models (`models.py`) — *What the data looks like*

**Responsibility**: Define database tables, field types, constraints, and string representations.

**Contains**:
- `Product` — name, length, width, height, weight
- `Box` — name, length, width, height, max_weight, cost
- `Order` — created_at (timestamp)
- `OrderItem` — FK to Order, FK to Product, quantity

**Does NOT contain**: Business rules, computations, or anything that references HTTP.

**Why this layer exists**: Django's ORM already gives us a clean data access pattern. Models should stay as pure schema definitions. If you put recommendation logic in a model method like `Order.get_best_box()`, you couple data storage to business rules — making both harder to change and test independently.

---

### Layer 2: Services (`services.py`) — *What the system does*

**Responsibility**: All business logic. This is where the actual recommendation algorithm lives.

**Contains**:
```
recommend_box(items: list[OrderItem]) → RecommendationResult
```

The function:
1. Computes total weight across all items × quantities
2. Computes a dimension envelope (packing heuristic)
3. Queries all boxes from DB
4. Filters: box must fit the envelope (in any rotation) AND support the weight
5. Selects the cheapest eligible box
6. Returns the box, or `None` with a reason

**Does NOT contain**: HTTP request/response handling. No `JsonResponse`, no `request.body`, no status codes.

**Why this layer exists**: This is the core of the assignment — the thing that actually gets evaluated. By isolating it:

- **Testable independently**: You can write `test_services.py` that creates a few model objects, calls `recommend_box()`, and asserts the result. No HTTP client, no URL routing, no JSON parsing. Tests run fast and read clearly.
- **Reusable**: If tomorrow you need a management command that batch-processes orders, you call the same function. If you add a Django Admin action "Recommend box for this order," same function.
- **Readable**: A reviewer opens `services.py` and sees the algorithm. They don't have to mentally filter out request parsing or error formatting.

---

### Layer 3: Views (`views.py`) — *How the outside world talks to us*

**Responsibility**: HTTP translation layer. Convert an HTTP request into a service call, then convert the result back into an HTTP response.

**Contains**:
```
recommend_box_view(request) → JsonResponse
```

The function:
1. Validates the request method is POST
2. Parses JSON body
3. Validates input shape (product_id exists, quantity is positive)
4. Calls `recommend_box()` from the service layer
5. Formats the result as JSON with the appropriate status code

**Does NOT contain**: Filtering logic, cost comparison, dimension calculations — none of that.

**Why this layer exists**: HTTP is a delivery mechanism, not business logic. Views handle things like "what happens when the JSON is malformed?" or "what status code do we return?" These are HTTP concerns. By keeping views thin:

- **Swappable**: If you later want DRF serializers or a GraphQL endpoint, you replace `views.py` without touching the algorithm.
- **Focused tests**: `test_views.py` only checks HTTP contract — "did I get a 200?", "is the JSON shaped correctly?", "do I get a 400 for bad input?" The algorithm correctness is already proven in `test_services.py`.

---

## Data Flow: A Concrete Example

A warehouse worker sends a request for an order with 2x Widget and 1x Gadget:

```
POST /api/recommend/
{"items": [{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}]}
```

```
views.py                          services.py                     models.py
────────                          ───────────                     ─────────
1. Parse JSON body
2. Validate: product_id           
   exists? quantity > 0?
3. Build OrderItem list
4. ──── call ────────────→  5. Sum weights:
                                2×0.5 + 1×1.2 = 2.2 kg
                            6. Compute envelope:
                                stack heights, max L/W
                            7. ──── query ──────────→  8. Box.objects.all()
                            9. Filter: fits? strong       
                                enough?                  
                            10. Sort by cost, pick     
                                cheapest               
                            11. Return Box instance    
12. ← result ─────────────
13. Format JSON:
    {"recommended_box": {...}}
14. Return JsonResponse(200)
```

Notice: steps 5–11 have zero knowledge of HTTP. That's the whole point.

---

## Testing Payoff

This separation gives us three independent, focused test suites:

| Test file | Tests | Can run without |
|---|---|---|
| `test_models.py` | Fields exist, constraints hold, `__str__` works | Services, Views, HTTP |
| `test_services.py` | Algorithm picks correct box for every edge case | Views, HTTP |
| `test_views.py` | Correct status codes, JSON shape, error format | Algorithm details (mocked or trivial data) |
| `test_integration.py` | Full POST → correct box (smoke test) | Nothing — exercises everything |

**The critical tests are in `test_services.py`.** If the recommendation algorithm is correct, the rest is plumbing. This architecture makes those critical tests the easiest to write and the fastest to run.

---

## What I'm NOT Adding (and Why)

| Pattern | Why not |
|---|---|
| **Serializers / DRF** | One endpoint. `json.loads` + `JsonResponse` is simpler and avoids a dependency. |
| **Repository pattern** | Our service calls `Box.objects.all()` directly. Adding an abstraction layer over Django's ORM for 2 queries is ceremony without benefit. |
| **DTOs / data classes** | The service can return the `Box` model instance directly. No need for a translation layer when the consumer (view) just reads attributes off it. |
| **Separate validators module** | Input validation is 5–10 lines in the view. A dedicated module would be more code than the validation itself. |
| **Signals / events** | No cross-cutting concerns that warrant decoupled event handling. |

Each of these would be reasonable in a larger system. Here, they'd add complexity without solving a real problem.

---

## Summary

Three files, three responsibilities, one clear direction of dependency:

```
views.py  →  services.py  →  models.py
  HTTP         Logic           Data
```

Approve this architecture and I'll start building from Milestone 1.
