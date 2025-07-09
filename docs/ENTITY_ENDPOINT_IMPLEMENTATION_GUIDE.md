# Entity Endpoint Implementation Guide

This document provides a step-by-step guide for adding new entity endpoints to the Online Shop Business Backend API, incorporating best practices for validation, error handling, and testing.

## Entity Implementation Progress

The following entities need to be implemented in order of dependency. Check them off as they are completed:

### Implementation Order

### Core Entities

#### Level 0: Independent Entities
- [x] **Units (Unitati)** - Units of measurement for products
- [x] **Payment Methods (Modalitati de Plata)** - Methods of payment
- [x] **Delivery Types (Tipuri Livrare)** - Types of delivery options
- [x] **Delivery Schedules (Orare Livrari)** - Delivery time schedules
- [x] **Business Details (Business Details)** - Shop business information
- [ ] **Categories (Categorii)** - Product categories
- [ ] **Admins (Admins)** - Admin user management

#### Level 1: First-Level Dependencies
- [ ] **Products (Produse)** - (depends on `Units` and `Categories`)
- [ ] **Lists (Liste)** - (depends on `Delivery Schedules`)

#### Level 2: Second-Level Dependencies
- [ ] **Secondary Images** - (depends on `Products`)
- [ ] **Temporary Products (Produse Temporare)** - (depends on `Products`)
- [ ] **Orders (Comenzi)** - (depends on `Lists`)

### Junction (Many-to-Many) Tables

These tables connect core entities and should be implemented after their dependencies are in place.

- [ ] **Business Details <> Payment Methods** - (depends on `Business Details`, `Payment Methods`)
- [ ] **Lists <> Delivery Types** - (depends on `Lists`, `Delivery Types`)
- [ ] **Lists <> Products** - (depends on `Lists`, `Products`)
- [ ] **Orders <> Products (Comenzi au Produse)** - (depends on `Orders`, `Products`, `Units`)

## Implementation Steps

Follow these steps in order when implementing a new entity endpoint. **Important**: Use a baby steps approach - implement one step, get feedback, then proceed to the next step only after verification.

### 1. Create the Database Model

- Define the SQLAlchemy model in `app/models/` directory
- Include appropriate field types, constraints, and relationships
- Add proper indexes for frequently queried fields
- Example:

```python
from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.core.database import Base

class YourEntity(Base):
    __tablename__ = "your_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(200), nullable=True)
    
    # Add UniqueConstraint if needed
    __table_args__ = (UniqueConstraint('name', name='uq_your_entity_name'),)
```

### 2. Create Pydantic Schemas

Create a new file in `app/schemas/` with three schema classes:

1. **Base schema** - Common fields and validators
2. **Create schema** - For creation requests (extends base)
3. **Update schema** - For update requests (extends base, all fields optional)
4. **Response schema** - For API responses (extends base, adds ID)

Example:

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional

class YourEntityBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Entity name",
        examples=["Example Name"]
    )
    description: Optional[str] = Field(
        None,
        max_length=200,
        description="Entity description"
    )
    
    @field_validator('name')
    def name_must_not_be_empty_or_whitespace(cls, v):
        if v.strip() == "":
            raise ValueError("Name must not be empty or whitespace only")
        return v.strip()

class YourEntityCreate(YourEntityBase):
    pass

class YourEntityUpdate(YourEntityBase):
    name: Optional[str] = Field(
        None, min_length=1, max_length=50,
        description="Entity name"
    )
    description: Optional[str] = None

class YourEntity(YourEntityBase):
    id: int = Field(gt=0)
    
    model_config = ConfigDict(from_attributes=True)
```

### 3. Implement Service Layer Functions

Create a new file in `app/services/` with CRUD operations that handle:

- Validation
- Database interactions
- Error handling
- Exception conversion

Example:

```python
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.your_entity import YourEntity
from app.schemas.your_entity import YourEntityCreate, YourEntityUpdate

