# Frontend Guide: Category Ordering

## Overview

Categories now support **manual ordering** through an `order_index` field. This allows admins to control the display order of categories in the frontend, ensuring important categories appear first or categories are organized in a logical sequence.

## Key Concepts

### Order Index
- **Range**: 1-127 (TINYINT)
- **Uniqueness**: Each category must have a unique `order_index` value
- **Display Order**: Categories are automatically sorted by `order_index` (ascending), then by `name` (ascending) as a tiebreaker
- **Required Field**: `order_index` is required when creating categories

### Automatic Ordering
When fetching categories via `GET /api/v1/categories/`, the response is automatically ordered by:
1. `order_index` (ascending)
2. `name` (ascending) - used as tiebreaker

## API Changes

### Breaking Changes

**Category Creation (POST)**
- `order_index` is now **required** when creating categories
- Must be an integer between 1 and 127
- Must be unique (cannot conflict with existing categories)

**Category Updates (PUT/PATCH)**
- `PUT /categories/{id}`: `order_index` is now **required** (full replacement)
- `PATCH /categories/{id}`: `order_index` is **optional** (partial update)
- When updating `order_index`, it must be unique and within range 1-127

**Category Response**
- All category responses now include `order_index` field
- Categories are automatically returned in order_index order

### New Endpoint

#### Reorder Categories
```http
PUT /api/v1/categories/reorder
```

**Description**: Atomically reorders all categories by providing the complete ordered list of category IDs.

**Authentication**: Required (Admin only)

**Request Body**:
```json
[3, 1, 2, 5, 4]
```

**Response**: Returns the complete list of categories in the new order:
```json
[
  {
    "id": 3,
    "name": "Electronics",
    "order_index": 1,
    "image_path": "categories/...",
    "created_at": "2024-01-15T10:30:00.000000Z",
    "updated_at": "2024-01-15T10:30:00.000000Z"
  },
  {
    "id": 1,
    "name": "Fruits",
    "order_index": 2,
    ...
  },
  ...
]
```

**Validation Rules**:
- Must include **all** category IDs (complete permutation of all categories)
- Cannot include duplicates
- Cannot include non-existent category IDs
- All IDs must exist in the database

**Error Responses**:
- `422`: Invalid permutation (missing IDs, duplicates, or wrong count)
- `404`: One or more category IDs not found
- `401`: Unauthorized (admin authentication required)

## Updated Endpoints

### 1. Get All Categories

**API**: `GET /api/v1/categories/`

**Response** (now includes `order_index` and is automatically ordered):
```json
[
  {
    "id": 1,
    "name": "Fruits",
    "order_index": 1,
    "image_path": "categories/...",
    "image_versions": {...},
    "created_at": "2024-01-15T10:30:00.000000Z",
    "updated_at": "2024-01-15T10:30:00.000000Z"
  },
  {
    "id": 2,
    "name": "Vegetables",
    "order_index": 2,
    ...
  }
]
```

**Note**: Categories are automatically returned in `order_index` order (ascending), then by `name` (ascending).

### 2. Create Category

**API**: `POST /api/v1/categories/`

**Breaking Change**: `order_index` is now **required** in the request.

**Request** (multipart/form-data):
```
name: Fruits
order_index: 1
primary_image: [file] (optional)
```

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/categories/" \
  -H "Authorization: Bearer {token}" \
  -F "name=Fruits" \
  -F "order_index=1" \
  -F "primary_image=@fruits.jpg"
```

**Validation**:
- `order_index` must be between 1 and 127
- `order_index` must be unique (409 Conflict if already used)
- `name` must be unique (409 Conflict if duplicate)

**Error Responses**:
- `422`: Missing or invalid `order_index` (out of range)
- `409`: Duplicate `order_index` or duplicate `name`

### 3. Update Category (PUT - Full Replacement)

**API**: `PUT /api/v1/categories/{id}`

**Breaking Change**: `order_index` is now **required** in the request.

**Request** (multipart/form-data):
```
name: Fruits
order_index: 2
primary_image: [file] (optional)
clear_image: false (optional)
```

**cURL Example**:
```bash
curl -X PUT "http://localhost:8000/api/v1/categories/1" \
  -H "Authorization: Bearer {token}" \
  -F "name=Fruits" \
  -F "order_index=2" \
  -F "primary_image=@fruits.jpg"
