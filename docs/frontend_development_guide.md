# Frontend development guide

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

**Description**: Retrieves all products with pagination support and optional filtering

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/products/" \
  -H "accept: application/json"
```

**cURL Example** (with pagination):
```bash
curl -X GET "http://localhost:8001/api/v1/products/?skip=0&limit=10" \
  -H "accept: application/json"
```

**cURL Example** (include deleted):
```bash
curl -X GET "http://localhost:8001/api/v1/products/?include_deleted=true" \
  -H "accept: application/json"
```

**cURL Example** (filter by category):
```bash
curl -X GET "http://localhost:8001/api/v1/products/?category_id=1" \
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
    "id": 8,
    "created_at": "2025-07-26T14:47:12.000000Z",
    "updated_at": "2025-07-26T14:47:12.000000Z",
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

**Parameters**:
- `skip` (integer, optional): Number of products to skip for pagination (default: 0)
- `limit` (integer, optional): Maximum number of products to return (default: 100, max: 1000)
- `include_deleted` (boolean, optional): Whether to include soft-deleted products (default: false)
- `category_id` (integer, optional): Filter products by category ID

#### 2. Get Specific Product

**Use Case**: Display product details page

**API**: `GET /api/v1/products/{product_id}`

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/products/8" \
  -H "accept: application/json"
```

**cURL Example** (include deleted):
```bash
curl -X GET "http://localhost:8001/api/v1/products/8?include_deleted=true" \
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
  "id": 8,
  "created_at": "2025-07-26T14:47:12.000000Z",
  "updated_at": "2025-07-26T14:47:12.000000Z",
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
curl -X POST "http://localhost:8001/api/v1/products/" \
  -H "accept: application/json" \
  -F "nume=Fresh Apples" \
  -F "cantitate=50" \
  -F "pret=25" \
  -F "description=Fresh organic apples from local farm" \
  -F "category_id=1" \
  -F "unitati_id=1" \
  -F "stock=50"
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
  "id": 8,
  "created_at": "2025-07-26T14:47:12.000000Z",
  "updated_at": "2025-07-26T14:47:12.000000Z",
  "is_deleted": false,
  "images": [],
  "image_versions": {
    "original": "/api/v1/static/placeholders/product_placeholder.jpg",
    "medium": "/api/v1/static/placeholders/product_placeholder.jpg",
    "thumbnail": "/api/v1/static/placeholders/product_placeholder.jpg"
  }
}
```

**Required Fields**:
- `nume` (string): Product name
- `cantitate` (integer): Product quantity (must be >= 0)
- `pret` (float): Product price (must be > 0)
- `category_id` (integer): ID of the associated category (must be > 0)
- `unitati_id` (integer): ID of the associated unit (must be > 0)
- `stock` (integer): Stock quantity (must be >= 0)

**Optional Fields**:
- `description` (string): Product description

#### 4. Partially Update Product

**Use Case**: Admin updating specific product fields

**API**: `PATCH /api/v1/products/{product_id}`

**Description**: Partially updates a product resource. Only updates fields explicitly provided.

**cURL Example** (update name and price):
```bash
curl -X PATCH "http://localhost:8001/api/v1/products/8" \
  -H "accept: application/json" \
  -F "nume=Premium Fresh Apples" \
  -F "pret=30"
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
  "stock": 50,
  "id": 8,
  "created_at": "2025-07-26T14:47:12.000000Z",
  "updated_at": "2025-07-26T14:48:20.000000Z",
  "is_deleted": false,
  "images": [],
  "image_versions": {
    "original": "/api/v1/static/placeholders/product_placeholder.jpg",
    "medium": "/api/v1/static/placeholders/product_placeholder.jpg",
    "thumbnail": "/api/v1/static/placeholders/product_placeholder.jpg"
  }
}
```

**Optional Fields** (all fields are optional for PATCH):
- `nume` (string): Product name
- `cantitate` (integer): Product quantity (must be >= 0)
- `pret` (float): Product price (must be > 0)
- `description` (string): Product description
- `category_id` (integer): ID of the associated category (must be > 0)
- `unitati_id` (integer): ID of the associated unit (must be > 0)
- `stock` (integer): Stock quantity (must be >= 0)

#### 5. Delete Product

**Use Case**: Admin removing products (soft delete by default)

**API**: `DELETE /api/v1/products/{product_id}`

**cURL Example** (soft delete - default):
```bash
curl -X DELETE "http://localhost:8001/api/v1/products/8" \
  -H "accept: application/json"
```

**cURL Example** (permanent delete):
```bash
curl -X DELETE "http://localhost:8001/api/v1/products/8?permanent=true" \
  -H "accept: application/json"
