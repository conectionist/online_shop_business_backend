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

**What is this?** Categories are the organizational backbone of your product catalog. They help customers find products by grouping similar items together.

**What is it for?** Categories provide structure and navigation for your online shop. Think of them like the aisles in a physical store - "Fruits & Vegetables", "Dairy", "Bakery", etc.

**Why do you need it?** Without categories, customers would have to browse through all products to find what they want. Categories make shopping efficient and intuitive.

**What's its purpose?** Categories serve multiple purposes:
- **Customer Experience**: Easy navigation and product discovery
- **Organization**: Logical grouping of related products
- **SEO**: Better search engine optimization with structured content
- **Analytics**: Track which product types are popular

**Why would you care about it?** As a frontend developer, you'll use categories to:
- Build navigation menus and breadcrumbs
- Create category-specific product listings
- Implement filtering and search functionality
- Display category images and descriptions

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

**Note**: When a category is deleted (soft or hard), all products that belonged to that category are automatically moved to the "Uncategorized" category (ID 1). This ensures data integrity and prevents orphaned references.

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

**What is this?** Products are the core items in your online shop - the actual goods that customers can browse, view, and purchase.

**What is it for?** Products represent everything you sell, from fresh produce to packaged goods. Each product has details like name, price, description, and images. Stock levels are managed at the list-product relationship level, not at the product level.

**Why do you need it?** Products are what customers come to your shop for. They need to see what's available, compare prices, and make informed purchasing decisions. Stock availability is managed when products are added to specific lists.

**What's its purpose?** Products serve as the foundation of your e-commerce system:
- **Customer Discovery**: What items are available for purchase
- **Product Information**: Detailed descriptions, pricing, and images
- **Inventory Management**: Stock levels are managed at the list-product level
- **Order Processing**: What customers actually order and receive

**Why would you care about it?** As a frontend developer, you'll use products to:
- Build product catalogs and listings
- Create detailed product pages with images and descriptions
- Implement search and filtering functionality
- Display pricing and availability (stock is managed at list level)
- Handle product images and multiple image versions
- Manage product categories and units of measurement

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

**Response Example** (products filtered by category):
```json
[
  {
    "nume": "Test Product",
    "cantitate": 50,
    "pret": 25,
    "description": "Test description",
    "category_id": 1,
    "unitati_id": 1,
    "id": 9,
    "created_at": "2025-07-26T15:23:05.000000Z",
    "updated_at": "2025-07-26T15:23:05.000000Z",
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

**Common Use Cases**:
- **Get all products**: `GET /api/v1/products/`
- **Get products by category**: `GET /api/v1/products/?category_id=1`
- **Get products with pagination**: `GET /api/v1/products/?skip=0&limit=10`
- **Get products by category with pagination**: `GET /api/v1/products/?category_id=1&skip=0&limit=10`

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
  -F "unitati_id=1"
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
- `unitati_id` (integer): ID of the associated unit (must be > 0)

**Optional Fields**:
- `description` (string): Product description
- `category_id` (integer): ID of the associated category (must be >= 0, defaults to 1 "Uncategorized" if not provided)

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
# Response: 422 {"detail":[{"type":"missing","loc":["body","nume"],"msg":"Field required","input":null},{"type":"missing","loc":["body","cantitate"],"msg":"Field required","input":null},{"type":"missing","loc":["body","pret"],"msg":"Field required","input":null},{"type":"missing","loc":["body","unitati_id"],"msg":"Field required","input":null}]}
```

**400 Bad Request** (invalid foreign key):
```bash
curl -X POST "http://localhost:8001/api/v1/products/" \
  -H "accept: application/json" \
  -F "nume=Fresh Apples" \
  -F "cantitate=50" \
  -F "pret=25" \
  -F "category_id=999" \
  -F "unitati_id=1"
# Response: 400 {"detail":[{"loc":["body","category_id"],"msg":"Invalid category ID","type":"value_error.foreign_key"}]}
```

### Lista 

(de produse disponibile pentru urmatoarea comanda)

**What is this?** Lists are time-based product catalogs that represent what's available for the next order cycle. Think of them as "today's menu" or "this week's offerings."

**What is it for?** Lists allow you to curate specific products for specific time periods. Instead of showing all products all the time, you can create focused lists like "Monday's Fresh Produce" or "Weekend Specials."

**Why do you need it?** Small businesses often have limited inventory or want to promote specific items. Lists let you control what customers see and when, making inventory management easier and creating urgency.

**What's its purpose?** Lists serve multiple business purposes:
- **Inventory Control**: Only show products you actually have in stock
- **Promotional Focus**: Highlight specific items or categories
- **Time Management**: Set different offerings for different days/periods
- **Customer Experience**: Provide curated, relevant product selections

**Why would you care about it?** As a frontend developer, you'll use lists to:
- Display current available products to customers
- Show historical lists for reference
- Manage list creation and editing for admins
- Handle list publishing/unpublishing workflows
- Connect products with delivery types and schedules
- Display WhatsApp contact information for orders

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

#### 7. List Products Management

**Use Case**: Manage products associated with a specific list

**API**: `GET /api/v1/liste/{list_id}/products`

**Description**: Retrieves all products associated with a specific list, including their stock levels (`stoc_produs`) for that specific list

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/liste/19/products" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "id": 1,
    "nume": "Apple",
    "cantitate": 1,
    "pret": 500,
    "description": "Fresh apples",
    "category_id": 2,
    "unitati_id": 1,
    "stoc_produs": 50,
    "created_at": "2025-07-26T15:10:57",
    "updated_at": "2025-07-26T15:10:57",
    "is_deleted": false,
    "images": []
  }
]
```

**API**: `POST /api/v1/liste/{list_id}/products/{product_id}`

**Description**: Adds a product to a specific list with optional stock level (`stoc_produs`)

**cURL Example** (without stock):
```bash
curl -X POST "http://localhost:8001/api/v1/liste/19/products/1" \
  -H "accept: application/json"
