# REST API Implementation Plan for Online Shop Business

## Overview

This document outlines the implementation plan for building a comprehensive REST API for the Online Shop Business application. The API will provide endpoints for managing all entities defined in the database schema, following RESTful principles and leveraging the existing FastAPI setup.

## Current Project State

- **Framework**: FastAPI with Pydantic
- **Database**: MySQL (configured via docker-compose)
- **Project Structure**: Basic structure established with app/models, app/schemas, app/services, app/utils directories
- **Current Implementation**: Basic FastAPI application with health check endpoint

## Implementation Principles

1. **Dependency-Based Approach**: Implement entities in order of dependencies, starting with independent tables
2. **Incremental Development**: One entity at a time with full CRUD operations
3. **Integrated Testing**: Implementation and testing in the same iteration cycle
4. **Leverage FastAPI Features**: Utilize automatic Swagger documentation, dependency injection, etc.

## API Endpoints Structure

```
/api/v1
├── auth
│   ├── login             # POST: authenticate admin
│   └── refresh           # POST: refresh JWT token
│
├── categories            # GET, POST: list/create categories
│   ├── {id}             # GET, PUT, DELETE: specific category
│   └── {id}/products    # GET: products in category
│
├── units                 # GET, POST: list/create units
│   └── {id}             # GET, PUT, DELETE: specific unit
│
├── delivery-types        # GET, POST: list/create delivery types
│   └── {id}             # GET, PUT, DELETE: specific delivery type
│
├── payment-methods       # GET, POST: list/create payment methods
│   └── {id}             # GET, PUT, DELETE: specific payment method
│
├── products              # GET, POST: list/create products
│   ├── {id}             # GET, PUT, DELETE: specific product
│   ├── {id}/images      # GET, POST: product images
│   └── search           # GET: search products
│
├── lists                 # GET, POST: list/create lists
│   ├── {id}             # GET, PUT, DELETE: specific list
│   ├── {id}/products    # GET, POST, DELETE: manage list products
│   ├── {id}/delivery    # GET, POST, DELETE: manage list delivery types
│   └── current          # GET: get current list
│
├── orders                # GET, POST: list/create orders
│   ├── {id}             # GET, PUT: specific order
│   ├── {id}/products    # GET: products in order
│   └── by-status/{status} # GET: filter orders by status
│
└── business              # GET, PUT: business details
    └── settings         # GET, PUT: business settings
```

## Implementation Phases

### Phase 1: Core Infrastructure (1-2 days)

1. **Database Connection**
   - Implement SQLAlchemy integration with MySQL
   - Create database session management
   - Set up connection utilities

2. **Base Components**
   - Create base SQLAlchemy models
   - Set up base Pydantic schemas
   - Implement pagination and filtering utilities

3. **Authentication**
   - Implement JWT-based authentication with the `admins` table
   - Set up authentication middleware

### Phase 2: Independent Entities (2-3 days)

Implement these entities that have minimal or no dependencies:

1. **Units (unitati)**
   - Database models and schemas
   - CRUD endpoints
   - Unit tests

2. **Categories (category)**
   - Database models and schemas
   - CRUD endpoints
   - Unit tests

3. **Delivery Types (tipuri_livrare)**
   - Database models and schemas
   - CRUD endpoints
   - Unit tests

4. **Payment Methods (modalitati_de_plata)**
   - Database models and schemas
   - CRUD endpoints
   - Unit tests

5. **Business Details (business_details)**
   - Database models and schemas
   - CRUD endpoints
   - Unit tests

### Phase 3: Intermediate Entities (2-3 days)

Implement entities with moderate dependencies:

1. **Products (produse)**
   - Database models and schemas including relationships
   - CRUD endpoints with category and unit relationships
   - Product search and filtering
   - Unit tests

2. **Secondary Images (secondary_images)**
   - Database models and schemas
   - CRUD endpoints
   - Image handling utilities
   - Unit tests

3. **Business Details - Payment Methods relationship**
   - Association endpoints
   - Unit tests

### Phase 4: Complex Entities (2-3 days)

Implement entities with multiple dependencies:

1. **Lists (liste)**
   - Database models and schemas
   - CRUD endpoints
   - Current list functionality
   - Unit tests

2. **List - Product Relationships (liste_au_produse)**
   - Association endpoints
   - Unit tests

3. **List - Delivery Type Relationships (liste_au_tipuri_livrare)**
   - Association endpoints
   - Unit tests

### Phase 5: Most Complex Entities (2-3 days)

Implement the most complex entities with multiple relationships:

1. **Orders (comenzi)**
   - Database models and schemas
   - CRUD endpoints
   - Order status management
   - Unit tests

2. **Order - Product Relationships (comenzi_au_produse)**
   - Association endpoints
   - Pricing and quantity management
   - Unit tests

### Phase 6: Integration and System Testing (1-2 days)

1. **End-to-End Testing**
   - Complete API flows testing
   - Load testing (optional)

2. **Documentation Finalization**
   - Review and enhance FastAPI auto-generated documentation
   - Create additional examples if needed

3. **Deployment Review**
   - Final checks for production readiness
   - Performance optimization if needed

## Technical Requirements

- FastAPI for API framework
- SQLAlchemy for ORM
- Pydantic for request/response validation
- PyJWT for authentication
- Pytest for testing

## Milestones and Timeline

- **Week 1**: Phases 1-2 (Core Infrastructure and Independent Entities)
- **Week 2**: Phases 3-4 (Intermediate and Complex Entities)
- **Week 3**: Phases 5-6 (Most Complex Entities, Integration and Testing)

## Future Enhancements (Post-MVP)

1. **Advanced Search**: Implement Elasticsearch for better product search
2. **Caching**: Redis for frequently accessed data
3. **Analytics**: Order and customer analytics endpoints
4. **Webhooks**: For integration with external systems
5. **API Rate Limiting**: Protect against abuse

---

*This implementation plan is subject to adjustment based on discoveries during development.*
