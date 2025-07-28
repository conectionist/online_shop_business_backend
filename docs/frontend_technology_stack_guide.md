# Frontend Technology Stack Guide

## 🎯 **Recommended Technology Stack**

Based on the analysis of your FastAPI backend, here's the **optimal frontend technology stack** for your online shop business:

### **Core Technologies**
```
Frontend Stack:
├── React 18+ (with hooks)
├── TypeScript 5+
├── Vite (build tool)
├── React Router (navigation)
├── TanStack Query (API state management)
├── Zustand (local state)
├── Tailwind CSS (styling)
├── React Hook Form (forms)
├── React Dropzone (file uploads)
└── Lucide React (icons)
```

### **Why This Stack is Perfect for Your Backend**

1. **Perfect API Compatibility**: Your FastAPI backend returns well-structured JSON with Pydantic schemas that map perfectly to TypeScript interfaces
2. **Image Upload Requirements**: Your API has sophisticated image handling (multiple versions, reordering, primary images) - React has excellent file upload libraries
3. **Complex State Management**: Your e-commerce domain has complex relationships (products, categories, lists, overrides) - React's ecosystem handles this well
4. **Type Safety**: Your backend uses strong typing - TypeScript will give you end-to-end type safety

## 🏗️ **Project Architecture**

### **Recommended Project Structure**
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/           # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── ...
│   │   ├── forms/        # Form components
│   │   │   ├── ProductForm.tsx
│   │   │   ├── CategoryForm.tsx
│   │   │   └── ...
│   │   ├── layout/       # Layout components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── ...
│   │   └── features/     # Feature-specific components
│   │       ├── products/
│   │       ├── categories/
│   │       ├── lists/
│   │       └── admin/
│   ├── hooks/            # Custom React hooks
│   │   ├── useApi.ts
│   │   ├── useAuth.ts
│   │   └── ...
│   ├── services/         # API service functions
│   │   ├── api.ts
│   │   ├── products.ts
│   │   ├── categories.ts
│   │   └── ...
│   ├── stores/           # State management
│   │   ├── authStore.ts
│   │   ├── cartStore.ts
│   │   └── ...
│   ├── types/            # TypeScript interfaces
│   │   ├── api.ts
│   │   ├── products.ts
│   │   └── ...
│   ├── utils/            # Utility functions
│   │   ├── api.ts
│   │   ├── validation.ts
│   │   └── ...
│   ├── pages/            # Page components
│   │   ├── admin/
│   │   ├── customer/
│   │   └── ...
│   └── App.tsx
├── public/               # Static assets
├── package.json
└── vite.config.ts
```

## 🚀 **Getting Started**

### **1. Project Setup with Docker**

```bash
# Create new React project with Vite
npm create vite@latest frontend -- --template react-ts

# Navigate to project
cd frontend

# Create Dockerfile
touch Dockerfile

# Create docker-compose.yml
touch docker-compose.yml

# Create .dockerignore
touch .dockerignore
```

### **2. Docker Configuration**

```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Install serve to run the built app
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Start the app
CMD ["serve", "-s", "dist", "-l", "3000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: online_shop_frontend
    restart: always
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./src:/app/src
      - ./public:/app/public
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

```gitignore
# .dockerignore
node_modules
npm-debug.log
dist
.git
.gitignore
README.md
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
```

### **3. Development Docker Setup**

```dockerfile
# Dockerfile.dev (for development)
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies)
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  frontend-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: online_shop_frontend_dev
    restart: always
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./src:/app/src
      - ./public:/app/public
      - ./package.json:/app/package.json
      - ./vite.config.ts:/app/vite.config.ts
      - ./tailwind.config.js:/app/tailwind.config.js
      - ./tsconfig.json:/app/tsconfig.json
      - ./index.html:/app/index.html
    stdin_open: true
    tty: true
```

### **4. Running the Application**

```bash
# Development mode (with hot reload)
docker-compose -f docker-compose.dev.yml up --build

# Production mode
docker-compose up --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f frontend-dev

# Access container shell
docker-compose exec frontend-dev sh
```

### **5. Environment Setup**

```bash
# Create your own .env file for frontend
cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Online Shop
EOF
```

### **2. Essential Dependencies**

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "@tanstack/react-query": "^4.29.0",
    "zustand": "^4.3.0",
    "react-hook-form": "^7.43.0",
    "@hookform/resolvers": "^2.9.0",
    "zod": "^3.20.0",
    "react-dropzone": "^14.2.0",
    "lucide-react": "^0.263.0",
    "axios": "^1.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "@types/node": "^18.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.2.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^4.3.0"
  }
}
```

### **3. Package.json Scripts**

```json
{
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "type-check": "tsc --noEmit"
  }
}
```

### **4. TypeScript Configuration**

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

## 📡 **API Integration**

### **1. API Client Setup**

```typescript
// src/services/api.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### **2. TypeScript Interfaces from Backend**