```

**Parameter:**
- `permanent` (boolean, optional): If true, performs a hard delete instead of a soft deletion (default: false)

**Response**: HTTP 204 No Content (successful deletion)

#### 6. Upload Product Image

**Use Case**: Admin adding product images after creation

**API**: `POST /api/v1/products/{product_id}/images`

**cURL Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/products/8/images" \
  -H "accept: application/json" \
  -F "file=@apples.jpg" \
  -F "position=0"
```

**Response Example**:
```json
{
  "path": "products/66197beeaf4b425382d2e450aa603aad",
  "position": 0,
  "id": 4,
  "produse_id": 8,
  "is_primary": true,
  "image_versions": {
    "original": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad.jpg",
    "medium": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-medium.jpg",
    "thumbnail": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-thumbnail.jpg"
  }
}
```

**Parameters**:
- `file` (file, required): Image file to upload (JPEG, PNG, or GIF, max 5MB)
- `position` (integer, optional): Image position (0=primary, if not specified will be added at the end)

#### 7. Get Product Images

**Use Case**: Display product image gallery

**API**: `GET /api/v1/products/{product_id}/images`

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/products/8/images" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "path": "products/66197beeaf4b425382d2e450aa603aad",
    "position": 0,
    "id": 4,
    "produse_id": 8,
    "is_primary": true,
    "image_versions": {
      "original": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad.jpg",
      "medium": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-medium.jpg",
      "thumbnail": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-thumbnail.jpg"
    }
  }
]
```

#### 8. Get Specific Product Image

**Use Case**: Display specific product image

**API**: `GET /api/v1/products/{product_id}/images/{image_id}`

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/products/8/images/4" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "path": "products/66197beeaf4b425382d2e450aa603aad",
  "position": 0,
  "id": 4,
  "produse_id": 8,
  "is_primary": true,
  "image_versions": {
    "original": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad.jpg",
    "medium": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-medium.jpg",
    "thumbnail": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-thumbnail.jpg"
  }
}
```

#### 9. Update Image Position

**Use Case**: Admin reordering product images

**API**: `PUT /api/v1/products/{product_id}/images/{image_id}/position`

**cURL Example**:
```bash
curl -X PUT "http://localhost:8001/api/v1/products/8/images/4/position" \
  -H "accept: application/json" \
  -F "position=1"
```

**Response Example**:
```json
{
  "path": "products/66197beeaf4b425382d2e450aa603aad",
  "position": 1,
  "id": 4,
  "produse_id": 8,
  "is_primary": false,
  "image_versions": {
    "original": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad.jpg",
    "medium": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-medium.jpg",
    "thumbnail": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-thumbnail.jpg"
  }
}
```

**Parameters**:
- `position` (integer, required): New position for the image (0=primary)

#### 10. Set Image as Primary

**Use Case**: Admin setting a product image as primary

**API**: `PUT /api/v1/products/{product_id}/images/{image_id}/primary`

**cURL Example**:
```bash
curl -X PUT "http://localhost:8001/api/v1/products/8/images/4/primary" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "path": "products/66197beeaf4b425382d2e450aa603aad",
  "position": 0,
  "id": 4,
  "produse_id": 8,
  "is_primary": true,
  "image_versions": {
    "original": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad.jpg",
    "medium": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-medium.jpg",
    "thumbnail": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-thumbnail.jpg"
  }
}
```

#### 11. Delete Product Image

**Use Case**: Admin removing product images

**API**: `DELETE /api/v1/products/{product_id}/images/{image_id}`

**cURL Example**:
```bash
curl -X DELETE "http://localhost:8001/api/v1/products/8/images/4" \
  -H "accept: application/json"
```

**Response**: HTTP 204 No Content (successful deletion)

#### 12. Reorder Product Images

**Use Case**: Admin reordering multiple product images at once

**API**: `PUT /api/v1/products/{product_id}/images/reorder`

**cURL Example**:
```bash
curl -X PUT "http://localhost:8001/api/v1/products/8/images/reorder" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '[
    {"id": 4, "position": 0},
    {"id": 5, "position": 1},
    {"id": 6, "position": 2}
  ]'
```

**Response Example**:
```json
[
  {
    "path": "products/66197beeaf4b425382d2e450aa603aad",
    "position": 0,
    "id": 4,
    "produse_id": 8,
    "is_primary": true,
    "image_versions": {
      "original": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad.jpg",
      "medium": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-medium.jpg",
      "thumbnail": "products/66197beeaf4b425382d2e450aa603aad/66197beeaf4b425382d2e450aa603aad-thumbnail.jpg"
    }
  }
]
```

**Request Body**: Array of objects with `id` and `position` fields

#### Error Handling Examples

**404 Not Found**:
```bash
curl -X GET "http://localhost:8001/api/v1/products/999"
# Response: 404 {"detail":"Product with ID 999 not found"}
```