# GET all entities with pagination
def get_entities(db: Session, skip: int = 0, limit: int = 100):
    try:
        return db.query(YourEntity).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )

# GET entity by ID
def get_entity_by_id(db: Session, entity_id: int):
    if entity_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {entity_id} - must be positive"
        )
    
    try:
        entity = db.query(YourEntity).filter(YourEntity.id == entity_id).first()
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity with ID {entity_id} not found"
            )
        return entity
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )

# CREATE new entity
def create_entity(db: Session, entity: YourEntityCreate):
    # Validate inputs
    if not entity.name or entity.name.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Entity name cannot be empty"
        )
    
    # Check for duplicates
    existing = db.query(YourEntity).filter(YourEntity.name == entity.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An entity with the name '{entity.name}' already exists"
        )
    
    try:
        db_entity = YourEntity(**entity.model_dump())
        db.add(db_entity)
        db.commit()
        db.refresh(db_entity)
        return db_entity
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An entity with the name '{entity.name}' already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )

# UPDATE existing entity
def update_entity(db: Session, entity_id: int, entity: YourEntityUpdate):
    # Validate ID
    if entity_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {entity_id} - must be positive"
        )
    
    # Check if there are any fields to update
    update_data = entity.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    try:
        # Check if entity exists
        db_entity = db.query(YourEntity).filter(YourEntity.id == entity_id).first()
        if db_entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity with ID {entity_id} not found"
            )
        
        # Check for duplicate name if updating name
        if "name" in update_data and update_data["name"]:
            name = update_data["name"]
            existing = db.query(YourEntity).filter(
                YourEntity.name == name,
                YourEntity.id != entity_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An entity with the name '{name}' already exists"
                )
        
        # Apply updates
        for key, value in update_data.items():
            setattr(db_entity, key, value)
        
        db.commit()
        db.refresh(db_entity)
        return db_entity
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate entity name"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )

# DELETE entity
def delete_entity(db: Session, entity_id: int):
    # Validate ID
    if entity_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {entity_id} - must be positive"
        )
    
    try:
        # Check if entity exists
        db_entity = db.query(YourEntity).filter(YourEntity.id == entity_id).first()
        if db_entity is None:
            return False
        
        db.delete(db_entity)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
```

### 4. Create API Endpoint Routes

Create a new file in `app/api/endpoints/` with router definitions for CRUD operations:

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.your_entity import YourEntity, YourEntityCreate, YourEntityUpdate
from app.services.your_entity import (
    create_entity,
    delete_entity,
    get_entity_by_id,
    get_entities,
    update_entity,
)

router = APIRouter()

@router.get("/", response_model=List[YourEntity], responses={
    200: {"description": "Successful response"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_entities(
    skip: int = Query(0, ge=0, le=100, description="Number of items to skip (max 100)"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return (max 100)"),
    db: Session = Depends(get_db)
):
    """Get all entities with pagination support"""
    try:
        entities = get_entities(db, skip=skip, limit=limit)
        return entities
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/", response_model=YourEntity, status_code=status.HTTP_201_CREATED, responses={
    201: {"description": "Entity created successfully"},
    400: {"description": "Bad request, e.g. duplicate entity"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def create_entity_endpoint(entity: YourEntityCreate, db: Session = Depends(get_db)):
    """Create a new entity"""
    try:
        return create_entity(db=db, entity=entity)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{entity_id}", response_model=YourEntity, responses={
    200: {"description": "Successful response"},
    404: {"description": "Entity not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def read_entity(entity_id: int = Path(..., gt=0, description="The ID of the entity"), db: Session = Depends(get_db)):
    """Get a specific entity by ID"""
    try:
        return get_entity_by_id(db=db, entity_id=entity_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.put("/{entity_id}", response_model=YourEntity, responses={
    200: {"description": "Entity updated successfully"},
    400: {"description": "Bad request, e.g. duplicate entity or no valid fields"},
    404: {"description": "Entity not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def update_entity_endpoint(
    entity_id: int = Path(..., gt=0, description="The ID of the entity to update"),
    entity: YourEntityUpdate = ...,
    db: Session = Depends(get_db)
):
    """Update an entity"""
    try:
        return update_entity(db=db, entity_id=entity_id, entity=entity)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    204: {"description": "Entity deleted successfully"},
    404: {"description": "Entity not found"},
    422: {"description": "Validation error"},
    500: {"description": "Internal server error"}
})
def delete_entity_endpoint(entity_id: int = Path(..., gt=0, description="The ID of the entity to delete"), db: Session = Depends(get_db)):
    """Delete an entity"""
    try:
        result = delete_entity(db=db, entity_id=entity_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity with ID {entity_id} not found"
            )
        return None
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
```

