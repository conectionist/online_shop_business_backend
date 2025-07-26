# Frontend development guide

WARNING!
Not up-to-date yet!
DO NOT USE!

## Introducere

Frontend-ul are nevoie de urmatoarele:
- categorii
	- create new category
	- get all categories
	- get specific category
	- edit specific category
	- delete specific category
- produse
	- create new product
	- get all products
	- get specific product
	- edit specific product
	- delete specific product
	- delete multiple products
- lista (de produse disponibile pentru urmatoarea comanda)
	- create new list
	- add (one or more) products to list
	- remove (one or more) products from list
	- invalidate (one or more) products from list (suspend the ability to purchase them)
	- edit product in list (just for that list. keep the original product intact)
	- publish list
	- unpublish list
	- set date
	- change date
	- set payment methods
	- update payment methods
	- set address
	- update address
	- set additional info
	- update additional info (e.g. "Am adaugat produse de la bacania boiereasca")
	- adauga orar livrari/ridicari
	- modifica orar livrari/ridicari
	- adauga mod de livrare/ridicare
	- modifica mod de livrare/ridicare
	- vezi liste anterioare
	- tipuri de plata acceptate
	- adauga alte detalii
	- modifica alte detalii (ex: "azi nu sunt la brutarie", "intarzii cu livrarile din cauza traficului", etc.)
	- adauga nr whatsapp
	- modifica nr whatsapp
	- get current list
	- get old lists
- comanda
	- create new command
	- get all commands (current or past)
	- get specific command(s)
	- edit command
	- delete command

## Detaliere

### Categorii

#### 1. Get All Categories
**Use Case**: Display category navigation menu
**API**: `GET /api/v1/categories`
**Description**: Retrieves all categories with pagination and optional inclusion of deleted ones

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/categories" \
  -H "accept: application/json"
```

**cURL Example** (include deleted):
```bash
curl -X GET "http://localhost:8000/api/v1/categories?include_deleted=true" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "id": 62,
    "name": "Test Category with Image",
    "image_path": "categories/21902c3b5129433ea7d1fb73c40f251f",
    "image_versions": {
      "original": "categories/21902c3b5129433ea7d1fb73c40f251f/21902c3b5129433ea7d1fb73c40f251f.jpg",
      "medium": "categories/21902c3b5129433ea7d1fb73c40f251f/21902c3b5129433ea7d1fb73c40f251f-medium.jpg",
      "thumbnail": "categories/21902c3b5129433ea7d1fb73c40f251f/21902c3b5129433ea7d1fb73c40f251f-thumbnail.jpg"
    },
    "is_deleted": false,
    "created_at": "2025-07-26T07:23:15.000000Z",
    "updated_at": "2025-07-26T07:23:15.000000Z"
  },
  {
    "id": 61,
    "name": "Test Category",
    "image_path": null,
    "image_versions": {
      "original": "/api/v1/static/placeholders/category_placeholder.jpg",
      "medium": "/api/v1/static/placeholders/category_placeholder.jpg",
      "thumbnail": "/api/v1/static/placeholders/category_placeholder.jpg"
    },
    "is_deleted": false,
    "created_at": "2025-07-26T07:23:06.000000Z",
    "updated_at": "2025-07-26T07:23:06.000000Z"
  }
]
```

#### 2. Get Specific Category
**Use Case**: Display category details or products for a specific category
**API**: `GET /api/v1/categories/{category_id}`

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/categories/1" \
  -H "accept: application/json"
```

**cURL Example** (include deleted):
```bash
curl -X GET "http://localhost:8000/api/v1/categories/1?include_deleted=true" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "id": 62,
  "name": "Test Category with Image",
  "image_path": "categories/21902c3b5129433ea7d1fb73c40f251f",
  "image_versions": {
    "original": "categories/21902c3b5129433ea7d1fb73c40f251f/21902c3b5129433ea7d1fb73c40f251f.jpg",
    "medium": "categories/21902c3b5129433ea7d1fb73c40f251f/21902c3b5129433ea7d1fb73c40f251f-medium.jpg",
    "thumbnail": "categories/21902c3b5129433ea7d1fb73c40f251f/21902c3b5129433ea7d1fb73c40f251f-thumbnail.jpg"
  },
  "is_deleted": false,
  "created_at": "2025-07-26T07:23:15.000000Z",
  "updated_at": "2025-07-26T07:23:15.000000Z"
}
```