```

**cURL Example** (with stock):
```bash
curl -X POST "http://localhost:8001/api/v1/liste/19/products/1" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"stoc_produs": 25}'
```

**Response Example**:
```json
{
  "message": "Product 1 added to list 19 successfully",
  "list_id": 19,
  "product_id": 1
}
```

**Request Body** (optional):
- `stoc_produs` (integer, optional): Available stock for this product in this list (must be >= 0)

**API**: `DELETE /api/v1/liste/{list_id}/products/{product_id}`

**Description**: Removes a product from a specific list

**cURL Example**:
```bash
curl -X DELETE "http://localhost:8001/api/v1/liste/19/products/1" \
  -H "accept: application/json"
```

**Response**: 204 No Content

**API**: `PUT /api/v1/liste/{list_id}/products`

**Description**: Replaces all products in a list with the provided product IDs

**cURL Example**:
```bash
curl -X PUT "http://localhost:8001/api/v1/liste/19/products" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3]'
```

**Response Example**:
```json
[
  {
    "id": 1,
    "nume": "Apple",
    "cantitate": 1,
    "pret": 500,
    "description": "Fresh apples",
    "category_id": 2,
    "unitati_id": 1,
    "stoc_produs": 50,
    "created_at": "2025-07-26T15:10:57",
    "updated_at": "2025-07-26T15:10:57",
    "is_deleted": false,
    "images": []
  },
  {
    "id": 2,
    "nume": "Banana",
    "cantitate": 1,
    "pret": 300,
    "description": "Fresh bananas",
    "category_id": 2,
    "unitati_id": 1,
    "stoc_produs": 30,
    "created_at": "2025-07-26T15:10:57",
    "updated_at": "2025-07-26T15:10:57",
    "is_deleted": false,
    "images": []
  },
  {
    "id": 3,
    "nume": "Milk",
    "cantitate": 1,
    "pret": 800,
    "description": "Fresh milk",
    "category_id": 4,
    "unitati_id": 4,
    "stoc_produs": 20,
    "created_at": "2025-07-26T15:10:57",
    "updated_at": "2025-07-26T15:10:57",
    "is_deleted": false,
    "images": []
  }
]
```

**Error Handling Examples**:

**404 Not Found** (list doesn't exist):
```bash
curl -X GET "http://localhost:8001/api/v1/liste/999/products"
# Response: 404 {"detail":"List with ID 999 not found"}
```

**404 Not Found** (product doesn't exist):
```bash
curl -X POST "http://localhost:8001/api/v1/liste/19/products/999"
# Response: 404 {"detail":"Product with ID 999 not found"}
```

**400 Bad Request** (product already in list):
```bash
curl -X POST "http://localhost:8001/api/v1/liste/19/products/1"
# Response: 400 {"detail":"Product 1 is already in list 19"}
```

**422 Validation Error** (negative stock):
```bash
curl -X POST "http://localhost:8001/api/v1/liste/19/products/1" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"stoc_produs": -5}'
# Response: 422 {"detail":[{"type":"greater_than_equal","loc":["body","stoc_produs"],"msg":"Input should be greater than or equal to 0","input":-5}]}
```

#### 8. List Delivery Types Management

**Use Case**: Manage delivery types associated with a specific list

**API**: `GET /api/v1/liste/{list_id}/delivery-types`

**Description**: Retrieves all delivery types associated with a specific list

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/liste/19/delivery-types" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "id": 2,
    "denumire": "Ridicare de la punct fix"
  },
  {
    "id": 3,
    "denumire": "Livrare la domiciliu"
  }
]
```

**API**: `POST /api/v1/liste/{list_id}/delivery-types/{delivery_type_id}`

**Description**: Adds a delivery type to a specific list

**cURL Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/liste/19/delivery-types/2" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "message": "Delivery type 2 added to list 19 successfully",
  "list_id": 19,
  "delivery_type_id": 2
}
```

**API**: `DELETE /api/v1/liste/{list_id}/delivery-types/{delivery_type_id}`

**Description**: Removes a delivery type from a specific list

**cURL Example**:
```bash
curl -X DELETE "http://localhost:8001/api/v1/liste/19/delivery-types/2" \
  -H "accept: application/json"
```

**Response**: 204 No Content

**API**: `PUT /api/v1/liste/{list_id}/delivery-types`

**Description**: Replaces all delivery types in a list with the provided delivery type IDs

**cURL Example**:
```bash
curl -X PUT "http://localhost:8001/api/v1/liste/19/delivery-types" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '[2, 3]'
```

**Response Example**:
```json
[
  {
    "id": 2,
    "denumire": "Ridicare de la punct fix"
  },
  {
    "id": 3,
    "denumire": "Livrare la domiciliu"
  }
]
```

**Error Handling Examples**:

**404 Not Found** (list doesn't exist):
```bash
curl -X GET "http://localhost:8001/api/v1/liste/999/delivery-types"
# Response: 404 {"detail":"List with ID 999 not found"}
```

**404 Not Found** (delivery type doesn't exist):
```bash
curl -X POST "http://localhost:8001/api/v1/liste/19/delivery-types/999"
# Response: 404 {"detail":"Delivery type with ID 999 not found"}
```

**400 Bad Request** (delivery type already in list):
```bash
curl -X POST "http://localhost:8001/api/v1/liste/19/delivery-types/2"
# Response: 400 {"detail":"Delivery type 2 is already in list 19"}
```

### Unitati

**What is this?** Units are the measurement standards for products - how quantities are expressed (pieces, kilograms, liters, etc.).

**What is it for?** Units provide consistency in how product quantities are displayed and ordered. They help customers understand exactly how much they're buying.

**Why do you need it?** Without units, customers wouldn't know if they're ordering 1 apple or 1 kilogram of apples. Units make product quantities clear and comparable.

**What's its purpose?** Units serve as the foundation for product measurement:
- **Clarity**: Customers know exactly what quantity they're ordering
- **Consistency**: Standardized measurement across all products
- **Comparison**: Easy to compare prices per unit (e.g., price per kg)
- **Order Accuracy**: Prevents confusion about quantities

**Why would you care about it?** As a frontend developer, you'll use units to:
- Display product quantities with proper units (e.g., "2 kg apples")
- Show unit prices for comparison shopping
- Build unit selection dropdowns in product forms
- Format quantity displays consistently across the app
- Handle unit conversions if needed

#### 1. Get All Units

**Use Case**: Display unit selection dropdown for product forms

**API**: `GET /api/v1/unitati/`

**Description**: Retrieves all available units for product measurements

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/unitati/" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "denumire": "buc",
    "id": 1
  },
  {
    "denumire": "g",
    "id": 2
  },
  {
    "denumire": "kg",
    "id": 3
  },
  {
    "denumire": "l",
    "id": 4
  },
  {
    "denumire": "ml",
    "id": 5
  },
  {
    "denumire": "portii",
    "id": 6
  }
]
```