```

### 4. Partially Update Category (PATCH)

**API**: `PATCH /api/v1/categories/{id}`

**New Field**: `order_index` is now **optional** in PATCH requests.

**Request** (multipart/form-data):
```
name: Fruits (optional)
order_index: 3 (optional)
primary_image: [file] (optional)
clear_image: false (optional)
```

**cURL Example** (update only order_index):
```bash
curl -X PATCH "http://localhost:8000/api/v1/categories/1" \
  -H "Authorization: Bearer {token}" \
  -F "order_index=3"
```

## Frontend Implementation Guide

### 1. Displaying Categories in Order

Categories are automatically returned in the correct order, so you can display them directly:

```javascript
// Fetch categories - they're already in order_index order
const response = await fetch('/api/v1/categories/');
const categories = await response.json();

// Display in order (no sorting needed)
categories.forEach(category => {
  console.log(`${category.order_index}: ${category.name}`);
});
```

### 2. Creating Categories

Always include `order_index` when creating categories:

```javascript
async function createCategory(name, orderIndex, imageFile) {
  const formData = new FormData();
  formData.append('name', name);
  formData.append('order_index', orderIndex.toString());
  
  if (imageFile) {
    formData.append('primary_image', imageFile);
  }

  const response = await fetch('/api/v1/categories/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  if (!response.ok) {
    const error = await response.json();
    if (response.status === 409) {
      // Handle duplicate order_index or name
      console.error('Conflict:', error.detail);
    }
    throw new Error(error.detail);
  }

  return await response.json();
}
```

**Finding Available Order Index**:
```javascript
async function findAvailableOrderIndex() {
  const response = await fetch('/api/v1/categories/');
  const categories = await response.json();
  
  // Find the highest order_index and add 1
  const maxIndex = Math.max(...categories.map(c => c.order_index), 0);
  const nextIndex = maxIndex + 1;
  
  // Ensure it's within valid range
  if (nextIndex > 127) {
    // Find a gap in the sequence
    const usedIndices = new Set(categories.map(c => c.order_index));
    for (let i = 1; i <= 127; i++) {
      if (!usedIndices.has(i)) {
        return i;
      }
    }
    throw new Error('No available order_index (all 127 slots are used)');
  }
  
  return nextIndex;
}
```

### 3. Updating Category Order Index

```javascript
async function updateCategoryOrderIndex(categoryId, newOrderIndex) {
  const formData = new FormData();
  formData.append('order_index', newOrderIndex.toString());

  const response = await fetch(`/api/v1/categories/${categoryId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  if (!response.ok) {
    const error = await response.json();
    if (response.status === 409) {
      console.error('Order index already in use:', error.detail);
    }
    throw new Error(error.detail);
  }

  return await response.json();
}
```

### 4. Reordering Categories (Drag-and-Drop)

Use the reorder endpoint for atomic reordering:

```javascript
async function reorderCategories(orderedCategoryIds) {
  const response = await fetch('/api/v1/categories/reorder', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(orderedCategoryIds)
  });

  if (!response.ok) {
    const error = await response.json();
    if (response.status === 422) {
      console.error('Invalid permutation:', error.detail);
    } else if (response.status === 404) {
      console.error('Category not found:', error.detail);
    }
    throw new Error(error.detail);
  }

  return await response.json();
}

// Example: Drag-and-drop reordering
function handleCategoryReorder(newOrder) {
  // newOrder is an array of category IDs in the desired order
  // e.g., [3, 1, 2, 5, 4]
  
  // Get all categories
  fetch('/api/v1/categories/')
    .then(res => res.json())
    .then(activeCategories => {
      const allIds = activeCategories.map(c => c.id);
      
      // Build new order: move selected categories to top, keep others in place
      const reorderedIds = [...newOrder, ...allIds.filter(id => !newOrder.includes(id))];
      
      return reorderCategories(reorderedIds);
    })
    .then(reorderedCategories => {
      console.log('Categories reordered:', reorderedCategories);
      // Update UI with new order
    })
    .catch(error => {
      console.error('Failed to reorder:', error);
    });
}
```

### 5. Handling Order Index Conflicts

When creating or updating categories, handle order_index conflicts:

```javascript
async function createCategoryWithAutoIndex(name, imageFile) {
  let orderIndex = await findAvailableOrderIndex();
  let attempts = 0;
  const maxAttempts = 127;

  while (attempts < maxAttempts) {
    try {
      return await createCategory(name, orderIndex, imageFile);
    } catch (error) {
      if (error.message.includes('order_index') && error.message.includes('already used')) {
        // Conflict - try next available index
        orderIndex = ((orderIndex % 127) + 1);
        attempts++;
        continue;
      }
      throw error;
    }
  }

  throw new Error('Could not find available order_index after 127 attempts');
}
```

### 6. React Component Example

```jsx
import { useState, useEffect } from 'react';

function CategoryManager() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCategories();
  }, []);

  async function fetchCategories() {
    try {
      const response = await fetch('/api/v1/categories/');
      const data = await response.json();
      setCategories(data); // Already in order_index order
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  }

  async function handleReorder(newOrder) {
    // Get all category IDs in current order
    const allIds = categories.map(c => c.id);
    
    // Build complete permutation for reorder endpoint (only active categories)
    const reorderedIds = [...newOrder, ...allIds.filter(id => !newOrder.includes(id))];
    
    try {
      const response = await fetch('/api/v1/categories/reorder', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(reorderedIds)
      });

      if (!response.ok) {
        throw new Error('Failed to reorder categories');
      }

      const reordered = await response.json();
      setCategories(reordered);
    } catch (error) {
      console.error('Failed to reorder:', error);
      alert('Failed to reorder categories. Please try again.');
    }
  }

  if (loading) return <div>Loading categories...</div>;

  return (
    <div>
      <h2>Categories (ordered by order_index)</h2>
      <CategoryList 
        categories={categories} 
        onReorder={handleReorder}
      />
    </div>
  );
}
```

## Migration Checklist

### Required Changes

- [ ] Update category creation forms to include `order_index` field
- [ ] Update category update forms to include `order_index` field (required for PUT, optional for PATCH)
- [ ] Update category display to show categories in `order_index` order (already handled by API)
- [ ] Add reorder functionality using `PUT /categories/reorder` endpoint
- [ ] Handle `order_index` validation errors (422, 409)
- [ ] Update category response handling to include `order_index` field

### Optional Enhancements

- [ ] Add drag-and-drop UI for reordering categories
- [ ] Add visual indicator of `order_index` in admin interface
- [ ] Add automatic `order_index` assignment when creating categories
- [ ] Add validation UI for `order_index` range (1-127)

## Error Handling

### Common Error Scenarios

**422 Validation Error** (Missing or Invalid order_index):
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "order_index"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

**409 Conflict** (Duplicate order_index):
```json
{
  "detail": "order_index '5' is already used by another category"
}
```

**409 Conflict** (Duplicate name):
```json
{
  "detail": "Category with name 'Fruits' already exists"
}
```

**422 Unprocessable Entity** (Invalid reorder permutation):
```json
{
  "detail": "IDs list must include all categories"
}
```

**404 Not Found** (Unknown category ID in reorder):
```json
{
  "detail": "Category IDs not found: [999]"
}
```

## Best Practices

1. **Always include order_index**: When creating categories, always provide an `order_index` value
2. **Use reorder endpoint for drag-and-drop**: For UI reordering, use the atomic reorder endpoint rather than multiple PATCH requests
3. **Handle conflicts gracefully**: When `order_index` conflicts occur, automatically find the next available index
4. **Validate on frontend**: Check `order_index` range (1-127) before submitting to API
5. **Display order visually**: Show `order_index` values in admin interfaces to help users understand the ordering

## Comparison with Delivery Types

Category ordering follows the same pattern as delivery type ordering:
- Both use `order_index` field (TINYINT, 1-127, unique)
- Both have `PUT /{resource}/reorder` endpoints
- Both automatically order responses by `order_index` then name
- Both require `order_index` on creation

You can reuse similar UI patterns and logic from delivery type ordering for category ordering.