**422 Validation Error** (missing required fields):
```bash
curl -X POST "http://localhost:8001/api/v1/products/" \
  -H "accept: application/json" \
  -F "description=Fresh apples"
# Response: 422 {"detail":[{"type":"missing","loc":["body","nume"],"msg":"Field required","input":null},{"type":"missing","loc":["body","cantitate"],"msg":"Field required","input":null},{"type":"missing","loc":["body","pret"],"msg":"Field required","input":null},{"type":"missing","loc":["body","category_id"],"msg":"Field required","input":null},{"type":"missing","loc":["body","unitati_id"],"msg":"Field required","input":null},{"type":"missing","loc":["body","stock"],"msg":"Field required","input":null}]}
```

**400 Bad Request** (invalid foreign key):
```bash
curl -X POST "http://localhost:8001/api/v1/products/" \
  -H "accept: application/json" \
  -F "nume=Fresh Apples" \
  -F "cantitate=50" \
  -F "pret=25" \
  -F "category_id=999" \
  -F "unitati_id=1" \
  -F "stock=50"
# Response: 400 {"detail":[{"loc":["body","category_id"],"msg":"Invalid category ID","type":"value_error.foreign_key"}]}
```

### Lista 

(de produse disponibile pentru urmatoarea comanda)

#### 1. Get All Lists

**Use Case**: Display all available product lists

**API**: `GET /api/v1/liste/`

**Description**: Retrieves all lists with pagination support and optional inclusion of deleted ones

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/liste/" \
  -H "accept: application/json"
```

**cURL Example** (with pagination):
```bash
curl -X GET "http://localhost:8001/api/v1/liste/?skip=0&limit=10" \
  -H "accept: application/json"
```

**cURL Example** (include deleted):
```bash
curl -X GET "http://localhost:8001/api/v1/liste/?include_deleted=true" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "data": "2025-07-26",
    "is_current": true,
    "is_published": false,
    "mesaj_introducere": "Test List",
    "alte_detalii": "Test details",
    "numar_whatsapp": "+40712345678",
    "orare_livrari_id": 8,
    "id": 19,
    "created_at": "2025-07-26T15:10:57",
    "updated_at": "2025-07-26T15:10:57",
    "is_deleted": false
  }
]
```

**Parameters**:
- `skip` (integer, optional): Number of lists to skip for pagination (default: 0)
- `limit` (integer, optional): Maximum number of lists to return (default: 100, max: 1000)
- `include_deleted` (boolean, optional): Whether to include soft-deleted lists (default: false)

#### 2. Get Specific List

**Use Case**: Display specific list details

**API**: `GET /api/v1/liste/{list_id}`

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/liste/19" \
  -H "accept: application/json"
```

**cURL Example** (include deleted):
```bash
curl -X GET "http://localhost:8001/api/v1/liste/19?include_deleted=true" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "data": "2025-07-26",
  "is_current": true,
  "is_published": false,
  "mesaj_introducere": "Test List",
  "alte_detalii": "Test details",
  "numar_whatsapp": "+40712345678",
  "orare_livrari_id": 8,
  "id": 19,
  "created_at": "2025-07-26T15:10:57",
  "updated_at": "2025-07-26T15:10:57",
  "is_deleted": false
}
```

#### 3. Create New List

**Use Case**: Admin creating a new product list

**API**: `POST /api/v1/liste/`

**cURL Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/liste/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "data": "2025-07-26",
    "is_current": true,
    "is_published": false,
    "mesaj_introducere": "Test List",
    "alte_detalii": "Test details",
    "numar_whatsapp": "+40712345678",
    "orare_livrari_id": 8
  }'
```

**Response Example**:
```json
{
  "data": "2025-07-26",
  "is_current": true,
  "is_published": false,
  "mesaj_introducere": "Test List",
  "alte_detalii": "Test details",
  "numar_whatsapp": "+40712345678",
  "orare_livrari_id": 8,
  "id": 19,
  "created_at": "2025-07-26T15:10:57",
  "updated_at": "2025-07-26T15:10:57",
  "is_deleted": false
}
```

**Required Fields**:
- `data` (date): Date of the list (format: YYYY-MM-DD)
- `is_current` (boolean): Flag indicating if this is the current list
- `orare_livrari_id` (integer): ID of the associated delivery schedule (must be > 0)

**Optional Fields**:
- `is_published` (boolean): Flag indicating if the list is published
- `mesaj_introducere` (string): Introduction message for the list (max 45 characters)
- `alte_detalii` (string): Additional details for the list (max 500 characters)
- `numar_whatsapp` (string): WhatsApp number for contact (format: +?[0-9]{10,15})

#### 4. Partially Update List

**Use Case**: Admin updating specific list fields

**API**: `PATCH /api/v1/liste/{list_id}`

**Description**: Partially updates a list resource. Only updates fields explicitly provided.

**cURL Example**:
```bash
curl -X PATCH "http://localhost:8001/api/v1/liste/19" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "mesaj_introducere": "Updated Test List",
    "is_published": true
  }'
