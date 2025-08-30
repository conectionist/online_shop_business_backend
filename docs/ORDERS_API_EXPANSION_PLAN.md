# Orders API Expansion Plan: Adding Delivery and Payment Methods

## Overview

This document outlines the plan to expand the Orders API to include delivery method and payment method selection when customers place orders. This is a breaking change that will require database schema updates, model changes, and API modifications.

## Current State Analysis

### Existing Orders Table Structure
```sql
CREATE TABLE `comenzi` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nume_client` VARCHAR(50) NOT NULL,
  `data_plasarii` DATETIME NOT NULL,
  `liste_id` INT NOT NULL,
  `order_notes` VARCHAR(500) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
);
```

### Existing Related Tables
- **`modalitati_de_plata`** - Payment methods (id, name, description)
- **`tipuri_livrare`** - Delivery types (id, denumire)
- **`liste_au_tipuri_livrare`** - Many-to-many relationship between lists and delivery types

### Current API Endpoints
- `GET /api/v1/orders/` - List orders (requires auth)
- `POST /api/v1/orders/` - Create order (public)
- `GET /api/v1/orders/{id}` - Get order details (requires auth)
- `PATCH /api/v1/orders/{id}` - Update order (requires auth)
- `DELETE /api/v1/orders/{id}` - Delete order (requires auth)
- `GET /api/v1/orders/{id}/products` - Get order items (requires auth)

## Required Changes

### 1. Database Schema Updates
- Add `delivery_type_id` and `payment_method_id` columns to `comenzi` table
- Add `delivery_address` column to `comenzi` table for home delivery scenarios
- Add foreign key constraints to reference existing tables
- Add appropriate indexes for performance

### 2. Model Updates
- Update `Order` SQLAlchemy model
- Update `OrderCreate` and `Order` Pydantic schemas
- Add validation for delivery and payment method selection

### 3. Service Layer Updates
- Update order creation logic to handle new fields
- Update order update logic to handle new fields
- Add validation for delivery/payment method availability

### 4. API Endpoint Updates
- Update order creation endpoint to accept new fields
- Update order response schemas to include new fields
- Update order update endpoint to allow modifying new fields

### 5. Testing Updates
- Update existing order tests
- Add new tests for delivery/payment method validation
- Test backward compatibility and migration scenarios

## Implementation Plan

### Phase 1: Database Schema Migration (1-2 days)

#### 1.1 Create Database Migration Script ✅
- [x] Create SQL migration script to add new columns
- [x] Add `delivery_type_id` column (TINYINT, nullable, foreign key to `tipuri_livrare.id`)
- [x] Add `payment_method_id` column (INT, nullable, foreign key to `modalitati_de_plata.id`)
- [x] Add `delivery_address` column (VARCHAR(150), nullable, for home delivery addresses)
- [x] Add appropriate indexes for performance
- [x] Add foreign key constraints with proper ON DELETE/ON UPDATE behavior
- [x] Test migration script on test database
- [x] Test migration script on production database
- [x] Verify schema changes are applied correctly in both environments

#### 1.2 Update Database Schema Documentation
- [ ] Update `db/schema.sql` with new table structure
- [ ] Document the new columns and constraints
- [ ] Update any database diagrams or documentation

### Phase 2: Model and Schema Updates (1-2 days)

#### 2.1 Update SQLAlchemy Models ✅
- [x] Update `app/models/order.py` to include new fields
- [x] Add relationships to `DeliveryType` and `ModalitatiPlata` models
- [x] Add `delivery_address` field with appropriate validation
- [x] Update model validation and constraints
- [x] Add appropriate indexes in `__table_args__`

#### 2.2 Update Pydantic Schemas ✅
- [x] Update `app/schemas/order.py` to include new fields
- [x] Update `OrderCreate` schema with new required fields
- [x] Update `Order` response schema with new fields
- [x] Update `OrderUpdate` schema to allow updating new fields
- [x] Add `delivery_address` field (optional, for home delivery scenarios)
- [x] Add validation for delivery/payment method selection

#### 2.3 Update Filter Parameters ✅
- [x] Add new filter options for delivery type and payment method
- [x] Update `OrderFilterParams` schema
- [x] Add new sorting options if needed

### Phase 3: Service Layer Updates (1-2 days)

#### 3.1 Update Order Creation Logic ✅
- [x] Update `create_order` function in `app/services/order.py`
- [x] Add validation for delivery method availability in the selected list
- [x] Add validation for payment method existence
- [x] Add business logic validation for delivery address (frontend responsibility)
- [x] Update foreign key validation logic
- [x] Handle cases where delivery/payment methods are not specified

#### 3.2 Update Order Update Logic ✅
- [x] Update `update_order` function to handle new fields
- [x] Add validation for delivery method changes
- [x] Add validation for payment method changes
- [x] Add validation for delivery address updates
- [x] Ensure business logic constraints are maintained

#### 3.3 Update Order Filtering and Sorting ✅
- [x] Update `_apply_order_filters` function to handle new filters
- [x] Update `_apply_sorting` function to handle new sort options
- [x] Add new filter logic for delivery and payment methods

### Phase 4: API Endpoint Updates (1 day)

#### 4.1 Update Order Creation Endpoint ✅
- [x] Update `POST /api/v1/orders/` endpoint in `app/api/endpoints/orders.py`
- [x] Ensure new fields are properly documented in OpenAPI schema
- [x] Update request/response examples
- [x] Add proper error handling for new validation rules

#### 4.2 Update Order Response Endpoints
- [ ] Update `GET /api/v1/orders/` endpoint to include new fields
- [ ] Update `GET /api/v1/orders/{id}` endpoint to include new fields
- [ ] Update response models and examples
- [ ] Document breaking changes and migration requirements for frontend clients

#### 4.3 Update Order Update Endpoint
- [ ] Update `PATCH /api/v1/orders/{id}` endpoint to handle new fields
- [ ] Add validation for new field updates
- [ ] Update request/response documentation

### Phase 5: Testing and Validation (2-3 days)

#### 5.1 Update Existing Tests
- [ ] Update `tests/integration/test_orders_api.py` to include new fields
- [ ] Modify existing test data to include delivery/payment methods
- [ ] Update test assertions to verify new fields
- [ ] Ensure all existing tests pass with new schema

#### 5.2 Add New Test Cases
- [ ] Test order creation with delivery and payment methods
- [ ] Test order creation without delivery/payment methods (if allowed)
- [ ] Test order creation with and without delivery address
- [ ] Test validation of delivery method availability in list
- [ ] Test validation of payment method existence
- [ ] Test order updates with new fields
- [ ] Test filtering and sorting by new fields

#### 5.3 Test Migration Scenarios
- [ ] Test database migration script
- [ ] Test backward compatibility for existing orders
- [ ] Test API behavior with and without new fields
- [ ] Test error handling for invalid delivery/payment methods

### Phase 6: Documentation and Deployment (1 day)

#### 6.1 Update API Documentation
- [ ] Update OpenAPI/Swagger documentation
- [ ] Update `docs/FRONTEND_ORDERS_API_GUIDE.md`
- [ ] Add examples of new request/response formats
- [ ] Document breaking changes and migration notes

#### 6.2 Update Frontend Guide
- [ ] Update frontend integration examples
- [ ] Add examples for new field handling
- [ ] Document new validation rules
- [ ] Document business logic for delivery address (frontend responsibility)
- [ ] Provide breaking change migration guide for frontend applications
- [ ] Document required frontend updates for new mandatory fields

#### 6.3 Deployment Preparation
- [ ] Create rollback plan for database migration
- [ ] Document deployment steps
- [ ] Prepare communication about breaking changes
- [ ] Plan testing in staging environment

## Breaking Changes and Migration Notes

### ⚠️ **BREAKING CHANGES - Frontend Updates Required**

This API expansion introduces **breaking changes** that require frontend updates:

1. **New Required Fields**: 
   - `delivery_type_id` is now **mandatory** for order creation
   - `payment_method_id` is now **mandatory** for order creation
   - Existing frontend code will receive 422 validation errors if these fields are missing

2. **Schema Changes**:
   - Order responses now include new fields that may not be handled by existing frontend code
   - New validation rules may cause previously working requests to fail

3. **Frontend Migration Requirements**:
   - Update order creation forms to include delivery and payment method selection
   - Update order display components to show new fields
   - Handle new validation error messages
   - Update any hardcoded order structures

### Migration Strategy
- **No backward compatibility**: This is a breaking change by design
- **Frontend must be updated** before deploying backend changes
- **Staging environment testing** required before production deployment
- **Coordinated deployment** of frontend and backend changes

## Technical Details

### New Database Schema
```sql
ALTER TABLE `comenzi` 
ADD COLUMN `delivery_type_id` TINYINT NULL,
ADD COLUMN `payment_method_id` INT NULL,
ADD COLUMN `delivery_address` VARCHAR(150) NULL,
ADD INDEX `idx_comenzi_delivery_type` (`delivery_type_id`),
ADD INDEX `idx_comenzi_payment_method` (`payment_method_id`),
ADD INDEX `idx_comenzi_delivery_address` (`delivery_address`),
ADD CONSTRAINT `fk_comenzi_delivery_type` 
    FOREIGN KEY (`delivery_type_id`) REFERENCES `tipuri_livrare` (`id`),
