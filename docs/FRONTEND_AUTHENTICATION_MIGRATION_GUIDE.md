# Frontend Authentication Migration Guide

## Overview
The Online Shop Business API has been upgraded with comprehensive JWT-based authentication. This document outlines all the changes made to the API and what the frontend needs to modify to work with the new authentication system.

## ⚠️ **BREAKING CHANGES**

### **Protected Endpoints**
The following endpoints now require authentication (JWT access token):

#### **Business Configuration & Core Data Management**
- `POST /api/v1/categories/` - Create categories
- `PUT /api/v1/categories/{id}` - Update categories
- `PATCH /api/v1/categories/{id}` - Partially update categories
- `DELETE /api/v1/categories/{id}` - Delete categories

- `POST /api/v1/products/` - Create products
- `PATCH /api/v1/products/{id}` - Partially update products
- `DELETE /api/v1/products/{id}` - Delete products

- `POST /api/v1/detalii-business/` - Create business details
- `PUT /api/v1/detalii-business/{id}` - Update business details
- `PATCH /api/v1/detalii-business/{id}` - Partially update business details
- `DELETE /api/v1/detalii-business/{id}` - Delete business details

#### **Business Operations**
- `POST /api/v1/tipuri-livrare/` - Create delivery types
- `PUT /api/v1/tipuri-livrare/{id}` - Update delivery types
- `PATCH /api/v1/tipuri-livrare/{id}` - Partially update delivery types
- `DELETE /api/v1/tipuri-livrare/{id}` - Delete delivery types

- `POST /api/v1/orare-livrari/` - Create delivery schedules
- `PUT /api/v1/orare-livrari/{id}` - Update delivery schedules
- `PATCH /api/v1/orare-livrari/{id}` - Partially update delivery schedules
- `DELETE /api/v1/orare-livrari/{id}` - Delete delivery schedules

- `POST /api/v1/modalitati-plata/` - Create payment methods
- `PUT /api/v1/modalitati-plata/{id}` - Update payment methods
- `PATCH /api/v1/modalitati-plata/{id}` - Partially update payment methods
- `DELETE /api/v1/modalitati-plata/{id}` - Delete payment methods

- `POST /api/v1/unitati/` - Create units
- `PUT /api/v1/unitati/{id}` - Update units
- `PATCH /api/v1/unitati/{id}` - Partially update units
- `DELETE /api/v1/unitati/{id}` - Delete units

#### **Content Management**
- `POST /api/v1/products/{id}/images` - Upload product images
- `PUT /api/v1/products/{id}/images/{image_id}/position` - Reorder images
- `PUT /api/v1/products/{id}/images/{image_id}/primary` - Set primary image
- `DELETE /api/v1/products/{id}/images/{image_id}` - Delete images
- `PUT /api/v1/products/{id}/images/reorder` - Reorder all images

- `POST /api/v1/liste/` - Create lists
- `PUT /api/v1/liste/{id}` - Update lists
- `PATCH /api/v1/liste/{id}` - Partially update lists
- `DELETE /api/v1/liste/{id}` - Delete lists

- `POST /api/v1/liste/{list_id}/products/{product_id}` - Add product to list
- `DELETE /api/v1/liste/{list_id}/products/{product_id}` - Remove product from list
- `PUT /api/v1/liste/{list_id}/products` - Replace all products in list
- `POST /api/v1/liste/{list_id}/delivery-types/{delivery_type_id}` - Add delivery type to list
- `DELETE /api/v1/liste/{list_id}/delivery-types/{delivery_type_id}` - Remove delivery type from list
- `PUT /api/v1/liste/{list_id}/delivery-types` - Replace all delivery types in list

- `POST /api/v1/product-overrides/` - Create product overrides
- `PUT /api/v1/product-overrides/{id}` - Update product overrides
- `DELETE /api/v1/product-overrides/{id}` - Delete product overrides