```

**Response Example**:
```json
{
  "data": "2025-07-26",
  "is_current": true,
  "is_published": true,
  "mesaj_introducere": "Updated Test List",
  "alte_detalii": "Test details",
  "numar_whatsapp": "+40712345678",
  "orare_livrari_id": 8,
  "id": 19,
  "created_at": "2025-07-26T15:10:57",
  "updated_at": "2025-07-26T15:11:10",
  "is_deleted": false
}
```

**Optional Fields** (all fields are optional for PATCH):
- `data` (date): Date of the list (format: YYYY-MM-DD)
- `is_current` (boolean): Flag indicating if this is the current list
- `is_published` (boolean): Flag indicating if the list is published
- `mesaj_introducere` (string): Introduction message for the list (max 45 characters)
- `alte_detalii` (string): Additional details for the list (max 500 characters)
- `numar_whatsapp` (string): WhatsApp number for contact (format: +?[0-9]{10,15})
- `orare_livrari_id` (integer): ID of the associated delivery schedule (must be > 0)

#### 5. Update List (Full Replacement)

**Use Case**: Admin completely replacing list information

**API**: `PUT /api/v1/liste/{list_id}`

**Description**: Fully replaces a list resource. All fields are required for PUT operations.

**cURL Example**:
```bash
curl -X PUT "http://localhost:8001/api/v1/liste/19" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "data": "2025-07-27",
    "is_current": false,
    "is_published": true,
    "mesaj_introducere": "Full Update List",
    "alte_detalii": "Updated details",
    "numar_whatsapp": "+40787654321",
    "orare_livrari_id": 9
  }'
```

**Response Example**:
```json
{
  "data": "2025-07-27",
  "is_current": false,
  "is_published": true,
  "mesaj_introducere": "Full Update List",
  "alte_detalii": "Updated details",
  "numar_whatsapp": "+40787654321",
  "orare_livrari_id": 9,
  "id": 19,
  "created_at": "2025-07-26T15:10:57",
  "updated_at": "2025-07-26T15:11:18",
  "is_deleted": false
}
```

**Required Fields** (all fields are required for PUT):
- `data` (date): Date of the list (format: YYYY-MM-DD)
- `is_current` (boolean): Flag indicating if this is the current list
- `is_published` (boolean): Flag indicating if the list is published
- `mesaj_introducere` (string): Introduction message for the list (max 45 characters)
- `alte_detalii` (string): Additional details for the list (max 500 characters)
- `numar_whatsapp` (string): WhatsApp number for contact (format: +?[0-9]{10,15})
- `orare_livrari_id` (integer): ID of the associated delivery schedule (must be > 0)

#### 6. Delete List

**Use Case**: Admin removing lists (soft delete by default)

**API**: `DELETE /api/v1/liste/{list_id}`

**cURL Example** (soft delete - default):
```bash
curl -X DELETE "http://localhost:8001/api/v1/liste/19" \
  -H "accept: application/json"
```

**cURL Example** (hard delete):
```bash
curl -X DELETE "http://localhost:8001/api/v1/liste/19?soft_delete=false" \
  -H "accept: application/json"
```

**Parameter:**
- `soft_delete` (boolean, optional): If true, performs a soft delete; otherwise, hard delete (default: true)

**Response Example** (soft delete):
```json
{
  "message": "List with ID 19 has been soft deleted"
}
```

#### Error Handling Examples

**404 Not Found**:
```bash
curl -X GET "http://localhost:8001/api/v1/liste/999"
# Response: 404 {"detail":"List with ID 999 not found"}
```

**422 Validation Error** (missing required fields):
```bash
curl -X POST "http://localhost:8001/api/v1/liste/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"mesaj_introducere": "Test List"}'
# Response: 422 {"detail":[{"type":"missing","loc":["body","data"],"msg":"Field required","input":{"mesaj_introducere":"Test List"}},{"type":"missing","loc":["body","is_current"],"msg":"Field required","input":{"mesaj_introducere":"Test List"}},{"type":"missing","loc":["body","orare_livrari_id"],"msg":"Field required","input":{"mesaj_introducere":"Test List"}}]}
```

**400 Bad Request** (invalid foreign key):
```bash
curl -X POST "http://localhost:8001/api/v1/liste/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"data": "2025-07-26", "is_current": true, "orare_livrari_id": 999}'
# Response: 400 {"detail":"Invalid delivery schedule ID: 999"}
```

### Comenzi