**Common Use Cases**:
- **Get all units for dropdown**: `GET /api/v1/unitati/`
- **Display unit options in product forms**: Used when creating/editing products

#### 2. Get Specific Unit

**Use Case**: Display unit details or validate unit existence

**API**: `GET /api/v1/unitati/{unit_id}`

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/unitati/1" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "denumire": "buc",
  "id": 1
}
```

#### 3. Create New Unit

**Use Case**: Admin adding new measurement units

**API**: `POST /api/v1/unitati/`

**cURL Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/unitati/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "pachet"}'
```

**Response Example**:
```json
{
  "denumire": "pachet",
  "id": 15
}
```

**Required Fields**:
- `denumire` (string): Unit name/description (e.g., "kg", "l", "buc")

#### 4. Update Unit (Full Replacement)

**Use Case**: Admin completely replacing unit information

**API**: `PUT /api/v1/unitati/{unit_id}`

**Description**: Fully replaces a unit resource. The `denumire` field is required.

**cURL Example**:
```bash
curl -X PUT "http://localhost:8001/api/v1/unitati/15" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "pachet mare"}'
```

**Response Example**:
```json
{
  "denumire": "pachet mare",
  "id": 15
}
```

**Required Fields**:
- `denumire` (string): Unit name/description

#### 5. Partially Update Unit

**Use Case**: Admin updating specific unit fields

**API**: `PATCH /api/v1/unitati/{unit_id}`

**Description**: Partially updates a unit resource. Only updates fields explicitly provided.

**cURL Example**:
```bash
curl -X PATCH "http://localhost:8001/api/v1/unitati/15" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "pachet mic"}'
```

**Response Example**:
```json
{
  "denumire": "pachet mic",
  "id": 15
}
```

**Optional Fields** (all fields are optional for PATCH):
- `denumire` (string): Unit name/description

#### 6. Delete Unit

**Use Case**: Admin removing units (hard delete)

**API**: `DELETE /api/v1/unitati/{unit_id}`

**Note**: Units are hard deleted (not soft deleted). Ensure no products are using the unit before deletion.

**cURL Example**:
```bash
curl -X DELETE "http://localhost:8001/api/v1/unitati/15" \
  -H "accept: application/json"
```

**Response**: HTTP 204 No Content (successful deletion)

#### Error Handling Examples

**404 Not Found**:
```bash
curl -X GET "http://localhost:8001/api/v1/unitati/999"
# Response: 404 {"detail":"Unit not found"}
```

**422 Validation Error** (missing required field):
```bash
curl -X POST "http://localhost:8001/api/v1/unitati/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{}'
# Response: 422 {"detail":[{"type":"missing","loc":["body","denumire"],"msg":"Field required","input":{}}]}
```

**409 Conflict** (duplicate unit name):
```bash
curl -X POST "http://localhost:8001/api/v1/unitati/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "kg"}'
# Response: 409 {"detail":"A unit with the name 'kg' already exists"}
```

### Tipuri Livrare

**What is this?** Delivery Types define how customers can receive their orders - home delivery, pickup from store, pickup from fixed point, etc.

**What is it for?** Delivery Types give customers options for receiving their orders and help businesses manage different delivery methods with different costs and timeframes.

**Why do you need it?** Different customers have different preferences and needs. Some want home delivery, others prefer pickup. Delivery types let you offer flexibility and charge appropriately.

**What's its purpose?** Delivery Types serve multiple business purposes:
- **Customer Choice**: Offer different delivery options to suit customer preferences
- **Pricing Flexibility**: Different delivery methods can have different costs
- **Operational Planning**: Help organize delivery routes and pickup schedules
- **Customer Experience**: Clear communication about delivery options

**Why would you care about it?** As a frontend developer, you'll use delivery types to:
- Display delivery options in order forms
- Show delivery costs and timeframes
- Build delivery type selection dropdowns
- Connect delivery types to specific lists
- Handle delivery-specific validation and messaging

#### 1. Get All Delivery Types

**Use Case**: Display delivery type selection dropdown for lists and orders

**API**: `GET /api/v1/tipuri-livrare/`

**Description**: Retrieves all available delivery types with pagination support

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/tipuri-livrare/" \
  -H "accept: application/json"
```

**cURL Example** (with pagination):
```bash
curl -X GET "http://localhost:8001/api/v1/tipuri-livrare/?skip=0&limit=10" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "denumire": "Livrare la domiciliu",
    "id": 3
  },
  {
    "denumire": "Ridicare de la punct fix",
    "id": 2
  },
  {
    "denumire": "Ridicare de la sediu",
    "id": 1
  }
]
```

**Parameters**:
- `skip` (integer, optional): Number of delivery types to skip for pagination (default: 0)
- `limit` (integer, optional): Maximum number of delivery types to return (default: 100, max: 100)

**Common Use Cases**:
- **Get all delivery types for dropdown**: `GET /api/v1/tipuri-livrare/`
- **Display delivery options in list forms**: Used when creating/editing lists
- **Filter delivery types with pagination**: `GET /api/v1/tipuri-livrare/?skip=0&limit=10`

#### 2. Get Specific Delivery Type

**Use Case**: Display delivery type details or validate delivery type existence

**API**: `GET /api/v1/tipuri-livrare/{delivery_type_id}`

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/tipuri-livrare/1" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "denumire": "Ridicare de la sediu",
  "id": 1
}
```

#### 3. Create New Delivery Type

**Use Case**: Admin adding new delivery options

