# Frontend Guide: List Cloning API

## Overview
The new list cloning API allows frontend users to duplicate existing product lists with a single API call. This eliminates the need to manually recreate lists with similar structure and ordering.

## API Endpoint

### Clone a List
```
POST /api/v1/liste/{list_id}/clone
```

**URL Parameters:**
- `{list_id}` - The ID of the existing list you want to clone

**Headers Required:**
- `Authorization: Bearer {admin_token}` - Admin authentication token
- `Content-Type: application/json`

**Request Body:**
- None required (empty JSON `{}`)

## Frontend Implementation Examples

### JavaScript/TypeScript with Fetch

```typescript
interface List {
  id: number;
  data: string;
  is_current: boolean;
  is_published: boolean;
  mesaj_introducere: string;
  alte_detalii: string;
  numar_whatsapp: string;
  orare_livrari_id: number;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
}

async function cloneList(listId: number, adminToken: string): Promise<List> {
  try {
    const response = await fetch(`/api/v1/liste/${listId}/clone`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${adminToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({})
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const clonedList: List = await response.json();
    return clonedList;
  } catch (error) {
    console.error('Error cloning list:', error);
    throw error;
  }
}

// Usage
const newList = await cloneList(5, adminToken);
console.log('Cloned list ID:', newList.id); // New ID will be different
```

### React Hook Example

```typescript
import { useState } from 'react';

interface UseListCloning {
  cloneList: (listId: number) => Promise<void>;
  isCloning: boolean;
  error: string | null;
  clonedList: List | null;
}

export function useListCloning(adminToken: string): UseListCloning {
  const [isCloning, setIsCloning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clonedList, setClonedList] = useState<List | null>(null);

  const cloneList = async (listId: number) => {
    setIsCloning(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/v1/liste/${listId}/clone`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to clone list');
      }

      const newList = await response.json();
      setClonedList(newList);
      
      // Optionally redirect to the new list or show success message
      console.log('List cloned successfully! New ID:', newList.id);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setIsCloning(false);
    }
  };

  return { cloneList, isCloning, error, clonedList };
}
```

### React Component Example

```tsx
import React from 'react';
import { useListCloning } from './hooks/useListCloning';

interface ListCloneButtonProps {
  listId: number;
  adminToken: string;
  onCloneSuccess?: (clonedList: List) => void;
}

export function ListCloneButton({ listId, adminToken, onCloneSuccess }: ListCloneButtonProps) {
  const { cloneList, isCloning, error, clonedList } = useListCloning(adminToken);

  const handleClone = async () => {
    await cloneList(listId);
  };

  React.useEffect(() => {
    if (clonedList && onCloneSuccess) {
      onCloneSuccess(clonedList);
    }
  }, [clonedList, onCloneSuccess]);

  return (
    <div>
      <button 
        onClick={handleClone} 
        disabled={isCloning}
        className="btn btn-primary"
      >
        {isCloning ? 'Cloning...' : 'Clone List'}
      </button>
      
      {error && (
        <div className="error-message">
          Error: {error}
        </div>
      )}
      
      {clonedList && (
        <div className="success-message">
          List cloned successfully! New ID: {clonedList.id}
        </div>
      )}
    </div>
  );
}
```

## What Happens When You Clone

### 1. **List Metadata is Copied:**
- ✅ Date (`data`)
- ✅ Introduction message (`mesaj_introducere`)
- ✅ Additional details (`alte_detalii`)
- ✅ WhatsApp number (`numar_whatsapp`)
- ✅ Delivery schedule (`orare_livrari_id`)

### 2. **Smart Defaults Applied:**
- ✅ `is_current` → `false` (new list won't override current list)
- ✅ `is_published` → `false` (new list starts as draft)
- ✅ `is_deleted` → `false`

### 3. **Structure is Preserved:**
- ✅ Category ordering (if any categories exist)
- ✅ Product ordering within categories (if any products exist)
- ✅ Stock quantities (if any products have stock)

### 4. **New List Gets:**
- ✅ New unique ID
- ✅ Current timestamps (`created_at`, `updated_at`)

## Common Use Cases

### 1. **Daily/Weekly Lists**
```typescript
// Clone yesterday's list for today
const yesterdayListId = 5;
const newList = await cloneList(yesterdayListId, adminToken);

// Now customize the new list
await updateList(newList.id, {
  data: new Date().toISOString().split('T')[0], // Today's date
  is_current: true,
  is_published: true
});
```

### 2. **Template Lists**
```typescript
// Clone a template list for a new event
const templateListId = 10;
const eventList = await cloneList(templateListId, adminToken);

// Customize for specific event
await updateList(eventList.id, {
  mesaj_introducere: "Special event - limited time offer!",
  is_published: true
});
```

### 3. **Seasonal Lists**
```typescript
// Clone summer list for winter season
const summerListId = 15;
const winterList = await cloneList(summerListId, adminToken);

// Update for winter season
await updateList(winterList.id, {
  mesaj_introducere: "Winter collection now available!",
  alte_detalii: "Warm up with our winter products"
});
```

## Error Handling

### Common HTTP Status Codes

| Status | Meaning | Action |
|--------|---------|---------|
| `201` | ✅ Success | List cloned successfully |
| `401` | ❌ Unauthorized | Check admin token |
| `404` | ❌ Not Found | Source list doesn't exist |
| `422` | ❌ Validation Error | Invalid list ID |
| `500` | ❌ Server Error | Try again later |

### Error Response Format
```json
{
  "detail": "List with ID 999 not found"
}
```

## Best Practices

### 1. **User Experience**
- Show loading state while cloning
- Display success message with new list ID
- Optionally redirect to the new list
- Handle errors gracefully with user-friendly messages

### 2. **Performance**
- Clone operation is typically fast (< 1 second)
- Consider showing progress indicator for large lists
- Don't block UI while cloning

### 3. **Security**
- Always use admin authentication
- Validate list ID on frontend before sending
- Don't expose admin tokens in client-side code

### 4. **Workflow Integration**
- Clone → Customize → Publish
- Consider adding confirmation dialog before cloning
- Provide option to clone and immediately edit

## Example Complete Workflow

```typescript
async function cloneAndCustomizeList(sourceListId: number, customizations: Partial<List>) {
  try {
    // 1. Clone the list
    const clonedList = await cloneList(sourceListId, adminToken);
    
    // 2. Customize the cloned list
    const updatedList = await updateList(clonedList.id, customizations);
    
    // 3. Optionally publish
    if (customizations.is_published) {
      await publishList(clonedList.id);
    }
    
    return updatedList;
  } catch (error) {
    console.error('Failed to clone and customize list:', error);
    throw error;
  }
}

// Usage
const newList = await cloneAndCustomizeList(5, {
  data: '2025-08-17',
  mesaj_introducere: 'New week, new products!',
  is_current: true,
  is_published: true
});
```

## Testing

### Test the API
```bash
# 1. Get admin token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "adminpass123"}'

# 2. Clone a list (replace TOKEN and LIST_ID)
curl -X POST "http://localhost:8000/api/v1/liste/LIST_ID/clone" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

This API should significantly improve the user experience by eliminating repetitive work when creating similar product lists! 🚀