### 5. Register the Router in API V1

Add the new router to `app/api/api.py`:

```python
from app.api.endpoints import your_entity

# Add this line to the existing api_router.include_router statements
api_router.include_router(your_entity.router, prefix="/your-entities", tags=["your-entities"])
```
## Best Practices

### Validation

1. **Validate Path Parameters**
   - Use `Path(...)` with constraints like `gt=0` for IDs

2. **Validate Query Parameters**
   - Use `Query(...)` with constraints like `ge=0`, `le=100`
   - Set reasonable limits for pagination

3. **Validate Request Bodies**
   - Use Pydantic validators for field-level validation
   - Add custom validators for business rules

### Error Handling

1. **Use Proper Status Codes**
   - 400: Bad Request (client error, invalid input)
   - 404: Not Found (resource does not exist)
   - 422: Unprocessable Entity (validation error)
   - 500: Internal Server Error (server-side error)

2. **Wrap Database Operations**
   - Use try-except blocks around all database operations
   - Catch specific exceptions and convert to appropriate HTTPExceptions
   - Always rollback transactions on error

3. **Provide Clear Error Messages**
   - Include specific details about what went wrong
   - Avoid exposing sensitive information

### Documentation

1. **Document Endpoints**
   - Add docstrings to all router functions
   - Use the `responses` parameter to document status codes

2. **Document Schemas**
   - Use Field's description parameter
   - Provide examples where helpful

## Manual Testing & Verification

### 6. Manual API Testing

Before writing automated tests, manually test all endpoints to verify functionality:

1. **Start the API server** (if not already running):
   ```bash
   docker-compose up -d
   ```

2. **Test each endpoint** using tools like cURL, Postman, or the Swagger UI at `http://localhost:8000/docs`:
   - Create a new entity (POST)
   - Get a list of entities (GET)
   - Get a specific entity by ID (GET)
   - Update an entity (PUT)
   - Delete an entity (DELETE)

3. **Verify error handling** by intentionally triggering validation errors, 404s, etc.

4. **Document any issues** and fix them before proceeding to automated testing.

## Automated Testing

### 7. Integration Tests

Create integration tests using the `EntityTestUtils` class to leverage common test functionality:

1. **Check if entity needs custom test utilities**:
   - If the entity follows the standard pattern with `denumire` field, use `EntityTestUtils` directly
   - If the entity has different fields or requirements, create a custom test utility class

