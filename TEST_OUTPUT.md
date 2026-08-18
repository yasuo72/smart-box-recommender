# Test Run Output

Command: `python manage.py test -v 2`
Environment: Python 3.9.2, Django 4.2 LTS, SQLite (in-memory test database)
Date: August 19, 2026

---

```text
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Found 51 test(s).
Operations to perform:
  Synchronize unmigrated apps: messages, staticfiles
  Apply all migrations: admin, auth, contenttypes, sessions, shipping
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying sessions.0001_initial... OK
  Applying shipping.0001_initial... OK
System check identified no issues (0 silenced).
test_creates_order_record (shipping.tests.test_integration.IntegrationTests)
The API should persist an Order with OrderItems. ... ok
test_empty_items_returns_400 (shipping.tests.test_integration.IntegrationTests)
Empty items list should be rejected. ... ok
test_heavy_order_no_fit (shipping.tests.test_integration.IntegrationTests)
3 monitor stands (10.5 kg) exceed the large box max_weight (10 kg). ... ok
test_keyboard_needs_medium_box (shipping.tests.test_integration.IntegrationTests)
A keyboard (45cm) won't fit in the small box, should get medium. ... ok
test_mixed_order_gets_appropriate_box (shipping.tests.test_integration.IntegrationTests)
Mouse + keyboard together should fit in the large box. ... ok
test_single_small_item_gets_cheapest_box (shipping.tests.test_integration.IntegrationTests)
A single mouse should fit in the Small Box (cheapest). ... ok
test_zero_quantity_returns_400 (shipping.tests.test_integration.IntegrationTests)
Zero quantity should be rejected. ... ok
test_empty_items_list (shipping.tests.test_services.RecommendBoxTests)
An empty items list should return None with an appropriate message. ... ok
test_exact_fit (shipping.tests.test_services.RecommendBoxTests)
A product that exactly matches box dimensions should fit. ... ok
test_item_fits_when_box_is_rotated (shipping.tests.test_services.RecommendBoxTests)
A tall, narrow product should fit in a wide, short box ... ok
test_mixed_products_in_order (shipping.tests.test_services.RecommendBoxTests)
An order with different products should sum weights and stack correctly. ... ok
test_multiple_products_with_quantity (shipping.tests.test_services.RecommendBoxTests)
Weight and stacking dimensions should account for quantity. ... ok
test_no_boxes_in_database (shipping.tests.test_services.RecommendBoxTests)
When no boxes exist at all, result.box should be None. ... ok
test_picks_cheapest_box_when_multiple_fit (shipping.tests.test_services.RecommendBoxTests)
When multiple boxes fit, the cheapest one should be selected. ... ok
test_result_includes_dimensions_and_weight (shipping.tests.test_services.RecommendBoxTests)
The result should include computed total weight and required dimensions. ... ok
test_returns_none_when_no_box_large_enough (shipping.tests.test_services.RecommendBoxTests)
When the order is too large for any box, result.box should be None. ... ok
test_returns_none_when_no_box_strong_enough (shipping.tests.test_services.RecommendBoxTests)
When the total weight exceeds all boxes, result.box should be None. ... ok
test_returns_none_when_quantity_exceeds_weight (shipping.tests.test_services.RecommendBoxTests)
High quantity pushing weight over capacity should result in no fit. ... ok
test_returns_none_when_stacking_exceeds_dimensions (shipping.tests.test_services.RecommendBoxTests)
Many items stacked should exceed box height even if single item fits. ... ok
test_single_product_fits_in_box (shipping.tests.test_services.RecommendBoxTests)
A single product should be placed in the smallest fitting box. ... ok
test_cube_product_in_cube_box_exact (shipping.tests.test_stress.StressTests)
A perfect cube in a same-size cube box -- all dimensions equal. ... ok
test_high_quantity_stacking_overflow (shipping.tests.test_stress.StressTests)
10 thin notebooks (25x20x0.5 cm, 0.2 kg). ... ok
test_mixed_products_dims_overflow_but_weight_ok (shipping.tests.test_stress.StressTests)
Two tall lamps (15x15x45 cm, 1 kg each). Stacked largest dim = 45+45 = 90 cm. ... ok
test_mixed_products_weight_overflow (shipping.tests.test_stress.StressTests)
Laptop (2 kg) + Monitor Stand (3.5 kg) + Keyboard (0.9 kg) = 6.4 kg. ... ok
test_off_by_one_hundredth_fits (shipping.tests.test_stress.StressTests)
Product 9.99 cm should fit in a box with 10.00 cm. ... ok
test_off_by_one_hundredth_too_large (shipping.tests.test_stress.StressTests)
Product 10.01 cm should NOT fit in a box with 10.00 cm max. ... ok
test_paper_thin_product (shipping.tests.test_stress.StressTests)
A poster (60x40x0.01 cm) should fit in a flat box. ... ok
test_product_needs_rotation_to_fit (shipping.tests.test_stress.StressTests)
A yoga mat (180x60x1 cm) in a box (65x5x185 cm). ... ok
test_quantity_pushes_weight_over_but_not_dimensions (shipping.tests.test_stress.StressTests)
5 USB drives (5x2x1 cm, 0.05 kg each) = 0.25 kg, stack height 5 cm. ... ok
test_rotation_cannot_save_one_oversized_dimension (shipping.tests.test_stress.StressTests)
A surfboard (200x60x10 cm) in a box (100x100x100 cm). ... ok
test_same_cost_different_sizes (shipping.tests.test_stress.StressTests)
When two boxes cost the same, either is acceptable (both fit). ... ok
test_single_item_fits_but_quantity_two_does_not (shipping.tests.test_stress.StressTests)
One book (20x15x3 cm) fits in box (25x20x5 cm). ... ok
test_skips_cheaper_box_that_doesnt_fit (shipping.tests.test_stress.StressTests)
Cheap box is too small, expensive box fits. Must pick expensive. ... ok
test_two_dimensions_fit_third_does_not (shipping.tests.test_stress.StressTests)
Monitor (60x40x5 cm) in box (50x50x50 cm). ... ok
test_very_long_narrow_product (shipping.tests.test_stress.StressTests)
A fishing rod (1x1x150 cm) needs a box with at least 150 cm in one dim. ... ok
test_weight_exactly_at_limit (shipping.tests.test_stress.StressTests)
Total weight exactly equal to max_weight should fit. ... ok
test_weight_one_hundredth_over_limit (shipping.tests.test_stress.StressTests)
Total weight 5.01 kg should NOT fit in box with 5.00 kg limit. ... ok
test_zero_cost_box_is_valid (shipping.tests.test_stress.StressTests)
A free sample box (cost=0) should be selected if it fits. ... ok
test_index_view_renders_successfully (shipping.tests.test_views.RecommendBoxViewTests)
GET / should render the index.html template with 200 OK. ... ok
test_rejects_empty_items_list (shipping.tests.test_views.RecommendBoxViewTests)
Empty items list should return 400. ... ok
test_rejects_get_request (shipping.tests.test_views.RecommendBoxViewTests)
GET requests should return 405 Method Not Allowed. ... ok
test_rejects_invalid_json (shipping.tests.test_views.RecommendBoxViewTests)
Malformed JSON should return 400. ... ok
test_rejects_invalid_product_id (shipping.tests.test_views.RecommendBoxViewTests)
Non-existent product_id should return 400. ... ok
test_rejects_missing_items_key (shipping.tests.test_views.RecommendBoxViewTests)
Request without 'items' key should return 400. ... ok
test_rejects_missing_quantity (shipping.tests.test_views.RecommendBoxViewTests)
Item without quantity should return 400. ... ok
test_rejects_negative_quantity (shipping.tests.test_views.RecommendBoxViewTests)
Negative quantity should return 400. ... ok
test_rejects_non_integer_product_id (shipping.tests.test_views.RecommendBoxViewTests)
String product_id should return 400. ... ok
test_rejects_zero_quantity (shipping.tests.test_views.RecommendBoxViewTests)
Zero quantity should return 400. ... ok
test_response_includes_all_box_fields (shipping.tests.test_views.RecommendBoxViewTests)
The recommended_box object should contain all expected fields. ... ok
test_returns_200_with_recommended_box (shipping.tests.test_views.RecommendBoxViewTests)
A valid order should return 200 with box details. ... ok
test_returns_null_box_when_no_fit (shipping.tests.test_views.RecommendBoxViewTests)
When no box fits, recommended_box is null with a message. ... ok

----------------------------------------------------------------------
Ran 51 tests in 0.087s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
```