#### 3. Create New Category
**Use Case**: Admin adding new product categories
**API**: `POST /api/v1/categories/`

**cURL Example** (basic category):
```bash
curl -X POST "http://localhost:8000/api/v1/categories/" \
  -H "accept: application/json" \
  -F "name=Fruits"
```

**cURL Example** (with image upload during creation):
```bash
curl -X POST "http://localhost:8000/api/v1/categories/" \
  -H "accept: application/json" \
  -F "name=Fruits" \
  -F "primary_image=@fruits.jpg"
```

**Response Example**:
```json
{
  "id": 5,
  "name": "Fruits",
  "image_path": "categories/f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "image_versions": {
    "original": "categories/f47ac10b-58cc-4372-a567-0e02b2c3d479/f47ac10b-58cc-4372-a567-0e02b2c3d479.jpg",
    "medium": "categories/f47ac10b-58cc-4372-a567-0e02b2c3d479/f47ac10b-58cc-4372-a567-0e02b2c3d479-medium.jpg",
    "thumbnail": "categories/f47ac10b-58cc-4372-a567-0e02b2c3d479/f47ac10b-58cc-4372-a567-0e02b2c3d479-thumbnail.jpg"
  },
  "is_deleted": false,
  "created_at": "2024-01-15T10:30:00.000000Z",
  "updated_at": "2024-01-15T10:30:00.000000Z"
}
```

#### 4. Edit Specific Category (Full Update)
**Use Case**: Admin completely replacing category information
**API**: `PUT /api/v1/categories/{category_id}`
**Description**: Fully replaces a category resource. The `name` field is required. If no image is provided and `clear_image` is false, the image will be reset to null (placeholder). If `clear_image` is true, the image will be cleared. If an image is provided, it will replace the existing image.

**cURL Example** (update name only - will reset image to placeholder):
```bash
curl -X PUT "http://localhost:8000/api/v1/categories/3" \
  -H "accept: application/json" \
  -F "name=Fresh Fruits & Berries"
```

**cURL Example** (update with new image):
```bash
curl -X PUT "http://localhost:8000/api/v1/categories/3" \
  -H "accept: application/json" \
  -F "name=Fresh Fruits" \
  -F "primary_image=@fresh_fruits.jpg"
```

**cURL Example** (clear image and use placeholder):
```bash
curl -X PUT "http://localhost:8000/api/v1/categories/3" \
  -H "accept: application/json" \
  -F "name=Fresh Fruits" \
  -F "clear_image=true"
```

**Parameter:**
- `clear_image` (boolean, optional): If true, clears the image and uses the placeholder image for the category.

#### 5. Partially Update Category
**Use Case**: Admin updating specific category fields
**API**: `PATCH /api/v1/categories/{category_id}`
**Description**: Partially updates a category resource. Only updates fields explicitly provided. If no image is provided and `clear_image` is false, the existing image is preserved. If `clear_image` is true, the image will be cleared. If an image is provided, it will replace the existing image.

**cURL Example** (update name only - preserves existing image):
```bash
curl -X PATCH "http://localhost:8000/api/v1/categories/3" \
  -H "accept: application/json" \
  -F "name=Fresh Fruits & Berries"
```

**cURL Example** (update with new image):
```bash
curl -X PATCH "http://localhost:8000/api/v1/categories/1/" \
  -H "accept: application/json" \
  -F "primary_image=@fresh_fruits.jpg"
```

**cURL Example** (clear image and use placeholder):
```bash
curl -X PATCH "http://localhost:8000/api/v1/categories/1/" \
  -H "accept: application/json" \
  -F "clear_image=true"
```

**Parameter:**
- `clear_image` (boolean, optional): If true, clears the image and uses the placeholder image for the category.

**Response Example (PUT with name only - image reset to placeholder):**
```json
{
  "id": 3,
  "name": "Fresh Fruits & Berries",
  "image_path": null,
  "image_versions": {
    "original": "/api/v1/static/placeholders/category_placeholder.jpg",
    "medium": "/api/v1/static/placeholders/category_placeholder.jpg",
    "thumbnail": "/api/v1/static/placeholders/category_placeholder.jpg"
  },
  "is_deleted": false,
  "created_at": "2024-01-15T10:30:00.000000Z",
  "updated_at": "2024-01-15T15:45:00.000000Z"
}
```