2. **Create a test file** in `tests/integration/` directory following this template:

   ```python
   # Standard usage with EntityTestUtils (for entities with 'denumire' field)
   from integration.test_utils import EntityTestUtils
   
   # Create a test utils instance for your entity
   entity_utils = EntityTestUtils(entity_name="Your Entity", endpoint_path="your-entities")
   
   def test_entity_crud_workflow():
       """Tests the full CRUD workflow for the entity"""
       entity_utils.test_crud_workflow()
   
   def test_entity_list_and_pagination():
       """Tests listing entities with pagination"""
       entity_utils.test_list_and_pagination()
   
   def test_entity_validation():
       """Tests validation for entity endpoints"""
       entity_utils.test_validation()
   ```

   For custom fields, create a custom test utility class:

   ```python
   class CustomEntityTestUtils(EntityTestUtils):
       """Test utilities for custom entity"""
       
       def __init__(self):
           super().__init__(entity_name="Custom Entity", endpoint_path="custom-entities")
       
       def create_entity(self, name=None):
           """Override to use custom fields"""
           if name is None:
               name = self.generate_unique_name()
               
           create_response = requests.post(
               f"{self.base_url}/",
               json={"custom_field": name}
           )
           # Rest of implementation...
       
       def update_entity(self, entity_id, name):
           """Override to use custom fields"""
           # Implementation...
       
       def test_crud_workflow(self):
           """Override to check custom fields"""
           # Implementation...
   ```

3. **Run integration tests**:
   ```bash
   ./run_api_integration_tests.sh
   ```

### 8. Contract Testing

Contract tests ensure API endpoints match their OpenAPI specification:

1. **Run contract tests** after implementing the entity:
   ```bash
   ./run_api_contract_tests.sh
   ```

2. **Address any failures** by:
   - Fixing schema definitions if they don't match implementation
   - Updating API implementation if it doesn't match contract
   - Adding proper validation rules

3. **Note:** No need to create custom contract tests for each entity as Schemathesis automatically tests against the OpenAPI schema

### 9. Update Implementation Guide

After successful implementation and testing:

1. **Mark the entity as completed** in the `docs/ENTITY_ENDPOINT_IMPLEMENTATION_GUIDE.md` file by changing:
   ```markdown
   - [ ] **Entity Name** - Entity description
   ```
   to:
   ```markdown
   - [x] **Entity Name** - Entity description
   ```

### 10. Update Version Number

1. **Increment the minor version** in `app/core/config.py` to reflect the addition of a new entity:
   ```python
   # Example: Change API_VERSION from "0.3.0" to "0.4.0"
   API_VERSION = "0.4.0"
   ```

2. **Commit and push** all changes to the repository:
   ```bash
   git add .
   git commit -m "Implement Entity Name with full CRUD operations and tests"
   git push
   ```

## Implementation Checklist

Use this checklist for each entity implementation and check off items as they are completed:

1. **Database Model**
   - [ ] SQLAlchemy model created in `app/models/` directory
   - [ ] Proper field types, constraints, and relationships defined
   - [ ] Table name matches database schema

2. **Pydantic Schemas**
   - [ ] Base schema with common fields and validators
   - [ ] Create schema for POST requests
   - [ ] Update schema with optional fields for PUT requests
   - [ ] Response schema with ID field and ORM mode enabled

3. **Service Layer**
   - [ ] CRUD operations implemented (get_all, get_by_id, create, update, delete)
   - [ ] Proper validation and error handling
   - [ ] Transaction management with rollback on errors

4. **API Endpoints**
   - [ ] Router with all CRUD endpoints (GET, POST, GET by ID, PUT, DELETE)
   - [ ] Appropriate response models, status codes, and error handling
   - [ ] Parameter validation (path, query, body)
   - [ ] OpenAPI documentation

5. **Router Registration**
   - [ ] Router added to main API router in `app/api/api.py`
   - [ ] Proper prefix and tags applied

6. **Manual Testing**
   - [ ] All endpoints tested manually via Swagger UI or Postman
   - [ ] Error scenarios verified

7. **Automated Tests**
   - [ ] Integration tests created using EntityTestUtils (standard or custom)
   - [ ] Contract tests pass for new endpoints
   - [ ] All tests running successfully in Docker environment

8. **Documentation**
   - [ ] Entity marked as completed in the implementation guide
   - [ ] Any special considerations or notes added to comments

9. **Update Version**
   - [ ] Minor version incremented in `app/core/config.py`
   - [ ] Changes committed and pushed to repository

**Final Check:** Verify that the implementation correctly handles all edge cases, follows project patterns, and maintains consistency with existing code.