ADD CONSTRAINT `fk_comenzi_payment_method` 
    FOREIGN KEY (`payment_method_id`) REFERENCES `modalitati_de_plata` (`id`);
```

### Updated Order Schema
```python
class OrderCreate(BaseModel):
    nume_client: str
    data_plasarii: datetime
    liste_id: int
    delivery_type_id: int  # New required field
    payment_method_id: int  # New required field
    delivery_address: Optional[str] = None  # New optional field for home delivery
    order_notes: Optional[str] = None
    items: Optional[List[OrderItemBase]] = None

class Order(BaseModel):
    id: int
    nume_client: str
    data_plasarii: datetime
    liste_id: int
    delivery_type_id: int  # New field
    payment_method_id: int  # New field
    delivery_address: Optional[str] = None  # New field for home delivery
    order_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItem]
    
    # New relationships
    delivery_type: DeliveryType
    payment_method: ModalitatePlata
```

### Validation Rules
1. **Delivery Method**: Must be available in the selected list (check `liste_au_tipuri_livrare`)
2. **Payment Method**: Must exist in `modalitati_de_plata` table
3. **Delivery Address**: Optional field, but frontend should enforce business rules
4. **Both delivery_type_id and payment_method_id are required** for new orders (breaking change)
5. **Existing orders** will have NULL values for these fields

## Breaking Changes

### API Changes
- **Order Creation**: Now requires `delivery_type_id` and `payment_method_id`, optional `delivery_address`
- **Order Response**: Includes new fields and related objects
- **Order Updates**: Can now modify delivery and payment methods, and delivery address

### Database Changes
- New columns added to existing table (`delivery_type_id`, `payment_method_id`, `delivery_address`)
- Foreign key constraints added for delivery and payment methods
- Existing orders will have NULL values for new fields

### Frontend Impact
- Order creation forms must include delivery and payment method selection
- Order creation forms should include delivery address field for home delivery scenarios
- Frontend must enforce business rules (e.g., address required for home delivery)
- Order display must handle new fields
- API calls must include new required fields

## Migration Strategy

### Database Migration
1. **Backup**: Create full database backup before migration
2. **Downtime**: Plan for minimal downtime during migration
3. **Rollback**: Prepare rollback script to remove new columns
4. **Testing**: Test migration on staging environment first

### Application Deployment
1. **Database First**: Apply database migration before deploying new code
2. **Code Deployment**: Deploy updated application code
3. **Verification**: Test all endpoints work correctly
4. **Monitoring**: Monitor for any issues after deployment

### Frontend Updates
1. **Coordinate**: Deploy frontend updates after backend deployment
2. **Graceful Degradation**: Handle cases where new fields might be missing
3. **User Communication**: Inform users about new required fields

## Risk Assessment

### High Risk
- **Database Migration**: Adding columns to production table
- **Breaking Changes**: API changes that affect existing clients
- **Data Integrity**: Foreign key constraints on existing data

### Medium Risk
- **Performance**: New indexes and foreign keys
- **Testing Coverage**: Ensuring all scenarios are tested
- **Rollback Complexity**: Reverting changes if issues arise

### Low Risk
- **Code Changes**: Standard model/schema updates
- **API Updates**: Following existing patterns
- **Documentation**: Updating guides and examples

## Success Criteria

- [ ] All existing orders API endpoints work with new schema
- [ ] New orders can be created with delivery and payment methods
- [ ] Existing orders display correctly (with NULL values for new fields)
- [ ] All tests pass with new implementation
- [ ] API documentation is updated and accurate
- [ ] Frontend integration guide is updated
- [ ] Database migration can be performed safely
- [ ] Rollback plan is tested and documented

## Timeline Estimate

- **Total Duration**: 7-10 days
- **Phase 1**: 1-2 days (Database)
- **Phase 2**: 1-2 days (Models/Schemas)
- **Phase 3**: 1-2 days (Services)
- **Phase 4**: 1 day (API)
- **Phase 5**: 2-3 days (Testing)
- **Phase 6**: 1 day (Documentation/Deployment)

## Dependencies

- Access to production database for migration
- Staging environment for testing
- Frontend team coordination for updates
- Frontend team understanding of business logic for delivery address validation
- Database backup and rollback procedures
- Monitoring and alerting for production deployment