**Response Example (PUT with new image):**
```json
{
  "id": 3,
  "name": "Fresh Fruits",
  "image_path": "categories/a1b2c3d4-5678-90ab-cdef-098765432109",
  "image_versions": {
    "original": "categories/a1b2c3d4-5678-90ab-cdef-098765432109/a1b2c3d4-5678-90ab-cdef-098765432109.jpg",
    "medium": "categories/a1b2c3d4-5678-90ab-cdef-098765432109/a1b2c3d4-5678-90ab-cdef-098765432109-medium.jpg",
    "thumbnail": "categories/a1b2c3d4-5678-90ab-cdef-098765432109/a1b2c3d4-5678-90ab-cdef-098765432109-thumbnail.jpg"
  },
  "is_deleted": false,
  "created_at": "2024-01-15T10:30:00.000000Z",
  "updated_at": "2024-01-15T15:45:00.000000Z"
}
```

**Response Example (PATCH with name only - preserves existing image):**
```json
{
  "id": 3,
  "name": "Fresh Fruits & Berries",
  "image_path": "categories/a1b2c3d4-5678-90ab-cdef-098765432109",
  "image_versions": {
    "original": "categories/a1b2c3d4-5678-90ab-cdef-098765432109/a1b2c3d4-5678-90ab-cdef-098765432109.jpg",
    "medium": "categories/a1b2c3d4-5678-90ab-cdef-098765432109/a1b2c3d4-5678-90ab-cdef-098765432109-medium.jpg",
    "thumbnail": "categories/a1b2c3d4-5678-90ab-cdef-098765432109/a1b2c3d4-5678-90ab-cdef-098765432109-thumbnail.jpg"
  },
  "is_deleted": false,
  "created_at": "2024-01-15T10:30:00.000000Z",
  "updated_at": "2024-01-15T15:45:00.000000Z"
}
```

#### 6. Delete Category
**Use Case**: Admin removing categories (soft delete)
**API**: `DELETE /api/v1/categories/{category_id}`

**cURL Example** (soft delete - default):
```bash
curl -X DELETE "http://localhost:8000/api/v1/categories/4" \
  -H "accept: application/json"
```

**cURL Example** (permanent delete):
```bash
curl -X DELETE "http://localhost:8000/api/v1/categories/4?permanent=true" \
  -H "accept: application/json"
```

**Parameter:**
- `permanent` (boolean, optional): If true, performs a permanent (hard) delete. Otherwise, performs a soft delete.

**Response**: HTTP 204 No Content (successful deletion)

#### Soft Delete Restoration Behavior

When creating a category with a name that matches a previously soft-deleted category, the system will **restore the deleted category** instead of creating a new one. This ensures data consistency and prevents accidental duplicates.

**Example**:
1. Create category "Fruits" (ID: 5)
2. Soft delete category "Fruits" 
3. Create category "Fruits" again → **Restores the original category (ID: 5)** instead of creating a new one

**Response for restoration**:
```json
{
  "id": 5,
  "name": "Fruits",
  "image_path": null,
  "created_at": "2024-01-15T10:30:00.000000Z",
  "updated_at": "2024-01-15T15:45:00.000000Z",
  "is_deleted": false,
  "image_versions": {
    "original": "/api/v1/static/placeholders/category_placeholder.jpg",
    "medium": "/api/v1/static/placeholders/category_placeholder.jpg",
    "thumbnail": "/api/v1/static/placeholders/category_placeholder.jpg"
  }
}
```

#### Error Handling Examples

**404 Not Found**:
```bash
curl -X GET "http://localhost:8000/api/v1/categories/999"
# Response: 404 {"detail":"Category with ID 999 not found"}
```

**422 Validation Error** (missing required field):
```bash
curl -X POST "http://localhost:8000/api/v1/categories" \
  -H "accept: application/json" \
  -F "image=@category.jpg"
# Response: 422 {"detail":"1 validation error for CategoryCreate\nname\n  String should have at least 1 character [type=string_too_short, input_value='', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_too_short"}
```

**409 Conflict** (duplicate category name):
```bash
curl -X POST "http://localhost:8000/api/v1/categories" \
  -H "accept: application/json" \
  -F "name=Fruits"
# Response: 409 {"detail":"Category with name 'Fruits' already exists"}
```