**API**: `POST /api/v1/tipuri-livrare/`

**cURL Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/tipuri-livrare/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "Livrare express"}'
```

**Response Example**:
```json
{
  "denumire": "Livrare express",
  "id": 15
}
```

**Required Fields**:
- `denumire` (string): Delivery type name/description (e.g., "Livrare la domiciliu", "Ridicare de la sediu")

#### 4. Update Delivery Type (Full Replacement)

**Use Case**: Admin completely replacing delivery type information

**API**: `PUT /api/v1/tipuri-livrare/{delivery_type_id}`

**Description**: Fully replaces a delivery type resource. The `denumire` field is required.

**cURL Example**:
```bash
curl -X PUT "http://localhost:8001/api/v1/tipuri-livrare/15" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "Livrare rapida"}'
```

**Response Example**:
```json
{
  "denumire": "Livrare rapida",
  "id": 15
}
```

**Required Fields**:
- `denumire` (string): Delivery type name/description

#### 5. Partially Update Delivery Type

**Use Case**: Admin updating specific delivery type fields

**API**: `PATCH /api/v1/tipuri-livrare/{delivery_type_id}`

**Description**: Partially updates a delivery type resource. Only updates fields explicitly provided.

**cURL Example**:
```bash
curl -X PATCH "http://localhost:8001/api/v1/tipuri-livrare/15" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "Livrare super rapida"}'
```

**Response Example**:
```json
{
  "denumire": "Livrare super rapida",
  "id": 15
}
```

**Optional Fields** (all fields are optional for PATCH):
- `denumire` (string): Delivery type name/description

#### 6. Delete Delivery Type

**Use Case**: Admin removing delivery types (hard delete)

**API**: `DELETE /api/v1/tipuri-livrare/{delivery_type_id}`

**Note**: Delivery types are hard deleted (not soft deleted). Ensure no lists or orders are using the delivery type before deletion.

**cURL Example**:
```bash
curl -X DELETE "http://localhost:8001/api/v1/tipuri-livrare/15" \
  -H "accept: application/json"
```

**Response**: HTTP 204 No Content (successful deletion)

#### Error Handling Examples

**404 Not Found**:
```bash
curl -X GET "http://localhost:8001/api/v1/tipuri-livrare/999"
# Response: 404 {"detail":"Delivery type with ID 999 not found"}
```

**422 Validation Error** (missing required field):
```bash
curl -X POST "http://localhost:8001/api/v1/tipuri-livrare/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{}'
# Response: 422 {"detail":[{"type":"missing","loc":["body","denumire"],"msg":"Field required","input":{}}]}
```

**400 Bad Request** (duplicate delivery type name):
```bash
curl -X POST "http://localhost:8001/api/v1/tipuri-livrare/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "Ridicare de la sediu"}'
# Response: 400 {"detail":"A delivery type with the name 'Ridicare de la sediu' already exists"}
```

### Modalitati Plata

**What is this?** Payment Methods define how customers can pay for their orders - cash on delivery, bank transfer, card payment, etc.

**What is it for?** Payment Methods give customers flexibility in how they pay and help businesses manage different payment processes and cash flow.

**Why do you need it?** Different customers prefer different payment methods. Some want to pay cash on delivery, others prefer online payments. Payment methods let you accommodate these preferences.

**What's its purpose?** Payment Methods serve multiple business purposes:
- **Customer Convenience**: Offer payment options that suit customer preferences
- **Cash Flow Management**: Different payment methods affect when you receive money
- **Risk Management**: Some payment methods have different fraud risks
- **Operational Efficiency**: Streamline payment processing workflows

**Why would you care about it?** As a frontend developer, you'll use payment methods to:
- Display payment options in order forms
- Show payment-specific instructions and requirements
- Build payment method selection dropdowns
- Handle payment validation and confirmation
- Connect payment methods to specific lists or orders

#### 1. Get All Payment Methods

**Use Case**: Display payment method selection dropdown for lists and orders

**API**: `GET /api/v1/modalitati-plata/`

**Description**: Retrieves all available payment methods with pagination support

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/modalitati-plata/" \
  -H "accept: application/json"
```

**cURL Example** (with pagination):
```bash
curl -X GET "http://localhost:8001/api/v1/modalitati-plata/?skip=0&limit=2" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "denumire": "Card",
    "id": 6
  },
  {
    "denumire": "Cash",
    "id": 5
  },
  {
    "denumire": "Transfer Bancar",
    "id": 7
  },
  {
    "denumire": "Transfer Revolut",
    "id": 8
  }
]
```

**Parameters**:
- `skip` (integer, optional): Number of payment methods to skip for pagination (default: 0)
- `limit` (integer, optional): Maximum number of payment methods to return (default: 100, max: 100)

**Common Use Cases**:
- **Get all payment methods for dropdown**: `GET /api/v1/modalitati-plata/`
- **Display payment options in list forms**: Used when creating/editing lists
- **Filter payment methods with pagination**: `GET /api/v1/modalitati-plata/?skip=0&limit=2`

#### 2. Get Specific Payment Method

**Use Case**: Display payment method details or validate payment method existence

**API**: `GET /api/v1/modalitati-plata/{payment_method_id}`

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/modalitati-plata/5" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "denumire": "Cash",
  "id": 5
}
```

#### 3. Create New Payment Method

**Use Case**: Admin adding new payment options

**API**: `POST /api/v1/modalitati-plata/`

**cURL Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/modalitati-plata/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "PayPal"}'
```

**Response Example**:
```json
{
  "denumire": "PayPal",
  "id": 20
}
```

**Required Fields**:
- `denumire` (string): Payment method name/description (e.g., "Cash", "Card", "Transfer Bancar")

#### 4. Update Payment Method (Full Replacement)

**Use Case**: Admin completely replacing payment method information

**API**: `PUT /api/v1/modalitati-plata/{payment_method_id}`

**Description**: Fully replaces a payment method resource. The `denumire` field is required.

**cURL Example**:
```bash
curl -X PUT "http://localhost:8001/api/v1/modalitati-plata/20" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "PayPal Express"}'
```