```typescript
// src/types/api.ts
export interface Product {
  id: number;
  nume: string;
  cantitate: number;
  pret: number;
  description?: string;
  category_id: number;
  unitati_id: number;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  images: ProductImage[];
  image_versions: {
    original: string;
    medium: string;
    thumbnail: string;
  };
}

export interface Category {
  id: number;
  name: string;
  image_path?: string;
  image_versions: {
    original: string;
    medium: string;
    thumbnail: string;
  };
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface List {
  id: number;
  data: string;
  is_current: boolean;
  is_published: boolean;
  mesaj_introducere?: string;
  alte_detalii?: string;
  numar_whatsapp?: string;
  orare_livrari_id: number;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
}

export interface ProductImage {
  id: number;
  path: string;
  position: number;
  produse_id: number;
  is_primary: boolean;
  image_versions: {
    original: string;
    medium: string;
    thumbnail: string;
  };
}

export interface Unit {
  id: number;
  denumire: string;
}

export interface DeliveryType {
  id: number;
  denumire: string;
}

export interface PaymentMethod {
  id: number;
  denumire: string;
}

export interface BusinessDetails {
  id: number;
  adresa?: string;
  telefon?: string;
  logo_path?: string;
  motto?: string;
  list_not_available_msg?: string;
  alte_detalii?: string;
}
```

### **3. API Service Functions**

```typescript
// src/services/products.ts
import { apiClient } from './api';
import { Product } from '@/types/api';

export const productsApi = {
  // Get all products
  getProducts: async (params?: {
    skip?: number;
    limit?: number;
    include_deleted?: boolean;
    category_id?: number;
  }) => {
    const response = await apiClient.get<Product[]>('/products', { params });
    return response.data;
  },

  // Get specific product
  getProduct: async (id: number, include_deleted = false) => {
    const response = await apiClient.get<Product>(`/products/${id}`, {
      params: { include_deleted }
    });
    return response.data;
  },

  // Create product
  createProduct: async (data: FormData) => {
    const response = await apiClient.post<Product>('/products', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Update product
  updateProduct: async (id: number, data: FormData) => {
    const response = await apiClient.patch<Product>(`/products/${id}`, data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Delete product
  deleteProduct: async (id: number, permanent = false) => {
    await apiClient.delete(`/products/${id}`, {
      params: { permanent }
    });
  },

  // Upload product image
  uploadImage: async (productId: number, file: File, position?: number) => {
    const formData = new FormData();
    formData.append('file', file);
    if (position !== undefined) {
      formData.append('position', position.toString());
    }
    
    const response = await apiClient.post(`/products/${productId}/images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }
};
```

## 🎨 **UI/UX Implementation**

### **1. Mobile-First Design**

```typescript
// src/components/layout/Header.tsx
import { useState } from 'react';
import { Menu, X, ShoppingCart } from 'lucide-react';

