# Service Layer Refactoring Options

This document outlines various approaches to refactoring the services layer to reduce code duplication and improve maintainability.

## Current Pattern Analysis

The services layer currently shows significant code duplication across different entity services with:

1. **Common CRUD Operations**: All services implement the same five core functions
2. **Identical Error Handling**: Same SQLAlchemyError handling patterns with db.rollback()
3. **Similar ID Validation**: Same validation for positive IDs
4. **Similar 404 Handling**: Same pattern for checking existence and raising 404s
5. **Consistent Transaction Management**: Similar db.commit() and db.refresh() patterns

## Approach 0: Object-Oriented Approach with Inheritance

### BaseEntityService Class

```python
class BaseEntityService:
    def __init__(self, model_class, entity_name):
        self.model_class = model_class
        self.entity_name = entity_name
        
    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        try:
            return db.query(self.model_class).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occurred: {str(e)}"
            )
            
    def get_by_id(self, db: Session, entity_id: int):
        self._validate_id(entity_id)
        try:
            entity = db.query(self.model_class).filter(self.model_class.id == entity_id).first()
            if entity is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.entity_name} with ID {entity_id} not found"
                )
            return entity
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occurred: {str(e)}"
            )
    
    def delete(self, db: Session, entity_id: int):
        self._validate_id(entity_id)
        try:
            entity = db.query(self.model_class).filter(self.model_class.id == entity_id).first()
            if entity is None:
                return False
            db.delete(entity)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occurred: {str(e)}"
            )
    
    def _validate_id(self, entity_id: int):
        if entity_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid ID: {entity_id} - must be positive"
            )
```

### Entity-Specific Subclass Example

```python
class BusinessDetailsService(BaseEntityService):
    def __init__(self):
        super().__init__(BusinessDetails, "Business details")
    
    def create(self, db: Session, business_details: BusinessDetailsCreate):
        try:
            db_business_details = BusinessDetails(
                adresa=business_details.adresa,
                telefon=business_details.telefon,
                # other fields...
            )
            return self._save_entity(db, db_business_details)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occurred: {str(e)}"
            )
    
    def update(self, db: Session, entity_id: int, business_details: BusinessDetailsUpdate):
        # Implementation would use common patterns and call parent methods
        pass
        
    def _save_entity(self, db: Session, entity):
        # Common saving logic with error handling
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity
```

### Usage Example

```python
# app/api/endpoints/business_details.py
business_details_service = BusinessDetailsService()

@router.get("/", response_model=List[schemas.BusinessDetails])
def read_business_details(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return business_details_service.get_all(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.BusinessDetails)
def create_business_details(
    business_details: schemas.BusinessDetailsCreate, db: Session = Depends(get_db)
):
    return business_details_service.create(db, business_details)
```

### Pros and Cons

**Pros:**
- Complete abstraction of common patterns
- Strong enforcement of consistent behavior
- Good for complex inheritance hierarchies
- Follows OOP principles

**Cons:**
- Major architectural shift from current approach
- Introduces complexity for simple CRUD operations
- Requires careful design of inheritance hierarchies
- Less explicit than functional approach

## Approach 1: Utility Functions with Functional Composition

### Utility Functions

```python
# app/services/utils.py
def validate_id(entity_id, entity_name):
    if entity_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {entity_id} - must be positive"
        )

def handle_db_error(func):
    """Decorator for handling database errors"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            db = next((arg for arg in args if isinstance(arg, Session)), kwargs.get('db'))
            if db:
                db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occurred: {str(e)}"
            )
    return wrapper

def get_entity_or_404(db, model_class, entity_id, entity_name):
    entity = db.query(model_class).filter(model_class.id == entity_id).first()
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with ID {entity_id} not found"
        )
    return entity
```

### Usage Example

```python
# app/services/business_details.py
from app.services.utils import validate_id, handle_db_error, get_entity_or_404

@handle_db_error
def get_business_details(db: Session, skip: int = 0, limit: int = 100):
    return db.query(BusinessDetails).offset(skip).limit(limit).all()

@handle_db_error
def get_business_details_by_id(db: Session, business_details_id: int):
    validate_id(business_details_id, "Business details")
    return get_entity_or_404(db, BusinessDetails, business_details_id, "Business details")
```

### Pros and Cons

**Pros:**
- Maintains functional programming style
- Can be adopted incrementally
- Functions are composable
- Decorator approach for error handling is clean

**Cons:**
- Requires careful function composition
- Decorator pattern might be less familiar
- May still require some boilerplate code

## Approach 2: Generic Service Functions with Type Parameters

### Generic Service Functions

```python
# app/services/generic.py
def get_all_entities(db: Session, model_class, skip: int = 0, limit: int = 100):
    try:
        return db.query(model_class).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )

def get_entity_by_id(db: Session, model_class, entity_id: int, entity_name: str):
    if entity_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {entity_id} - must be positive"
        )
    
    try:
        entity = db.query(model_class).filter(model_class.id == entity_id).first()
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} with ID {entity_id} not found"
            )
        return entity
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
```

### Usage Example

```python
# app/services/business_details.py
from app.services.generic import get_all_entities, get_entity_by_id

def get_business_details(db: Session, skip: int = 0, limit: int = 100):
    return get_all_entities(db, BusinessDetails, skip, limit)

def get_business_details_by_id(db: Session, business_details_id: int):
    return get_entity_by_id(db, BusinessDetails, business_details_id, "Business details")
```

### Pros and Cons

**Pros:**
- Simple and straightforward approach
- Maintains current function-based paradigm
- Easy to understand and use
- Direct mapping from entity services to generic functions

**Cons:**
- Limited abstraction for complex operations
- Still requires repetitive function definitions
- Type safety relies on runtime checks rather than compile-time