### **New Authentication Endpoints**
- `POST /api/v1/auth/login` - Admin login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/create-admin` - Create new admin (protected)
- `POST /api/v1/auth/change-password` - Change admin password (protected)

## **Public Endpoints (No Changes Required)**
The following endpoints remain public and require no authentication:

### **Read Operations**
- `GET /api/v1/categories/` - List categories
- `GET /api/v1/categories/{id}` - Get category details
- `GET /api/v1/products/` - List products
- `GET /api/v1/products/{id}` - Get product details
- `GET /api/v1/detalii-business/` - Get business details
- `GET /api/v1/system/` - Get system configuration
- `GET /api/v1/tipuri-livrare/` - List delivery types
- `GET /api/v1/orare-livrari/` - List delivery schedules
- `GET /api/v1/modalitati-plata/` - List payment methods
- `GET /api/v1/unitati/` - List units
- `GET /api/v1/products/{id}/images` - Get product images
- `GET /api/v1/product-overrides/` - List product overrides
- `GET /api/v1/liste/` - List lists
- `GET /api/v1/liste/{list_id}/products` - Get list products
- `GET /api/v1/liste/{list_id}/delivery-types` - Get list delivery types

## **Frontend Migration Steps**

### **Step 1: Add Authentication Service**

Create an authentication service to handle login, token management, and authenticated requests:

```javascript
// services/authService.js
class AuthService {
  constructor() {
    this.baseURL = 'http://localhost:8000/api/v1';
    this.accessToken = localStorage.getItem('accessToken');
    this.refreshToken = localStorage.getItem('refreshToken');
  }

