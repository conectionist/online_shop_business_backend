# Frontend Migration Guide: Order Error Responses (API v4.0.0)

## Overview

API version 4.0.0 introduces **breaking changes** to error responses for order creation. Error responses now use a structured format instead of plain string messages, making them easier to parse and handle programmatically.

## What Changed

### 1. Status Code Change
- **Out-of-stock errors**: Changed from `400 Bad Request` to `409 Conflict`
- **Duplicate order errors**: Still `409 Conflict` (unchanged)

### 2. Error Response Format
Error responses now use structured objects instead of string messages.

**Before (API v3.x):**
```json
{
  "detail": "Insufficient stock for product 7 in list 57"
}
```

**After (API v4.0.0):**
```json
{
  "detail": {
    "error_code": "INSUFFICIENT_STOCK",
    "message": "Insufficient stock for product",
    "product_id": 7,
    "list_id": 57,
    "requested_quantity": 5,
    "available_quantity": 2
  }
}
```

## Error Types

### 1. Duplicate Order Error

**Status Code:** `409 Conflict`

**Response Format:**
```json
{
  "detail": {
    "error_code": "DUPLICATE_ORDER",
    "message": "Duplicate order detected: an order with the same customer and items already exists",
    "order_id": 117
  }
}
```

### 2. Insufficient Stock Error

**Status Code:** `409 Conflict` (changed from `400`)

**Response Format:**
```json
{
  "detail": {
    "error_code": "INSUFFICIENT_STOCK",
    "message": "Insufficient stock for product",
    "product_id": 7,
    "list_id": 57,
    "requested_quantity": 5,
    "available_quantity": 2
  }
}
```

## Frontend Migration Steps

### Step 1: Update Error Handling Logic

**Old code (parsing string messages):**
```javascript
try {
  const response = await fetch('/api/v1/orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    const errorMessage = error.detail; // string
    
    // Parsing string to extract IDs (fragile!)
    if (errorMessage.includes('Insufficient stock')) {
      const match = errorMessage.match(/product (\d+)/);
      const productId = match ? parseInt(match[1]) : null;
      // Handle out of stock...
    } else if (errorMessage.includes('Duplicate order')) {
      const match = errorMessage.match(/id=(\d+)/);
      const orderId = match ? parseInt(match[1]) : null;
      // Handle duplicate...
    }
  }
} catch (error) {
  // Handle error
}
```

**New code (using structured errors):**
```javascript
try {
  const response = await fetch('/api/v1/orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    const errorDetail = error.detail;
    
    // Check if it's a structured error (object) or legacy string
    if (typeof errorDetail === 'object' && errorDetail.error_code) {
      switch (errorDetail.error_code) {
        case 'INSUFFICIENT_STOCK':
          // Direct access to structured data - no parsing needed!
          showOutOfStockError({
            productId: errorDetail.product_id,
            listId: errorDetail.list_id,
            requested: errorDetail.requested_quantity,
            available: errorDetail.available_quantity
          });
          break;
          
        case 'DUPLICATE_ORDER':
          showDuplicateOrderError({
            orderId: errorDetail.order_id,
            message: errorDetail.message
          });
          break;
          
        default:
          showGenericError(errorDetail.message);
      }
    } else {
      // Fallback for legacy string format (if still in use)
      showGenericError(errorDetail);
    }
  }
} catch (error) {
  // Handle network/other errors
}
```

### Step 2: Update Status Code Checks

**Update any code that checks for `400` status for out-of-stock errors:**

```javascript
// OLD - checking for 400
if (response.status === 400) {
  // Handle out of stock
}

// NEW - check for 409 and error_code
if (response.status === 409) {
  const error = await response.json();
  if (error.detail?.error_code === 'INSUFFICIENT_STOCK') {
    // Handle out of stock
  } else if (error.detail?.error_code === 'DUPLICATE_ORDER') {
    // Handle duplicate order
  }
}
```

### Step 3: Create Helper Functions (Recommended)

```javascript
/**
 * Parse order creation error response
 * @param {Response} response - Fetch response object
 * @returns {Promise<Object>} Parsed error object
 */
async function parseOrderError(response) {
  const error = await response.json();
  const detail = error.detail;
  
  // Handle structured errors (API v4.0.0+)
  if (typeof detail === 'object' && detail.error_code) {
    return {
      type: detail.error_code,
      message: detail.message,
      ...detail // Spread all additional fields (product_id, order_id, etc.)
    };
  }
  
  // Fallback for legacy string format
  return {
    type: 'UNKNOWN',
    message: typeof detail === 'string' ? detail : 'An error occurred'
  };
}

// Usage:
if (!response.ok) {
  const error = await parseOrderError(response);
  
  if (error.type === 'INSUFFICIENT_STOCK') {
    // error.product_id, error.available_quantity, etc. are available
    showError(`Product ${error.product_id} is out of stock. Available: ${error.available_quantity}`);
  } else if (error.type === 'DUPLICATE_ORDER') {
    // error.order_id is available
    showError(`This order already exists (Order #${error.order_id})`);
  }
}
```

## Benefits of the New Format

1. **No String Parsing**: Direct access to `product_id`, `order_id`, and quantities
2. **Type Safety**: Structured data is easier to validate and type-check
3. **Better UX**: Can show specific product names, quantities, and order references
4. **Consistent Format**: Both error types use the same structure
5. **Extensible**: Easy to add new fields without breaking existing code

## Example: Complete Error Handler

```javascript
async function createOrder(orderData) {
  try {
    const response = await fetch('/api/v1/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orderData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      const detail = error.detail;
      
      // Handle structured errors
      if (typeof detail === 'object' && detail.error_code) {
        switch (detail.error_code) {
          case 'INSUFFICIENT_STOCK':
            // Fetch product name for better UX
            const product = await getProduct(detail.product_id);
            throw new OutOfStockError({
              productId: detail.product_id,
              productName: product?.name || `Product ${detail.product_id}`,
              requested: detail.requested_quantity,
              available: detail.available_quantity,
              listId: detail.list_id
            });
            
          case 'DUPLICATE_ORDER':
            throw new DuplicateOrderError({
              orderId: detail.order_id,
              message: detail.message
            });
            
          default:
            throw new Error(detail.message || 'Unknown error');
        }
      } else {
        // Legacy string format fallback
        throw new Error(typeof detail === 'string' ? detail : 'An error occurred');
      }
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof OutOfStockError) {
      // Handle out of stock with specific product info
      showNotification({
        type: 'error',
        message: `${error.productName} is out of stock. Available: ${error.available}, Requested: ${error.requested}`
      });
    } else if (error instanceof DuplicateOrderError) {
      // Handle duplicate order
      showNotification({
        type: 'warning',
        message: `This order already exists. Order ID: ${error.orderId}`
      });
    } else {
      // Generic error handling
      showNotification({
        type: 'error',
        message: error.message || 'Failed to create order'
      });
    }
    throw error;
  }
}
```

## Testing Checklist

- [ ] Update error handling to check for `error_code` field
- [ ] Change status code checks from `400` to `409` for out-of-stock errors
- [ ] Update UI to display structured error information (product IDs, quantities)
- [ ] Test duplicate order detection
- [ ] Test out-of-stock scenarios
- [ ] Verify error messages display correctly to users
- [ ] Consider adding fallback for legacy string format (if needed)

## Questions or Issues?

If you encounter any issues during migration or have questions about the new error format, please contact the backend team or refer to the API documentation at `/api/v1/docs`.