export const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <h1 className="text-xl font-bold text-gray-900">Online Shop</h1>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-8">
            <a href="/" className="text-gray-700 hover:text-gray-900">Home</a>
            <a href="/products" className="text-gray-700 hover:text-gray-900">Products</a>
            <a href="/lists" className="text-gray-700 hover:text-gray-900">Lists</a>
          </nav>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-700 hover:text-gray-900"
            >
              {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>

          {/* Cart Icon */}
          <div className="flex items-center">
            <button className="relative p-2 text-gray-700 hover:text-gray-900">
              <ShoppingCart size={24} />
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                3
              </span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              <a href="/" className="block px-3 py-2 text-gray-700 hover:text-gray-900">Home</a>
              <a href="/products" className="block px-3 py-2 text-gray-700 hover:text-gray-900">Products</a>
              <a href="/lists" className="block px-3 py-2 text-gray-700 hover:text-gray-900">Lists</a>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
```

### **2. Product Card Component**

```typescript
// src/components/features/products/ProductCard.tsx
import { Product } from '@/types/api';
import { Heart, ShoppingCart } from 'lucide-react';

interface ProductCardProps {
  product: Product;
  onAddToCart: (product: Product) => void;
  onToggleFavorite: (productId: number) => void;
  isFavorite?: boolean;
}

export const ProductCard = ({ 
  product, 
  onAddToCart, 
  onToggleFavorite, 
  isFavorite = false 
}: ProductCardProps) => {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      {/* Product Image */}
      <div className="relative aspect-square">
        <img
          src={product.image_versions.thumbnail}
          alt={product.nume}
          className="w-full h-full object-cover"
        />
        <button
          onClick={() => onToggleFavorite(product.id)}
          className="absolute top-2 right-2 p-1 bg-white rounded-full shadow-sm hover:bg-gray-50"
        >
          <Heart 
            size={20} 
            className={isFavorite ? 'fill-red-500 text-red-500' : 'text-gray-400'} 
          />
        </button>
      </div>

      {/* Product Info */}
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 mb-2">{product.nume}</h3>
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {product.description}
        </p>
        
        {/* Price and Quantity */}
        <div className="flex justify-between items-center mb-3">
          <span className="text-lg font-bold text-gray-900">
            {product.pret / 100} RON
          </span>
          <span className="text-sm text-gray-500">
            {product.cantitate} {product.unitati_id}
          </span>
        </div>

        {/* Add to Cart Button */}
        <button
          onClick={() => onAddToCart(product)}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
        >
          <ShoppingCart size={16} />
          Add to Cart
        </button>
      </div>
    </div>
  );
};
```

### **3. Image Upload Component**

```typescript
// src/components/forms/ImageUpload.tsx
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X } from 'lucide-react';

interface ImageUploadProps {
  onUpload: (files: File[]) => void;
  maxFiles?: number;
  acceptedTypes?: string[];
}

export const ImageUpload = ({ 
  onUpload, 
  maxFiles = 5, 
  acceptedTypes = ['image/jpeg', 'image/png', 'image/gif'] 
}: ImageUploadProps) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    onUpload(acceptedFiles);
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedTypes.reduce((acc, type) => ({ ...acc, [type]: [] }), {}),
    maxFiles,
    maxSize: 5 * 1024 * 1024, // 5MB
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
        isDragActive 
          ? 'border-blue-400 bg-blue-50' 
          : 'border-gray-300 hover:border-gray-400'
      }`}
    >
      <input {...getInputProps()} />
      <Upload size={48} className="mx-auto text-gray-400 mb-4" />
      {isDragActive ? (
        <p className="text-blue-600">Drop the files here...</p>
      ) : (
        <div>
          <p className="text-gray-600 mb-2">
            Drag & drop images here, or click to select
          </p>
          <p className="text-sm text-gray-500">
            Supports: JPEG, PNG, GIF (max 5MB each)
          </p>
        </div>
      )}
    </div>
  );
};
```

## 🔄 **State Management**

### **1. Zustand Store for Cart**

