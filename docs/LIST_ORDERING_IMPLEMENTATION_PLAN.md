# List Ordering Implementation Plan

## Overview
This plan implements a comprehensive solution for ordering categories and products within lists. The solution will allow admins to specify the exact order of categories and products within each category for any given list.

## Architecture
- **List-Category Ordering**: Each list can have categories in a specific order
- **Product-Category Ordering**: Each category within a list can have products in a specific order
- **Stock Management**: Products maintain their stock information per list
- **API Design**: RESTful endpoints for managing ordering

---

## Phase 1: Database Schema & Models

### Step 1.1: Update Database Schema
- [x] Update `db/schema.sql` to add new ordering tables
- [x] Add `liste_au_categorii` table for list-category ordering
- [x] Add `liste_au_produse_ordered` table for list-product ordering within categories
- [x] Add appropriate indexes for performance
- [x] Add foreign key constraints

### Step 1.2: Create SQLAlchemy Models
- [x] Create `app/models/list_category.py` for ListCategory model
- [x] Create `app/models/list_product_ordered.py` for ListProductOrdered model
- [x] Update `app/models/list.py` to include new relationships
- [x] Add proper imports in `app/models/__init__.py`

### Step 1.3: Update Database Schema Documentation
- [x] Update `db/schema.sql` to include new tables
- [x] Add comments explaining the ordering system
- [x] Document the relationship between tables

---

## Phase 2: Core Service Layer

### Step 2.1: Create List Category Service
- [x] Create `app/services/list_category.py`
- [x] Implement `get_list_categories_ordered(db, list_id)` function
- [x] Implement `add_category_to_list(db, list_id, category_id, position)` function
- [x] Implement `update_category_position(db, list_id, category_id, new_position)` function
- [x] Implement `remove_category_from_list(db, list_id, category_id)` function
- [x] Add proper error handling and validation

### Step 2.2: Create List Product Ordered Service
- [x] Create `app/services/list_product_ordered.py`
- [x] Implement `get_list_products_by_category(db, list_id)` function
- [x] Implement `add_product_to_category(db, list_id, product_id, category_id, position)` function
- [x] Implement `update_product_position(db, list_id, product_id, new_position)` function
- [x] Implement `move_product_between_categories(db, list_id, product_id, new_category_id, position)` function
- [x] Implement `remove_product_from_list(db, list_id, product_id)` function
- [x] Add proper error handling and validation

### Step 2.3: Replace Existing List Product Service
- [x] Replace `app/services/list_product.py` with new ordered structure
- [x] Update `get_list_products()` to return ordered data using new tables
- [x] Remove old functions that are no longer needed
- [x] Update any imports that reference the old service

---

## Phase 3: API Endpoints

### Step 3.1: Create List Category Endpoints
- [ ] Create `app/api/endpoints/list_categories.py`
- [ ] Implement `GET /api/v1/liste/{list_id}/categories` - Get ordered categories
- [ ] Implement `POST /api/v1/liste/{list_id}/categories/{category_id}` - Add category at position
- [ ] Implement `PUT /api/v1/liste/{list_id}/categories/{category_id}/position` - Update category position
- [ ] Implement `DELETE /api/v1/liste/{list_id}/categories/{category_id}` - Remove category
- [ ] Add proper authentication and authorization
- [ ] Add comprehensive error handling

### Step 3.2: Create List Product Ordered Endpoints
- [ ] Create `app/api/endpoints/list_products_ordered.py`
- [ ] Implement `GET /api/v1/liste/{list_id}/products/ordered` - Get products grouped by category
- [ ] Implement `POST /api/v1/liste/{list_id}/categories/{category_id}/products/{product_id}` - Add product to category
- [ ] Implement `PUT /api/v1/liste/{list_id}/products/{product_id}/position` - Update product position
- [ ] Implement `PUT /api/v1/liste/{list_id}/products/{product_id}/category` - Move product to different category
- [ ] Implement `DELETE /api/v1/liste/{list_id}/products/{product_id}` - Remove product from list
- [ ] Add proper authentication and authorization
- [ ] Add comprehensive error handling

### Step 3.3: Update API Router
- [ ] Update `app/api/api.py` to include new endpoints
- [ ] Add proper route prefixes and tags
- [ ] Update API documentation

---

## Phase 4: Schemas & Validation

### Step 4.1: Create List Category Schemas
- [ ] Create `app/schemas/list_category.py`
- [ ] Define `ListCategoryCreate` schema
- [ ] Define `ListCategoryUpdate` schema
- [ ] Define `ListCategoryResponse` schema
- [ ] Add proper validation rules

### Step 4.2: Create List Product Ordered Schemas
- [ ] Create `app/schemas/list_product_ordered.py`
- [ ] Define `ListProductOrderedCreate` schema
- [ ] Define `ListProductOrderedUpdate` schema
- [ ] Define `ListProductOrderedResponse` schema
- [ ] Add proper validation rules

### Step 4.3: Update Existing Schemas
- [ ] Update `app/schemas/list.py` to include new relationships
- [ ] Update `app/schemas/product.py` if needed
- [ ] Ensure all schemas are properly imported