**Response Example**:
```json
{
  "denumire": "PayPal Express",
  "id": 20
}
```

**Required Fields**:
- `denumire` (string): Payment method name/description

#### 5. Partially Update Payment Method

**Use Case**: Admin updating specific payment method fields

**API**: `PATCH /api/v1/modalitati-plata/{payment_method_id}`

**Description**: Partially updates a payment method resource. Only updates fields explicitly provided.

**cURL Example**:
```bash
curl -X PATCH "http://localhost:8001/api/v1/modalitati-plata/20" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "PayPal Standard"}'
```

**Response Example**:
```json
{
  "denumire": "PayPal Standard",
  "id": 20
}
```

**Optional Fields** (all fields are optional for PATCH):
- `denumire` (string): Payment method name/description

#### 6. Delete Payment Method

**Use Case**: Admin removing payment methods (hard delete)

**API**: `DELETE /api/v1/modalitati-plata/{payment_method_id}`

**Note**: Payment methods are hard deleted (not soft deleted). Ensure no lists or orders are using the payment method before deletion.

**cURL Example**:
```bash
curl -X DELETE "http://localhost:8001/api/v1/modalitati-plata/20" \
  -H "accept: application/json"
```

**Response**: HTTP 204 No Content (successful deletion)

#### Error Handling Examples

**404 Not Found**:
```bash
curl -X GET "http://localhost:8001/api/v1/modalitati-plata/999"
# Response: 404 {"detail":"Payment method not found"}
```

**422 Validation Error** (missing required field):
```bash
curl -X POST "http://localhost:8001/api/v1/modalitati-plata/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{}'
# Response: 422 {"detail":[{"type":"missing","loc":["body","denumire"],"msg":"Field required","input":{}}]}
```

**400 Bad Request** (duplicate payment method name):
```bash
curl -X POST "http://localhost:8001/api/v1/modalitati-plata/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"denumire": "Cash"}'
# Response: 400 {"detail":"A payment method with the name 'Cash' already exists"}
```

### Orare Livrari

**What is this?** Delivery Schedules define when deliveries and pickups are available - specific days, times, and time slots for order fulfillment.

**What is it for?** Delivery Schedules help businesses manage their delivery capacity and let customers know when they can expect their orders to be delivered or available for pickup.

**Why do you need it?** Businesses can't deliver 24/7. Delivery schedules set realistic expectations and help organize delivery operations efficiently.

**What's its purpose?** Delivery Schedules serve multiple business purposes:
- **Customer Expectations**: Clear communication about when orders will be ready
- **Operational Planning**: Organize delivery routes and pickup schedules
- **Capacity Management**: Control how many orders you can handle
- **Service Quality**: Ensure reliable delivery timeframes

**Why would you care about it?** As a frontend developer, you'll use delivery schedules to:
- Display available delivery/pickup times to customers
- Show delivery schedule options in order forms
- Build schedule selection dropdowns
- Handle time slot availability and booking
- Connect schedules to specific lists or delivery types

#### 1. Get All Delivery Schedules

**Use Case**: Display delivery schedule selection dropdown for lists

**API**: `GET /api/v1/orare-livrari/`

**Description**: Retrieves all available delivery schedules with pagination support

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/orare-livrari/" \
  -H "accept: application/json"
```

**cURL Example** (with pagination):
```bash
curl -X GET "http://localhost:8001/api/v1/orare-livrari/?skip=0&limit=3" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "orar_livrari": "Luni-Vineri 9:00-18:00",
    "id": 8
  },
  {
    "orar_livrari": "Marti si Vineri 9:00-18:00",
    "id": 9
  },
  {
    "orar_livrari": "Weekend 10:00-14:00",
    "id": 10
  }
]
```

**Parameters**:
- `skip` (integer, optional): Number of delivery schedules to skip for pagination (default: 0)
- `limit` (integer, optional): Maximum number of delivery schedules to return (default: 100, max: 100)

**Common Use Cases**:
- **Get all delivery schedules for dropdown**: `GET /api/v1/orare-livrari/`
- **Display delivery schedule options in list forms**: Used when creating/editing lists
- **Filter delivery schedules with pagination**: `GET /api/v1/orare-livrari/?skip=0&limit=3`

#### 2. Get Specific Delivery Schedule

**Use Case**: Display delivery schedule details or validate delivery schedule existence

**API**: `GET /api/v1/orare-livrari/{delivery_schedule_id}`

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/orare-livrari/8" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "orar_livrari": "Luni-Vineri 9:00-18:00",
  "id": 8
}
```

#### 3. Create New Delivery Schedule

**Use Case**: Admin adding new delivery schedule options

**API**: `POST /api/v1/orare-livrari/`

**cURL Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/orare-livrari/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"orar_livrari": "Luni-Vineri 9:00-18:00"}'
```

**Response Example**:
```json
{
  "orar_livrari": "Luni-Vineri 9:00-18:00",
  "id": 22
}
```

**Required Fields**:
- `orar_livrari` (string): Delivery schedule description (e.g., "Luni-Vineri 9:00-18:00", "Weekend 10:00-16:00")

#### 4. Update Delivery Schedule (Full Replacement)

**Use Case**: Admin completely replacing delivery schedule information

**API**: `PUT /api/v1/orare-livrari/{delivery_schedule_id}`

**Description**: Fully replaces a delivery schedule resource. The `orar_livrari` field is required.

**cURL Example**:
```bash
curl -X PUT "http://localhost:8001/api/v1/orare-livrari/22" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"orar_livrari": "Luni-Vineri 8:00-17:00"}'
```

**Response Example**:
```json
{
  "orar_livrari": "Luni-Vineri 8:00-17:00",
  "id": 22
}
```

**Required Fields**:
- `orar_livrari` (string): Delivery schedule description

#### 5. Partially Update Delivery Schedule

**Use Case**: Admin updating specific delivery schedule fields

**API**: `PATCH /api/v1/orare-livrari/{delivery_schedule_id}`

**Description**: Partially updates a delivery schedule resource. Only updates fields explicitly provided.

**cURL Example**:
```bash
curl -X PATCH "http://localhost:8001/api/v1/orare-livrari/22" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"orar_livrari": "Luni-Vineri 10:00-19:00"}'
```

**Response Example**:
```json
{
  "orar_livrari": "Luni-Vineri 10:00-19:00",
  "id": 22
}
```

**Optional Fields** (all fields are optional for PATCH):
- `orar_livrari` (string): Delivery schedule description

#### 6. Delete Delivery Schedule

**Use Case**: Admin removing delivery schedules (hard delete)

**API**: `DELETE /api/v1/orare-livrari/{delivery_schedule_id}`

**Note**: Delivery schedules are hard deleted (not soft deleted). Ensure no lists are using the delivery schedule before deletion.

**cURL Example**:
```bash
curl -X DELETE "http://localhost:8001/api/v1/orare-livrari/22" \
  -H "accept: application/json"
