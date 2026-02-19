# Frontend Guide: Bulk Update Positions API

## Overview

The new bulk update positions API allows frontend applications to reorder categories and products within a list using a single API call. This replaces the need for multiple individual PATCH requests and provides a more efficient way to handle drag-and-drop reordering.

## API Endpoint

```
PUT /api/v1/liste/{list_id}/positions
```

**Authentication Required:** Yes (Admin token)

## Request Format

### Headers
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

### Request Body
```json
{
  "positions": [
    {
      "category_id": 2,
      "products": [1, 3, 0, 2]
    },
    {
      "category_id": 3,
      "products": [1, 0]
    },
    {
      "category_id": 1,
      "products": [33, 55]
    }
  ]
}
```

### Structure Explanation

- **`positions`**: Array of category objects in the desired order
- **`category_id`**: ID of the category
- **`products`**: Array of product IDs in the desired order within that category

**Important Notes:**
- The order of categories in the array determines their position (index 0 = first, index 1 = second, etc.)
- The order of products in each array determines their position within that category
- Each product can only appear once across all categories
- Each category can only appear once in the request

## Response Format

### Success Response (200)
```json
{
  "message": "Bulk position update completed successfully for list 5",
  "list_id": 5,
  "updated_structure": {
    "list_id": 5,
    "categories": [
      {
        "id": 10,
        "name": "Deliciosenii de cofetarie",
        "position": 0,
        "products": [
          {
            "id": 15,
            "nume": "Monoportie cu fructe exotice",
            "position": 0,
            "stoc_produs": null,
            // ... other product fields
          }
          // ... more products
        ]
      }
      // ... more categories
    ]
  }
}
```

### Error Responses

#### 400 Bad Request
```json
{
  "detail": "Invalid data provided: Duplicate category IDs are not allowed"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

#### 404 Not Found
```json
{
  "detail": "Product with ID 99999 not found"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "positions", 0, "products"],
      "msg": "Duplicate product IDs are not allowed within the same category",
      "type": "value_error"
    }
  ]
}
```

## Frontend Implementation Examples

### JavaScript/TypeScript Example

```typescript
interface CategoryPosition {
  category_id: number;
  products: number[];
}

interface BulkUpdateRequest {
  positions: CategoryPosition[];
}

interface BulkUpdateResponse {
  message: string;
  list_id: number;
  updated_structure: {
    list_id: number;
    categories: Array<{
      id: number;
      name: string;
      position: number;
      products: Array<{
        id: number;
        nume: string;
        position: number;
        stoc_produs: number | null;
        // ... other fields
      }>;
    }>;
  };
}