### Produse

#### 1. Get All Products
**Use Case**: Display product catalog or listings
**API**: `GET /api/v1/products/`
**Description**: Retrieves all products with pagination support

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/products/" \
  -H "accept: application/json"
```

**cURL Example** (with pagination):
```bash
curl -X GET "http://localhost:8000/api/v1/products/?skip=0&limit=10" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "nume": "Fresh Apples",
    "cantitate": 50,
    "pret": 25,
    "description": "Fresh organic apples from local farm",
    "category_id": 1,
    "unitati_id": 1,
    "stock": 50,
    "id": 9,
    "created_at": "2024-01-15T10:30:45.000000Z",
    "updated_at": "2024-01-15T10:30:45.000000Z",
    "is_deleted": false,
    "images": [],
    "image_versions": {
      "original": "/api/v1/static/placeholders/product_placeholder.jpg",
      "medium": "/api/v1/static/placeholders/product_placeholder.jpg",
      "thumbnail": "/api/v1/static/placeholders/product_placeholder.jpg"
    }
  }
]
```

#### 2. Get Specific Product
**Use Case**: Display product details page
**API**: `GET /api/v1/products/{product_id}/`

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/products/9/" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "nume": "Fresh Apples",
  "cantitate": 50,
  "pret": 25,
  "description": "Fresh organic apples from local farm",
  "category_id": 1,
  "unitati_id": 1,
  "stock": 50,
  "id": 9,
  "created_at": "2024-01-15T10:30:45.000000Z",
  "updated_at": "2024-01-15T10:30:45.000000Z",
  "is_deleted": false,
  "images": [],
  "image_versions": {
    "original": "/api/v1/static/placeholders/product_placeholder.jpg",
    "medium": "/api/v1/static/placeholders/product_placeholder.jpg",
    "thumbnail": "/api/v1/static/placeholders/product_placeholder.jpg"
  }
}
```

#### 3. Create New Product
**Use Case**: Admin adding new products to catalog
**API**: `POST /api/v1/products/`

**cURL Example** (basic product):
```bash
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "accept: application/json" \
  -F "nume=Fresh Apples" \
  -F "cantitate=50" \
  -F "pret=25" \
  -F "description=Fresh organic apples from local farm" \
  -F "category_id=1" \
  -F "unitati_id=1" \
  -F "stock=50"
```

**cURL Example** (with images):
```bash
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "accept: application/json" \
  -F "nume=Fresh Apples" \
  -F "cantitate=50" \
  -F "pret=25" \
  -F "description=Fresh organic apples from local farm" \
  -F "category_id=1" \
  -F "unitati_id=1" \
  -F "stock=50" \
  -F "primary_image=@apples.jpg"
```

**Response Example**:
```json
{
  "nume": "Fresh Apples",
  "cantitate": 50,
  "pret": 25,
  "description": "Fresh organic apples from local farm",
  "category_id": 1,
  "unitati_id": 1,
  "stock": 50,
  "id": 9,
  "created_at": "2024-01-15T10:30:45.000000Z",
  "updated_at": "2024-01-15T10:30:45.000000Z",
  "is_deleted": false,
  "images": [],
  "image_versions": {
    "original": "/api/v1/static/placeholders/product_placeholder.jpg",
    "medium": "/api/v1/static/placeholders/product_placeholder.jpg",
    "thumbnail": "/api/v1/static/placeholders/product_placeholder.jpg"
  }
}
```

#### 4. Update Product
**Use Case**: Admin updating product information
**API**: `PUT /api/v1/products/{product_id}/`

**cURL Example** (update basic fields):
```bash
curl -X PUT "http://localhost:8000/api/v1/products/9/" \
  -H "accept: application/json" \
  -F "nume=Premium Fresh Apples" \
  -F "pret=30" \
  -F "stock=45"
```

**cURL Example** (update with new image):
```bash
curl -X PUT "http://localhost:8000/api/v1/products/9/" \
  -H "accept: application/json" \
  -F "nume=Premium Fresh Apples" \
  -F "pret=30" \
  -F "primary_image=@premium_apples.jpg"
```