```

**Response**: HTTP 204 No Content (successful deletion)

#### Error Handling Examples

**404 Not Found**:
```bash
curl -X GET "http://localhost:8001/api/v1/orare-livrari/999"
# Response: 404 {"detail":"Delivery schedule with ID 999 not found"}
```

**422 Validation Error** (missing required field):
```bash
curl -X POST "http://localhost:8001/api/v1/orare-livrari/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{}'
# Response: 422 {"detail":[{"type":"missing","loc":["body","orar_livrari"],"msg":"Field required","input":{}}]}
```

### Detalii Business

**What is this?** Business Details contain the essential information about your shop - address, phone number, logo, motto, and other business-specific information.

**What is it for?** Business Details provide customers with the information they need to contact you, understand your business, and build trust in your brand.

**Why do you need it?** Customers need to know who they're buying from. Business details help establish credibility and provide essential contact information for orders and support.

**What's its purpose?** Business Details serve multiple business purposes:
- **Brand Identity**: Logo, motto, and business information build brand recognition
- **Customer Contact**: Phone number and address for orders and support
- **Trust Building**: Professional presentation and clear business information
- **Operational Communication**: Messages about availability, delivery delays, etc.

**Why would you care about it?** As a frontend developer, you'll use business details to:
- Display business information on the website/app
- Show contact information for customer support
- Display business logo and branding elements
- Show business messages and announcements
- Handle business-specific content and styling

#### 1. Get All Business Details

**Use Case**: Display business information or manage business settings

**API**: `GET /api/v1/detalii-business/`

**Description**: Retrieves all business details entries with pagination support

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/detalii-business/" \
  -H "accept: application/json"
```

**cURL Example** (with pagination):
```bash
curl -X GET "http://localhost:8001/api/v1/detalii-business/?skip=0&limit=2" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "adresa": "Strada Test 123",
    "telefon": "+40712345678",
    "logo_path": null,
    "motto": null,
    "list_not_available_msg": null,
    "alte_detalii": null,
    "id": 10
  }
]
```

**Parameters**:
- `skip` (integer, optional): Number of business details to skip for pagination (default: 0)
- `limit` (integer, optional): Maximum number of business details to return (default: 100, max: 100)

**Common Use Cases**:
- **Get all business details**: `GET /api/v1/detalii-business/`
- **Display business information**: Used for contact details, about page
- **Filter business details with pagination**: `GET /api/v1/detalii-business/?skip=0&limit=2`

#### 2. Get Specific Business Details

**Use Case**: Display specific business details entry or validate existence

**API**: `GET /api/v1/detalii-business/{business_details_id}`

**cURL Example**:
```bash
curl -X GET "http://localhost:8001/api/v1/detalii-business/10" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "adresa": "Strada Test 123",
  "telefon": "+40712345678",
  "logo_path": null,
  "motto": null,
  "list_not_available_msg": null,
  "alte_detalii": null,
  "id": 10
}
```

#### 3. Create New Business Details

**Use Case**: Admin adding new business information

**API**: `POST /api/v1/detalii-business/`

**cURL Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/detalii-business/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "adresa": "Strada Test 123",
    "telefon": "+40712345678",
    "motto": "Calitate si pret bun",
    "alte_detalii": "Livrare gratuita pentru comenzi peste 100 lei"
  }'
```

**Response Example**:
```json
{
  "adresa": "Strada Test 123",
  "telefon": "+40712345678",
  "logo_path": null,
  "motto": "Calitate si pret bun",
  "alte_detalii": "Livrare gratuita pentru comenzi peste 100 lei",
  "id": 10
}
```

**Optional Fields** (all fields are optional):
- `adresa` (string): Business address
- `telefon` (string): Business phone number
- `logo_path` (string): Path to business logo image
- `motto` (string): Business motto or tagline
- `list_not_available_msg` (string): Message to display when lists are not available
- `alte_detalii` (string): Additional business details

#### 4. Update Business Details (Full Replacement)

**Use Case**: Admin completely replacing business information

**API**: `PUT /api/v1/detalii-business/{business_details_id}`

**Description**: Fully replaces a business details resource. All fields are optional for PUT operations.

**cURL Example**:
```bash
curl -X PUT "http://localhost:8001/api/v1/detalii-business/10" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "adresa": "Strada Noua 456",
    "telefon": "+40787654321",
    "motto": "Calitate si pret bun"
  }'