```typescript
// src/stores/cartStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Product } from '@/types/api';

interface CartItem {
  product: Product;
  quantity: number;
}

interface CartStore {
  items: CartItem[];
  addItem: (product: Product, quantity?: number) => void;
  removeItem: (productId: number) => void;
  updateQuantity: (productId: number, quantity: number) => void;
  clearCart: () => void;
  getTotalItems: () => number;
  getTotalPrice: () => number;
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      items: [],
      
      addItem: (product, quantity = 1) => {
        set((state) => {
          const existingItem = state.items.find(item => item.product.id === product.id);
          
          if (existingItem) {
            return {
              items: state.items.map(item =>
                item.product.id === product.id
                  ? { ...item, quantity: item.quantity + quantity }
                  : item
              )
            };
          }
          
          return {
            items: [...state.items, { product, quantity }]
          };
        });
      },
      
      removeItem: (productId) => {
        set((state) => ({
          items: state.items.filter(item => item.product.id !== productId)
        }));
      },
      
      updateQuantity: (productId, quantity) => {
        set((state) => ({
          items: state.items.map(item =>
            item.product.id === productId
              ? { ...item, quantity: Math.max(0, quantity) }
              : item
          ).filter(item => item.quantity > 0)
        }));
      },
      
      clearCart: () => {
        set({ items: [] });
      },
      
      getTotalItems: () => {
        return get().items.reduce((total, item) => total + item.quantity, 0);
      },
      
      getTotalPrice: () => {
        return get().items.reduce((total, item) => {
          return total + (item.product.pret * item.quantity);
        }, 0);
      }
    }),
    {
      name: 'cart-storage',
    }
  )
);
```

### **2. TanStack Query for API State**

```typescript
// src/hooks/useProducts.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productsApi } from '@/services/products';
import { Product } from '@/types/api';

export const useProducts = (params?: {
  skip?: number;
  limit?: number;
  include_deleted?: boolean;
  category_id?: number;
}) => {
  return useQuery({
    queryKey: ['products', params],
    queryFn: () => productsApi.getProducts(params),
  });
};

export const useProduct = (id: number, include_deleted = false) => {
  return useQuery({
    queryKey: ['product', id, include_deleted],
    queryFn: () => productsApi.getProduct(id, include_deleted),
    enabled: !!id,
  });
};

export const useCreateProduct = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: FormData) => productsApi.createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
};

export const useUpdateProduct = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: FormData }) =>
      productsApi.updateProduct(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['product', id] });
    },
  });
};
```

## 📱 **Mobile-First Features**

### **1. Responsive Product Grid**

```typescript
// src/components/features/products/ProductGrid.tsx
import { Product } from '@/types/api';
import { ProductCard } from './ProductCard';

interface ProductGridProps {
  products: Product[];
  onAddToCart: (product: Product) => void;
}

export const ProductGrid = ({ products, onAddToCart }: ProductGridProps) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {products.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          onAddToCart={onAddToCart}
        />
      ))}
    </div>
  );
};
```

### **2. Mobile-Optimized Forms**

```typescript
// src/components/forms/ProductForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const productSchema = z.object({
  nume: z.string().min(1, 'Name is required'),
  cantitate: z.number().min(1, 'Quantity must be at least 1'),
  pret: z.number().min(0.01, 'Price must be greater than 0'),
  description: z.string().optional(),
  category_id: z.number().min(1, 'Category is required'),
  unitati_id: z.number().min(1, 'Unit is required'),
});

type ProductFormData = z.infer<typeof productSchema>;

export const ProductForm = ({ 
  initialData, 
  onSubmit, 
  isLoading = false 
}: {
  initialData?: Partial<ProductFormData>;
  onSubmit: (data: ProductFormData) => void;
  isLoading?: boolean;
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: initialData,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Name Field */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Product Name
        </label>
        <input
          {...register('nume')}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter product name"
        />
        {errors.nume && (
          <p className="mt-1 text-sm text-red-600">{errors.nume.message}</p>
        )}
      </div>

      {/* Price and Quantity Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Price (RON)
          </label>
          <input
            type="number"
            step="0.01"
            {...register('pret', { valueAsNumber: true })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="0.00"
          />
          {errors.pret && (
            <p className="mt-1 text-sm text-red-600">{errors.pret.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Quantity
          </label>
          <input
            type="number"
            {...register('cantitate', { valueAsNumber: true })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="1"
          />
          {errors.cantitate && (
            <p className="mt-1 text-sm text-red-600">{errors.cantitate.message}</p>
          )}
        </div>
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          {...register('description')}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter product description"
        />
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Saving...' : 'Save Product'}
      </button>
    </form>
  );
};
```

## 🎨 **Styling with Tailwind CSS**