  async login(username, password) {
    try {
      const response = await fetch(`${this.baseURL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;
      
      localStorage.setItem('accessToken', this.accessToken);
      localStorage.setItem('refreshToken', this.refreshToken);
      
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async refreshAccessToken() {
    try {
      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      this.accessToken = data.access_token;
      localStorage.setItem('accessToken', this.accessToken);
      
      return data;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.logout();
      throw error;
    }
  }

  logout() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  }

  isAuthenticated() {
    return !!this.accessToken;
  }

  getAuthHeaders() {
    return {
      'Authorization': `Bearer ${this.accessToken}`,
      'Content-Type': 'application/json',
    };
  }

  async makeAuthenticatedRequest(url, options = {}) {
    if (!this.accessToken) {
      throw new Error('No access token available');
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    });

    if (response.status === 401) {
      // Token expired, try to refresh
      try {
        await this.refreshAccessToken();
        // Retry the request with new token
        return await fetch(url, {
          ...options,
          headers: {
            ...this.getAuthHeaders(),
            ...options.headers,
          },
        });
      } catch (error) {
        this.logout();
        throw new Error('Authentication failed');
      }
    }

    return response;
  }
}

export default new AuthService();
```

### **Step 2: Update API Service**

Update your existing API service to use authentication for protected endpoints:

```javascript
// services/apiService.js
import authService from './authService';

class ApiService {
  constructor() {
    this.baseURL = 'http://localhost:8000/api/v1';
  }

  // Public endpoints (no authentication required)
  async getCategories() {
    const response = await fetch(`${this.baseURL}/categories/`);
    return response.json();
  }

  async getProducts() {
    const response = await fetch(`${this.baseURL}/products/`);
    return response.json();
  }

  // Protected endpoints (authentication required)
  async createCategory(categoryData) {
    const response = await authService.makeAuthenticatedRequest(
      `${this.baseURL}/categories/`,
      {
        method: 'POST',
        body: JSON.stringify(categoryData),
      }
    );
    return response.json();
  }

  async updateCategory(id, categoryData) {
    const response = await authService.makeAuthenticatedRequest(
      `${this.baseURL}/categories/${id}`,
      {
        method: 'PUT',
        body: JSON.stringify(categoryData),
      }
    );
    return response.json();
  }

  async deleteCategory(id) {
    const response = await authService.makeAuthenticatedRequest(
      `${this.baseURL}/categories/${id}`,
      {
        method: 'DELETE',
      }
    );
    return response;
  }

  // Similar pattern for all other protected endpoints...
  async createProduct(productData) {
    const response = await authService.makeAuthenticatedRequest(
      `${this.baseURL}/products/`,
      {
        method: 'POST',
        body: JSON.stringify(productData),
      }
    );
    return response.json();
  }

  async updateProduct(id, productData) {
    const response = await authService.makeAuthenticatedRequest(
      `${this.baseURL}/products/${id}`,
      {
        method: 'PATCH',
        body: JSON.stringify(productData),
      }
    );
    return response.json();
  }

  async deleteProduct(id) {
    const response = await authService.makeAuthenticatedRequest(
      `${this.baseURL}/products/${id}`,
      {
        method: 'DELETE',
      }
    );
    return response;
  }

  // File upload with authentication
  async uploadProductImage(productId, file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await authService.makeAuthenticatedRequest(
      `${this.baseURL}/products/${productId}/images`,
      {
        method: 'POST',
        headers: {
          // Don't set Content-Type for FormData
        },
        body: formData,
      }
    );
    return response.json();
  }
}

export default new ApiService();
```

### **Step 3: Add Login Component**

Create a login component for admin authentication:

```javascript
// components/Login.js
import React, { useState } from 'react';
import authService from '../services/authService';

const Login = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await authService.login(username, password);
      onLoginSuccess();
    } catch (error) {
      setError('Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit}>
        <h2>Admin Login</h2>
        {error && <div className="error">{error}</div>}
        <div>
          <label>Username:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
};

export default Login;
```

### **Step 4: Update App Component**

Update your main app component to handle authentication state:

```javascript
// App.js
import React, { useState, useEffect } from 'react';
import authService from './services/authService';
import Login from './components/Login';
import Dashboard from './components/Dashboard';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already authenticated
    setIsAuthenticated(authService.isAuthenticated());
    setLoading(false);
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div>
      <header>
        <h1>Online Shop Business Admin</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>
      <Dashboard />
    </div>
  );
};

export default App;
```

### **Step 5: Update Error Handling**

Update your error handling to handle 401 Unauthorized responses:

```javascript
// utils/errorHandler.js
export const handleApiError = (error, response) => {
  if (response?.status === 401) {
    // Redirect to login or show login modal
    return {
      type: 'AUTHENTICATION_REQUIRED',
      message: 'Please log in to continue',
    };
  }

  if (response?.status === 403) {
    return {
      type: 'FORBIDDEN',
      message: 'You do not have permission to perform this action',
    };
  }

  return {
    type: 'GENERAL_ERROR',
    message: error.message || 'An error occurred',
  };
};
```

## **Environment Configuration**

### **Required Environment Variables**
Make sure your frontend has access to the correct API URL:

```javascript
// config.js
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  AUTH_ENDPOINT: '/auth/login',
  REFRESH_ENDPOINT: '/auth/refresh',
};
```

## **Testing Checklist**

### **Authentication Flow**
- [ ] Login with valid credentials
- [ ] Login with invalid credentials (error handling)
- [ ] Token refresh when access token expires
- [ ] Logout functionality
- [ ] Persistent authentication state

### **Protected Endpoints**
- [ ] Test all POST endpoints with authentication
- [ ] Test all PUT/PATCH endpoints with authentication
- [ ] Test all DELETE endpoints with authentication
- [ ] Test file upload endpoints with authentication
- [ ] Test error handling for 401 responses

### **Public Endpoints**
- [ ] Verify all GET endpoints work without authentication
- [ ] Test error handling for public endpoints

### **Error Scenarios**
- [ ] Network errors
- [ ] Token expiration
- [ ] Invalid tokens
- [ ] Server errors (500, 404, etc.)

## **Migration Timeline**

### **Phase 1: Authentication Setup (1-2 days)**
- [ ] Implement authentication service
- [ ] Add login component
- [ ] Update app routing for authentication

### **Phase 2: API Integration (2-3 days)**
- [ ] Update all protected endpoints
- [ ] Test authentication flow
- [ ] Handle error scenarios

### **Phase 3: Testing & Polish (1-2 days)**
- [ ] Comprehensive testing
- [ ] Error handling improvements
- [ ] User experience refinements

## **Common Issues & Solutions**

### **CORS Issues**
If you encounter CORS issues, contact the API team to ensure your frontend domain is properly configured in the CORS settings.

### **Token Storage**
Consider using secure storage for tokens in production:
- Use `httpOnly` cookies for better security
- Implement token rotation
- Add token expiration handling

### **Error Handling**
Implement comprehensive error handling:
- Network errors
- Authentication errors
- Validation errors
- Server errors

## **Security Best Practices**

### **Frontend Security**
- [ ] Never store sensitive data in localStorage (use httpOnly cookies)
- [ ] Implement proper token expiration handling
- [ ] Add CSRF protection
- [ ] Sanitize user inputs
- [ ] Implement rate limiting for login attempts

### **API Security**
- [ ] Use HTTPS in production
- [ ] Implement proper CORS configuration
- [ ] Add request validation
- [ ] Monitor for suspicious activity

## **Support**

If you encounter any issues during migration:

1. **Check the API documentation** for endpoint details
2. **Review the authentication tests** for usage examples
3. **Test with the provided test utilities**
4. **Check the server logs** for detailed error messages

## **Conclusion**

This migration will require significant changes to your frontend code, but the result will be a much more secure and robust application. The authentication system provides:

- **Secure admin access** to all mutable operations
- **Public read access** to all data
- **Automatic token management** with refresh capabilities
- **Comprehensive error handling** for all scenarios

Take your time with the migration and test thoroughly at each step. The authentication system is designed to be reliable and secure for production use. 