```

**Response Example**:
```json
{
  "adresa": "Strada Noua 456",
  "telefon": "+40787654321",
  "logo_path": null,
  "motto": "Calitate si pret bun",
  "list_not_available_msg": null,
  "alte_detalii": null,
  "id": 10
}
```

**Optional Fields** (all fields are optional for PUT):
- `adresa` (string): Business address
- `telefon` (string): Business phone number
- `logo_path` (string): Path to business logo image
- `motto` (string): Business motto or tagline
- `list_not_available_msg` (string): Message to display when lists are not available
- `alte_detalii` (string): Additional business details

#### 5. Partially Update Business Details

**Use Case**: Admin updating specific business fields

**API**: `PATCH /api/v1/detalii-business/{business_details_id}`

**Description**: Partially updates a business details resource. Only updates fields explicitly provided.

**cURL Example**:
```bash
curl -X PATCH "http://localhost:8001/api/v1/detalii-business/10" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"alte_detalii": "Livrare gratuita pentru comenzi peste 100 lei"}'
```

**Response Example**:
```json
{
  "adresa": "Strada Noua 456",
  "telefon": "+40787654321",
  "logo_path": null,
  "motto": "Calitate si pret bun",
  "list_not_available_msg": null,
  "alte_detalii": "Livrare gratuita pentru comenzi peste 100 lei",
  "id": 10
}
```

**Optional Fields** (all fields are optional for PATCH):
- `adresa` (string): Business address
- `telefon` (string): Business phone number
- `logo_path` (string): Path to business logo image
- `motto` (string): Business motto or tagline
- `list_not_available_msg` (string): Message to display when lists are not available
- `alte_detalii` (string): Additional business details

#### 6. Delete Business Details

**Use Case**: Admin removing business details entries (hard delete)

**API**: `DELETE /api/v1/detalii-business/{business_details_id}`

**Note**: Business details are hard deleted (not soft deleted).

**cURL Example**:
```bash
curl -X DELETE "http://localhost:8001/api/v1/detalii-business/10" \
  -H "accept: application/json"
```

**Response**: HTTP 204 No Content (successful deletion)

#### Error Handling Examples

**404 Not Found**:
```bash
curl -X GET "http://localhost:8001/api/v1/detalii-business/999"
# Response: 404 {"detail":"Business details with ID 999 not found"}
```

**Empty Business Details Creation**:
```bash
curl -X POST "http://localhost:8001/api/v1/detalii-business/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{}'
# Response: 200 (creates business details with all null fields)
```

### Product Overrides

**What is this?** Product Overrides allow you to temporarily modify product information like prices, descriptions, or availability without changing the original product data.

**What is it for?** Product Overrides are perfect for sales, promotions, or temporary changes. They let you highlight special offers or update product information for specific periods.

**Why do you need it?** Sometimes you need to change product information temporarily - like lowering prices for a sale or adding promotional messages to descriptions. Overrides let you do this without permanently changing the original product data.

**What's its purpose?** Product Overrides serve multiple business purposes:
- **Sales & Promotions**: Temporarily lower prices for special offers
- **Marketing**: Highlight specific products or features
- **Flexibility**: Make temporary changes without affecting original data

**Why would you care about it?** As a frontend developer, you'll use product overrides to:
- Display sale prices alongside original prices
- Handle temporary product modifications
- Display override information to customers
- Manage active/inactive override states

#### 1. Get All Product Overrides

**Use Case**: Admin viewing all product overrides

**API**: `GET /api/v1/product-overrides`

**Description**: Retrieves all product overrides with optional filtering by product_id and active status

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/product-overrides" \
  -H "accept: application/json"
```

**cURL Example** (filter by product):
```bash
curl -X GET "http://localhost:8000/api/v1/product-overrides?product_id=1" \
  -H "accept: application/json"
```

**cURL Example** (filter by active status):
```bash
curl -X GET "http://localhost:8000/api/v1/product-overrides?is_active=true" \
  -H "accept: application/json"
```

**Response Example**:
```json
[
  {
    "id": 1,
    "produse_id": 1,
    "field_name": "price",
    "old_value": "100",
    "new_value": "80",
    "notes": "Sale price",
    "is_active": true,
    "created_at": "2025-07-27T14:05:37",
    "updated_at": "2025-07-27T14:05:37"
  }
]
```

#### 2. Get Available Override Fields

**Use Case**: Frontend needs to know which fields can be overridden

**API**: `GET /api/v1/product-overrides/fields`

**Description**: Returns list of available fields that can be overridden

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/product-overrides/fields" \
  -H "accept: application/json"
```

**Response Example**:
```json
["price", "description", "availability"]
```

#### 3. Get Specific Product Override

**Use Case**: Admin viewing details of a specific override

**API**: `GET /api/v1/product-overrides/{override_id}`

**Description**: Retrieves a specific product override by ID

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/product-overrides/1" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "id": 1,
  "produse_id": 1,
  "field_name": "price",
  "old_value": "100",
  "new_value": "80",
  "notes": "Sale price",
  "is_active": true,
  "created_at": "2025-07-27T14:05:37",
  "updated_at": "2025-07-27T14:05:37"
}
```

#### 4. Create Product Override

**Use Case**: Admin creating a temporary override for a product

**API**: `POST /api/v1/product-overrides`

**Description**: Creates a new product override. Only one active override per product and field is allowed.

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/product-overrides" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "produse_id": 1,
    "field_name": "price",
    "old_value": "100",
    "new_value": "80",
    "notes": "Sale price",
    "is_active": true
  }'
```

**Response Example**:
```json
{
  "id": 1,
  "produse_id": 1,
  "field_name": "price",
  "old_value": "100",
  "new_value": "80",
  "notes": "Sale price",
  "is_active": true,
  "created_at": "2025-07-27T14:05:37",
  "updated_at": "2025-07-27T14:05:37"
}
```

**Required Fields**:
- `produse_id` (integer): ID of the product to override
- `field_name` (string): Field to override ("price", "description", "availability")
- `new_value` (string): New override value

**Optional Fields**:
- `old_value` (string): Original value for reference
- `notes` (string): Optional notes about the override
- `is_active` (boolean): Whether override is active (default: true)

#### 5. Update Product Override

**Use Case**: Admin modifying an existing override

**API**: `PUT /api/v1/product-overrides/{override_id}`

**Description**: Updates a product override. Only provided fields are updated.

**cURL Example**:
```bash
curl -X PUT "http://localhost:8000/api/v1/product-overrides/1" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "new_value": "75",
    "notes": "Updated sale price"
  }'
```

**Response Example**:
```json
{
  "id": 1,
  "produse_id": 1,
  "field_name": "price",
  "old_value": "100",
  "new_value": "75",
  "notes": "Updated sale price",
  "is_active": true,
  "created_at": "2025-07-27T14:05:37",
  "updated_at": "2025-07-27T14:06:08"
}
```

**Optional Fields** (all fields are optional for PUT):
- `new_value` (string): New override value
- `notes` (string): Optional notes about the override
- `is_active` (boolean): Whether override is active

#### 6. Delete Product Override

**Use Case**: Admin removing an override

**API**: `DELETE /api/v1/product-overrides/{override_id}`

**Description**: Permanently deletes a product override

**cURL Example**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/product-overrides/1" \
  -H "accept: application/json"
```