### **1. Tailwind Configuration**

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```

### **2. Global Styles**

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    font-family: 'Inter', system-ui, sans-serif;
  }
  
  body {
    @apply bg-gray-50 text-gray-900;
  }
}

@layer components {
  .btn-primary {
    @apply bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors;
  }
  
  .btn-secondary {
    @apply bg-gray-200 text-gray-900 px-4 py-2 rounded-md hover:bg-gray-300 transition-colors;
  }
  
  .input-field {
    @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500;
  }
}
```

## 🔧 **Development Setup**

### **1. Environment Variables**

```bash
# .env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Online Shop
```

### **2. Vite Configuration**

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0', // Required for Docker
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### **3. Development Workflow**

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f frontend-dev

# Access container for debugging
docker-compose -f docker-compose.dev.yml exec frontend-dev sh

# Install new dependencies (if needed)
docker-compose -f docker-compose.dev.yml exec frontend-dev npm install package-name

# Run linting
docker-compose -f docker-compose.dev.yml exec frontend-dev npm run lint

# Type checking
docker-compose -f docker-compose.dev.yml exec frontend-dev npm run type-check
```

## 🚀 **Deployment Considerations**

### **1. Production Docker Setup**

```dockerfile
# Dockerfile.prod (optimized for production)
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

        # Handle client-side routing
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### **2. Production Docker Compose**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: online_shop_frontend_prod
    restart: always
    ports:
      - "80:80"
    environment:
      - VITE_API_URL=http://localhost:8000
```

### **3. Environment-Specific Configuration**

```typescript
// src/config/environment.ts
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  appName: import.meta.env.VITE_APP_NAME || 'Online Shop',
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
};
```

### **4. Deployment Commands**

```bash
# Development deployment
docker-compose -f docker-compose.dev.yml up --build -d

# Production deployment
docker-compose -f docker-compose.prod.yml up --build -d

# Stop all services
docker-compose -f docker-compose.prod.yml down

# View production logs
docker-compose -f docker-compose.prod.yml logs -f frontend

# Update production deployment
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up --build -d
```

## 📋 **Implementation Checklist**

### **Phase 1: Foundation**
- [ ] Set up React + TypeScript + Vite project
- [ ] Create Docker configuration (Dockerfile, docker-compose.yml)
- [ ] Configure Tailwind CSS
- [ ] Set up React Router
- [ ] Configure TanStack Query
- [ ] Set up Zustand stores
- [ ] Create basic layout components
- [ ] Test Docker development environment

### **Phase 2: Core Features**
- [ ] Implement product listing and details
- [ ] Create category management
- [ ] Build image upload functionality
- [ ] Implement list management
- [ ] Add cart functionality
- [ ] Test all features in Docker environment

### **Phase 3: Admin Interface**
- [ ] Create admin dashboard
- [ ] Build product management forms
- [ ] Implement category management
- [ ] Add list publishing functionality
- [ ] Create order management
- [ ] Ensure admin features work in containerized environment

### **Phase 4: Customer Interface**
- [ ] Build product catalog
- [ ] Implement shopping cart
- [ ] Create checkout process
- [ ] Add order tracking
- [ ] Implement mobile optimizations
- [ ] Test customer interface in Docker

### **Phase 5: Polish & Production**
- [ ] Add loading states
- [ ] Implement error handling
- [ ] Add animations and transitions
- [ ] Optimize performance
- [ ] Add PWA features
- [ ] Create production Docker configuration
- [ ] Test production deployment
- [ ] Set up CI/CD pipeline for Docker builds

## 🎯 **Key Benefits of This Stack**

1. **Type Safety**: End-to-end TypeScript integration with your FastAPI backend
2. **Performance**: Vite provides fast development and optimized builds
3. **Developer Experience**: Excellent tooling and debugging capabilities
4. **Mobile-First**: Responsive design that works great on mobile devices
5. **Scalability**: Modular architecture that grows with your business
6. **Maintainability**: Clean code structure with clear separation of concerns

This technology stack is specifically chosen to work seamlessly with your FastAPI backend and provide the best development experience for building a modern, mobile-first e-commerce application. 