async function bulkUpdatePositions(
  listId: number, 
  positions: CategoryPosition[], 
  authToken: string
): Promise<BulkUpdateResponse> {
  const response = await fetch(`/api/v1/liste/${listId}/positions`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ positions }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Bulk update failed: ${error.detail}`);
  }

  return response.json();
}
```

### React Hook Example

```typescript
import { useState, useCallback } from 'react';

interface UseBulkUpdateProps {
  listId: number;
  authToken: string;
}

export function useBulkUpdate({ listId, authToken }: UseBulkUpdateProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updatePositions = useCallback(async (positions: CategoryPosition[]) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await bulkUpdatePositions(listId, positions, authToken);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [listId, authToken]);

  return {
    updatePositions,
    isLoading,
    error,
  };
}
```

### Drag and Drop Implementation

```typescript
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

interface ListEditorProps {
  listId: number;
  initialData: ListStructure;
  onUpdate: (positions: CategoryPosition[]) => void;
}

export function ListEditor({ listId, initialData, onUpdate }: ListEditorProps) {
  const [categories, setCategories] = useState(initialData.categories);

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;

    const { source, destination, type } = result;

    if (type === 'category') {
      // Reorder categories
      const newCategories = Array.from(categories);
      const [removed] = newCategories.splice(source.index, 1);
      newCategories.splice(destination.index, 0, removed);
      
      setCategories(newCategories);
      
      // Prepare positions data
      const positions: CategoryPosition[] = newCategories.map(category => ({
        category_id: category.id,
        products: category.products.map(p => p.id)
      }));
      
      onUpdate(positions);
    } else if (type === 'product') {
      // Reorder products within category
      const sourceCategoryId = parseInt(source.droppableId);
      const destCategoryId = parseInt(destination.droppableId);
      
      const newCategories = categories.map(category => {
        if (category.id === sourceCategoryId) {
          const newProducts = Array.from(category.products);
          const [removed] = newProducts.splice(source.index, 1);
          
          if (sourceCategoryId === destCategoryId) {
            // Same category
            newProducts.splice(destination.index, 0, removed);
          }
          // If different category, product will be moved in the next step
          
          return { ...category, products: newProducts };
        } else if (category.id === destCategoryId && sourceCategoryId !== destCategoryId) {
          // Different category - add product to destination
          const newProducts = Array.from(category.products);
          const movedProduct = categories
            .find(c => c.id === sourceCategoryId)?.products[source.index];
          
          if (movedProduct) {
            newProducts.splice(destination.index, 0, movedProduct);
          }
          
          return { ...category, products: newProducts };
        }
        return category;
      });
      
      setCategories(newCategories);
      
      // Prepare positions data
      const positions: CategoryPosition[] = newCategories.map(category => ({
        category_id: category.id,
        products: category.products.map(p => p.id)
      }));
      
      onUpdate(positions);
    }
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Droppable droppableId="categories" type="category">
        {(provided) => (
          <div {...provided.droppableProps} ref={provided.innerRef}>
            {categories.map((category, index) => (
              <Draggable key={category.id} draggableId={`category-${category.id}`} index={index}>
                {(provided) => (
                  <div ref={provided.innerRef} {...provided.draggableProps}>
                    <h3 {...provided.dragHandleProps}>{category.name}</h3>
                    
                    <Droppable droppableId={category.id.toString()} type="product">
                      {(provided) => (
                        <div {...provided.droppableProps} ref={provided.innerRef}>
                          {category.products.map((product, index) => (
                            <Draggable key={product.id} draggableId={`product-${product.id}`} index={index}>
                              {(provided) => (
                                <div ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps}>
                                  {product.nume}
                                </div>
                              )}
                            </Draggable>
                          ))}
                          {provided.placeholder}
                        </div>
                      )}
                    </Droppable>
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  );
}
```

### Complete Usage Example

```typescript
function ListManagementPage() {
  const { listId } = useParams();
  const { authToken } = useAuth();
  const { updatePositions, isLoading, error } = useBulkUpdate({ 
    listId: parseInt(listId!), 
    authToken 
  });

  const handlePositionsUpdate = async (positions: CategoryPosition[]) => {
    try {
      await updatePositions(positions);
      // Show success message
      toast.success('List order updated successfully!');
    } catch (err) {
      // Show error message
      toast.error('Failed to update list order');
    }
  };

  return (
    <div>
      <h1>Edit List Order</h1>
      
      {error && (
        <div className="error-message">
          Error: {error}
        </div>
      )}
      
      {isLoading && (
        <div className="loading">
          Updating positions...
        </div>
      )}
      
      <ListEditor
        listId={parseInt(listId!)}
        initialData={listData}
        onUpdate={handlePositionsUpdate}
      />
    </div>
  );
}
```

## Validation Rules

### Frontend Validation

Before sending the request, validate:

1. **No duplicate categories**: Each `category_id` should appear only once
2. **No duplicate products**: Each product ID should appear only once across all categories
3. **Valid IDs**: All category and product IDs should be positive integers
4. **Non-empty arrays**: Each category should have at least one product

```typescript
function validatePositions(positions: CategoryPosition[]): string[] {
  const errors: string[] = [];
  
  // Check for duplicate categories
  const categoryIds = positions.map(p => p.category_id);
  const uniqueCategoryIds = new Set(categoryIds);
  if (categoryIds.length !== uniqueCategoryIds.size) {
    errors.push('Duplicate category IDs are not allowed');
  }
  
  // Check for duplicate products
  const allProductIds: number[] = [];
  positions.forEach(pos => allProductIds.push(...pos.products));
  const uniqueProductIds = new Set(allProductIds);
  if (allProductIds.length !== uniqueProductIds.size) {
    errors.push('Duplicate product IDs are not allowed');
  }
  
  // Check for empty product arrays
  positions.forEach((pos, index) => {
    if (pos.products.length === 0) {
      errors.push(`Category ${pos.category_id} must have at least one product`);
    }
  });
  
  return errors;
}
```

## Migration from Individual Updates

### Before (Multiple PATCH calls)
```typescript
// Old way - multiple API calls
async function updateProductPosition(listId: number, productId: number, newPosition: number) {
  await fetch(`/api/v1/liste/${listId}/products/${productId}/position`, {
    method: 'PATCH',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ new_position: newPosition })
  });
}

// Multiple calls needed for complex reordering
await updateProductPosition(listId, 1, 2);
await updateProductPosition(listId, 2, 0);
await updateProductPosition(listId, 3, 1);
// ... more calls
```

### After (Single PUT call)
```typescript
// New way - single API call
async function updateAllPositions(listId: number, positions: CategoryPosition[]) {
  await fetch(`/api/v1/liste/${listId}/positions`, {
    method: 'PUT',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ positions })
  });
}

// Single call for any reordering
await updateAllPositions(listId, [
  { category_id: 1, products: [2, 3, 1] },
  { category_id: 2, products: [4, 5] }
]);
```

## Best Practices

1. **Debounce Updates**: When implementing drag-and-drop, debounce the API calls to avoid excessive requests
2. **Optimistic Updates**: Update the UI immediately, then sync with the server
3. **Error Handling**: Always handle API errors and provide user feedback
4. **Loading States**: Show loading indicators during API calls
5. **Validation**: Validate data on the frontend before sending to the API

```typescript
import { debounce } from 'lodash';

const debouncedUpdate = debounce(async (positions: CategoryPosition[]) => {
  try {
    await updatePositions(positions);
  } catch (err) {
    // Revert optimistic update on error
    setCategories(originalCategories);
  }
}, 500);
```

## Testing

### Unit Tests
```typescript
describe('Bulk Update Positions', () => {
  it('should send correct request format', async () => {
    const positions = [
      { category_id: 1, products: [1, 2, 3] },
      { category_id: 2, products: [4, 5] }
    ];
    
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ message: 'Success' })
    });
    
    global.fetch = mockFetch;
    
    await bulkUpdatePositions(5, positions, 'token');
    
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/liste/5/positions',
      expect.objectContaining({
        method: 'PUT',
        headers: {
          'Authorization': 'Bearer token',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ positions })
      })
    );
  });
});
```

## Summary

The new bulk update API provides:

✅ **Single API call** for complex reordering  
✅ **Atomic operations** - all changes happen together  
✅ **Better performance** - fewer network requests  
✅ **Simpler frontend logic** - no need to manage multiple async calls  
✅ **Better error handling** - single point of failure  
✅ **Drag-and-drop friendly** - perfect for UI reordering  

This replaces the previous approach of multiple individual PATCH calls with a more efficient and user-friendly solution. 