## Approach 3: Service Factory with Higher-Order Functions

### Factory Module

```python
# app/services/factory.py
def create_service(model_class, entity_name):
    """Creates a set of CRUD service functions for a given entity type"""
    
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        try:
            return db.query(model_class).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                               detail=f"Database error occurred: {str(e)}")
    
    def get_by_id(db: Session, entity_id: int):
        if entity_id <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                              detail=f"Invalid ID: {entity_id} - must be positive")
        try:
            entity = db.query(model_class).filter(model_class.id == entity_id).first()
            if entity is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                  detail=f"{entity_name} with ID {entity_id} not found")
            return entity
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              detail=f"Database error occurred: {str(e)}")
    
    # Other CRUD functions...
    
    return {
        "get_all": get_all,
        "get_by_id": get_by_id,
        # Other functions...
    }
```

### Usage Example

```python
# app/services/business_details.py
from app.services.factory import create_service

# Create the basic CRUD services
business_details_service = create_service(
    model_class=BusinessDetails,
    entity_name="Business details"
)

# Extract individual functions
get_business_details = business_details_service["get_all"]
get_business_details_by_id = business_details_service["get_by_id"]
```

### Pros and Cons

**Pros:**
- Dynamic function generation
- Consistent function signatures
- Reduces service implementation to configuration
- Easy to extend with custom behavior

**Cons:**
- More complex concept (higher-order functions)
- Dictionary-based access to functions is less IDE-friendly
- Harder to customize individual function behavior

## Approach 4: Minimal Dependency Injection

### Service Class

```python
# app/services/base.py
class CrudService:
    """Base CRUD operations that can be injected into service functions"""
    
    @staticmethod
    def validate_id(entity_id):
        if entity_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid ID: {entity_id} - must be positive"
            )
    
    @staticmethod
    def get_all(db, model_class, skip=0, limit=100):
        try:
            return db.query(model_class).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occurred: {str(e)}"
            )
```

### Usage Example

```python
# app/services/business_details.py
from app.services.base import CrudService

# Create service instance to be used by all functions
crud = CrudService()

def get_business_details(db: Session, skip: int = 0, limit: int = 100):
    return crud.get_all(db, BusinessDetails, skip, limit)

def get_business_details_by_id(db: Session, business_details_id: int):
    crud.validate_id(business_details_id)
    # Rest of implementation...
```

### Pros and Cons

**Pros:**
- Simpler than full OOP approach
- Maintains familiar function-based API
- Static methods avoid need for instantiation
- Good balance of abstraction and explicitness

**Cons:**
- Not as DRY as other approaches
- Introduces a class just for utility methods
- May be overkill for simple operations

## Approach 5: Hybrid Approach with Specialized Utility Module (Recommended)

### CRUD Utility Module

```python
# app/services/crud_utils.py
def get_entities(db: Session, model_class, skip: int = 0, limit: int = 100):
    """Generic function to get all entities with pagination"""
    try:
        return db.query(model_class).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )

def get_entity_by_id(db: Session, model_class, entity_id: int, entity_name: str):
    """Generic function to get entity by ID with validation"""
    if entity_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {entity_id} - must be positive"
        )
    
    try:
        entity = db.query(model_class).filter(model_class.id == entity_id).first()
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} with ID {entity_id} not found"
            )
        return entity
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )

def save_entity(db: Session, entity):
    """Common save operation with error handling"""
    try:
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )

def delete_entity(db: Session, model_class, entity_id: int, entity_name: str):
    """Generic function to delete entity by ID with validation"""
    if entity_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID: {entity_id} - must be positive"
        )
    
    try:
        entity = db.query(model_class).filter(model_class.id == entity_id).first()
        if entity is None:
            return False
        
        db.delete(entity)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
```

### Usage Example

```python
# app/services/business_details.py
from app.services.crud_utils import get_entities, get_entity_by_id, save_entity, delete_entity

def get_business_details(db: Session, skip: int = 0, limit: int = 100):
    return get_entities(db, BusinessDetails, skip, limit)

def get_business_details_by_id(db: Session, business_details_id: int):
    return get_entity_by_id(db, BusinessDetails, business_details_id, "Business details")

def create_business_details(db: Session, business_details: BusinessDetailsCreate):
    db_business_details = BusinessDetails(
        adresa=business_details.adresa,
        telefon=business_details.telefon,
        # Other fields...
    )
    return save_entity(db, db_business_details)

def delete_business_details(db: Session, business_details_id: int):
    return delete_entity(db, BusinessDetails, business_details_id, "Business details")
```

### Pros and Cons

**Pros:**
- Pragmatic approach focusing on most repetitive code
- Familiar function-based approach matching current architecture
- Can be adopted incrementally
- Maintains explicitness and readability
- Minimal learning curve

**Cons:**
- Not as complete as other approaches
- Doesn't fully eliminate all duplication
- Entity-specific variations still require custom code

## Implementation Recommendation

The **Hybrid Approach with Specialized Utility Module** (Approach 5) offers the best balance of benefits for your current project:

1. **Immediate Value**: Targets the most repetitive aspects of CRUD operations
2. **Low Risk**: Can be implemented incrementally with minimal disruption
3. **Compatibility**: Aligns with current function-based architecture
4. **Maintainability**: Centralizes common error handling and validation logic
5. **Flexibility**: Easy to extend for entity-specific requirements

### Implementation Steps:

1. Create the `app/services/crud_utils.py` module
2. Implement the core utility functions
3. Refactor one service as a proof of concept
4. Gradually refactor other services as needed
5. Update documentation to encourage use of the utilities

This approach respects the existing architecture while still providing significant improvements in code quality and maintainability.