**Response**: HTTP 204 No Content (successful deletion)

#### 7. Get Product with Overrides

**Use Case**: Frontend displaying product with active overrides applied

**API**: `GET /api/v1/product-overrides/product/{product_id}/with-overrides`

**Description**: Returns product data with active overrides applied

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/product-overrides/product/1/with-overrides" \
  -H "accept: application/json"
```

**Response Example**:
```json
{
  "id": 1,
  "nume": "Test Product",
  "cantitate": 10,
  "pret": 100,
  "description": "Original description",
  "category_id": 1,
  "unitati_id": 1,
  "overrides": {
    "price": "80",
    "description": "Only 5 left!"
  }
}
```

#### Error Handling Examples

**404 Not Found**:
```bash
curl -X GET "http://localhost:8000/api/v1/product-overrides/999"
# Response: 404 {"detail":"Product override with ID 999 not found"}
```

**Duplicate Active Override**:
```bash
curl -X POST "http://localhost:8000/api/v1/product-overrides" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "produse_id": 1,
    "field_name": "price",
    "new_value": "90",
    "is_active": true
  }'
# Response: 400 {"detail":"Active override already exists for this product and field"}
```

**Invalid Field Name**:
```bash
curl -X POST "http://localhost:8000/api/v1/product-overrides" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "produse_id": 1,
    "field_name": "invalid_field",
    "new_value": "80"
  }'
# Response: 422 Validation error
```

### Comenzi

**Note**: Stock management has been refactored to work at the list-product relationship level. Products no longer have a direct `stock` field. Instead, stock levels (`stoc_produs`) are managed when products are added to specific lists. This allows for more flexible inventory management where the same product can have different stock levels in different lists.

### Stock Management (New Architecture)

**What is this?** Stock management has been moved from the product level to the list-product relationship level. This means stock levels are managed per list, not per product.

**What is it for?** This new approach allows the same product to have different stock levels in different lists. For example, "Fresh Apples" can have 50 units available in "Monday's List" but only 20 units in "Wednesday's List".

**Why do you need it?** This provides more flexible inventory management for small businesses that may have limited stock for specific time periods or want to control availability per list.

**How does it work?** 
- Products are created without stock information
- When adding a product to a list, you can specify `stoc_produs` (stock for this product in this list)
- Stock levels are managed at the list-product relationship level
- The same product can have different stock levels in different lists

**API Usage Examples**:

**Adding a product to a list without stock**:
```bash
curl -X POST "http://localhost:8001/api/v1/liste/19/products/1" \
  -H "accept: application/json"
```

**Adding a product to a list with stock**:
```bash
curl -X POST "http://localhost:8001/api/v1/liste/19/products/1" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"stoc_produs": 25}'
```

**Getting products from a list (includes stock)**:
```bash
curl -X GET "http://localhost:8001/api/v1/liste/19/products" \
  -H "accept: application/json"
```

**Response includes stock per product**:
```json
[
  {
    "id": 1,
    "nume": "Apple",
    "cantitate": 1,
    "pret": 500,
    "description": "Fresh apples",
    "category_id": 2,
    "unitati_id": 1,
    "stoc_produs": 25,
    "created_at": "2025-07-26T15:10:57",
    "updated_at": "2025-07-26T15:10:57",
    "is_deleted": false,
    "images": []
  }
]
```

### Payment Methods & Business Details Architecture

**What is this?** The system has a simplified architecture for handling payment methods and business information. Payment methods are globally available, while business details contain contact information.

**What is it for?** This architecture supports single-business setups where all payment methods are available to all customers, and business contact information is consistent across all lists.

**Why do you need it?** When customers view a published list, they need to know:
- What products are available (from the list)
- How to contact the business (from business details)
- What payment methods are accepted (from payment methods API)
- What delivery options are available (from list-delivery-types)

**How does it work?** 
- **Payment Methods**: Globally available via `/api/v1/modalitati-plata`
- **Business Details**: Contains contact info (address, phone, WhatsApp, etc.)
- **Lists**: Contain products, delivery types, and business contact info
- **No Direct Links**: Payment methods are not linked to specific lists or business details

**Architecture Benefits:**
- **Simplicity**: Payment methods are consistent across all lists
- **Flexibility**: Easy to add/remove payment methods globally
- **Single Source of Truth**: Business contact info in one place
- **Future-Proof**: Can add business-specific filtering later if needed

**Frontend Implementation:**
When displaying a published list, combine data from multiple endpoints:

1. **Get List Details**: `/api/v1/liste/{list_id}`
2. **Get List Products**: `/api/v1/liste/{list_id}/products`
3. **Get Business Details**: `/api/v1/detalii-business`
4. **Get Payment Methods**: `/api/v1/modalitati-plata` (see Modalitati Plata section for detailed API)
5. **Get Delivery Types**: `/api/v1/liste/{list_id}/delivery-types`

**Example Customer View:**
```json
{
  "list": {
    "id": 19,
    "data": "2025-07-26",
    "mesaj_introducere": "Fresh produce available today!",
    "numar_whatsapp": "+40712345678"
  },
  "products": [
    {
      "id": 1,
      "nume": "Fresh Apples",
      "pret": 25,
      "stoc_produs": 50
    }
  ],
  "business_details": {
    "adresa": "123 Main Street",
    "telefon": "+40712345678",
    "motto": "Fresh from our farm"
  },
  "payment_methods": [
    {"id": 1, "denumire": "Cash"},
    {"id": 2, "denumire": "Card"},
    {"id": 3, "denumire": "Transfer Bancar"}
  ],
  "delivery_types": [
    {"id": 1, "denumire": "Ridicare de la sediu"},
    {"id": 3, "denumire": "Livrare la domiciliu"}
  ]
}
```

**Note**: For detailed payment methods API documentation, see the "Modalitati Plata" section above.