---

## Phase 5: Database Updates & Testing

### Step 5.1: Update Database Schema
- [ ] Update `db/schema.sql` to replace `liste_au_produse` with new ordering tables
- [ ] Remove old `liste_au_produse` table definition
- [ ] Add new `liste_au_categorii` and `liste_au_produse_ordered` table definitions
- [ ] Update any existing foreign key references

### Step 5.2: Create New Test Data
- [ ] Create `test/test_data/seed_data_ordered.sql` with new table structure
- [ ] Add sample data for ordered categories and products
- [ ] Ensure test data covers various scenarios (empty lists, single category, multiple categories, etc.)

### Step 5.3: Create Integration Tests
- [ ] Create `tests/integration/test_list_categories_api.py`
- [ ] Create `tests/integration/test_list_products_ordered_api.py`
- [ ] Test all CRUD operations for categories
- [ ] Test all CRUD operations for products
- [ ] Test ordering functionality
- [ ] Test error scenarios

---

## Phase 6: Documentation & Cleanup

### Step 6.1: Update API Documentation
- [ ] Update OpenAPI/Swagger documentation
- [ ] Add examples for all new endpoints
- [ ] Document request/response formats
- [ ] Add usage examples

### Step 6.2: Update Code Documentation
- [ ] Add docstrings to all new functions
- [ ] Update existing docstrings where needed
- [ ] Add type hints to all new code
- [ ] Create README updates

### Step 6.3: Remove Old Code
- [ ] Remove old `liste_au_produse` table and related code
- [ ] Remove old `ListProduct` model
- [ ] Remove old list product endpoints
- [ ] Clean up any remaining references to old structure

---

## Phase 7: Performance & Optimization

### Step 7.1: Database Optimization
- [ ] Analyze query performance
- [ ] Add missing indexes if needed
- [ ] Optimize complex queries
- [ ] Add database query logging for monitoring

### Step 7.2: API Performance
- [ ] Add response caching where appropriate
- [ ] Optimize serialization
- [ ] Add pagination for large lists
- [ ] Monitor API response times

---

## Implementation Notes

### Database Schema Details
```sql
-- List-Category ordering
CREATE TABLE `liste_au_categorii` (
  `liste_id` INT NOT NULL,
  `category_id` INT NOT NULL,
  `position` INT NOT NULL,
  PRIMARY KEY (`liste_id`, `category_id`),
  INDEX `idx_liste_categorii_position` (`liste_id`, `position`),
  FOREIGN KEY (`liste_id`) REFERENCES `liste` (`id`),
  FOREIGN KEY (`category_id`) REFERENCES `category` (`id`)
);

-- List-Product ordering within categories
CREATE TABLE `liste_au_produse_ordered` (
  `liste_id` INT NOT NULL,
  `produse_id` INT NOT NULL,
  `category_id` INT NOT NULL,
  `position` INT NOT NULL,
  `stoc_produs` INT NULL,
  PRIMARY KEY (`liste_id`, `produse_id`),
  INDEX `idx_liste_produse_category_position` (`liste_id`, `category_id`, `position`),
  FOREIGN KEY (`liste_id`) REFERENCES `liste` (`id`),
  FOREIGN KEY (`produse_id`) REFERENCES `produse` (`id`),
  FOREIGN KEY (`category_id`) REFERENCES `category` (`id`)
);
```

### API Response Format
```json
{
  "list_id": 1,
  "categories": [
    {
      "id": 2,
      "name": "Category2",
      "position": 0,
      "products": [
        {
          "id": 5,
          "nume": "product5",
          "position": 0,
          "stoc_produs": 10,
          "images": [...]
        },
        {
          "id": 6,
          "nume": "product6",
          "position": 1,
          "stoc_produs": 5,
          "images": [...]
        }
      ]
    }
  ]
}
```

### Key Functions to Implement
- Position management (shifting positions when adding/removing items)
- Validation (ensuring positions are sequential and unique)
- Error handling (invalid positions, non-existent items)
- Performance optimization (efficient queries for large lists)

---

## Success Criteria
- [ ] Admins can create lists with ordered categories
- [ ] Admins can add products to categories in specific order
- [ ] Admins can reorder categories and products via API
- [ ] Frontend receives products in exact admin-specified order
- [ ] All operations are properly validated and error-handled
- [ ] Performance is acceptable for lists with many categories/products
- [ ] All tests pass
- [ ] Documentation is complete and accurate

---

## Estimated Timeline
- **Phase 1**: 1-2 days
- **Phase 2**: 2-3 days  
- **Phase 3**: 2-3 days
- **Phase 4**: 1 day
- **Phase 5**: 2-3 days
- **Phase 6**: 1-2 days
- **Phase 7**: 1-2 days

**Total Estimated Time**: 10-16 days

---

## Risk Mitigation
- **Complexity**: Break down into smaller, manageable steps
- **Data Integrity**: Comprehensive validation and error handling
- **Performance**: Monitor and optimize as needed
- **Testing**: Thorough test coverage for all scenarios
- **Documentation**: Keep documentation updated throughout development 