**cURL Example** (clear image and use placeholder):
```bash
curl -X PUT "http://localhost:8000/api/v1/products/9/" \
  -H "accept: application/json" \
  -F "clear_image=true"
```

#### 6. Upload Category Image (Separate Endpoint)
**Use Case**: Admin adding/updating category image after creation
**API**: `POST /api/v1/categories/{category_id}/image`

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/categories/1/image" \
  -H "accept: application/json" \
  -F "file=@vegetables.jpg"
```

**Response Example**:
```json
{
  "name": "Vegetables",
  "image_path": "categories/5ca42f29580e43edaecca182e7680fe2",
  "id": 2,
  "created_at": "2024-01-15T10:30:45.000000Z",
  "updated_at": "2024-01-15T15:45:00.000000Z",
  "is_deleted": false,
  "image_versions": {
    "original": "categories/5ca42f29580e43edaecca182e7680fe2/5ca42f29580e43edaecca182e7680fe2.jpg",
    "medium": "categories/5ca42f29580e43edaecca182e7680fe2/5ca42f29580e43edaecca182e7680fe2-medium.jpg",
    "thumbnail": "categories/5ca42f29580e43edaecca182e7680fe2/5ca42f29580e43edaecca182e7680fe2-thumbnail.jpg"
  }
}
```

#### 7. Upload Product Images (Separate Endpoint)
**Use Case**: Admin adding product images after creation
**API**: `POST /api/v1/products/{product_id}/images/`

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/products/9/images/" \
  -H "accept: application/json" \
  -F "file=@apples.jpg" \
  -F "position=0"
```

**Response Example**:
```json
{
  "id": 1,
  "product_id": 9,
  "filename": "apples.jpg",
  "position": 0,
  "file_path": "products/8f47ac10b58cc4372a5670e02b2c3d479/apples.jpg",
  "file_versions": {
    "original": "products/8f47ac10b58cc4372a5670e02b2c3d479/apples.jpg",
    "medium": "products/8f47ac10b58cc4372a5670e02b2c3d479/apples-medium.jpg",
    "thumbnail": "products/8f47ac10b58cc4372a5670e02b2c3d479/apples-thumbnail.jpg"
  },
  "created_at": "2024-01-15T15:45:00.000000Z"
}
```

**Response Example**:
```json
{
  "nume": "Premium Fresh Apples",
  "cantitate": 50,
  "pret": 30,
  "description": "Fresh organic apples from local farm",
  "category_id": 1,
  "unitati_id": 1,
  "stock": 45,
  "id": 9,
  "created_at": "2024-01-15T10:30:45.000000Z",
  "updated_at": "2024-01-15T15:45:00.000000Z",
  "is_deleted": false,
  "images": [],
  "image_versions": {
    "original": "/api/v1/static/placeholders/product_placeholder.jpg",
    "medium": "/api/v1/static/placeholders/product_placeholder.jpg",
    "thumbnail": "/api/v1/static/placeholders/product_placeholder.jpg"
  }
}
```

#### 5. Delete Product
**Use Case**: Admin removing products (soft delete by default)
**API**: `DELETE /api/v1/products/{product_id}/`

**cURL Example** (soft delete - default):
```bash
curl -X DELETE "http://localhost:8000/api/v1/products/9/" \
  -H "accept: application/json"
```

**cURL Example** (permanent delete):
```bash
curl -X DELETE "http://localhost:8000/api/v1/products/9/?permanent=true" \
  -H "accept: application/json"
```

**Response**: HTTP 204 No Content (successful deletion)

#### Error Handling Examples

**404 Not Found**:
```bash
curl -X GET "http://localhost:8000/api/v1/products/999/"
# Response: 404 {"detail":"Product with ID 999 not found"}
```

**422 Validation Error** (missing required field):
```bash
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "accept: application/json" \
  -F "description=Fresh apples"
# Response: 422 {"detail":[{"loc":["body","nume"],"msg":"field required","type":"value_error.missing"}]}
```

**409 Conflict** (duplicate product name):
```bash
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "accept: application/json" \
  -F "nume=Fresh Apples" \
  -F "cantitate=50" \
  -F "pret=25" \
  -F "category_id=1" \
  -F "unitati_id=1"
# Response: 409 {"detail":"Product with name 'Fresh Apples' already exists"}
```

### Lista 

(de produse disponibile pentru urmatoarea comanda)

### Comenzi


