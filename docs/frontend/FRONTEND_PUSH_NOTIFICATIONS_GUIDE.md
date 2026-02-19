# Frontend Push Notifications Integration Guide

This guide explains how to integrate push notifications into your frontend application using the backend API.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [API Endpoints](#api-endpoints)
- [Frontend Implementation](#frontend-implementation)
- [Service Worker Setup](#service-worker-setup)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Production Considerations](#production-considerations)

## Overview

The backend provides a complete push notification system with:
- VAPID key management
- Subscription management (subscribe/unsubscribe)
- Server-side deduplication
- Admin test endpoint
- Automatic cleanup of inactive subscriptions

## Prerequisites

1. **HTTPS Required**: Push notifications only work over HTTPS (except localhost)
2. **Service Worker**: Required for receiving push notifications
3. **User Permission**: Browser will prompt user for notification permission
4. **Modern Browser**: Support for Push API and Service Workers

## API Endpoints

### Base URL
```
/api/v1/push
```

### 1. Get VAPID Public Key
```http
GET /api/v1/push/public-key
```

**Response:**
```json
{
  "publicKey": "BOe2k7srNl1rTt1y_1l3VBo3qk4n6B1k9E9oV8zqj5sRrVg6q1bK42NzfQ9oYd0z7qf6e5XjT1dD2C3B4A5c6dE"
}
```

### 2. Customer Push Notifications

#### Subscribe to Customer Notifications
```http
POST /api/v1/push/subscribe
Content-Type: application/json
```

**Request Body:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "BEl62iUYgUivxIkv69yViEuiBIa40HI...",
    "auth": "tBHItJI5svbpez7KI4CCXg=="
  },
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

**Response:**
```json
{
  "id": 123,
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "is_active": true
}
```

**Note:** No authentication required for customer subscriptions.

### 3. Admin Push Notifications

#### Subscribe to Admin Notifications
```http
POST /api/v1/push/admin/subscribe
Content-Type: application/json
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "BEl62iUYgUivxIkv69yViEuiBIa40HI...",
    "auth": "tBHItJI5svbpez7KI4CCXg=="
  },
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

**Response:**
```json
{
  "id": 124,
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "is_active": true
}
```

**Note:** Admin authentication required. Subscription will be associated with the authenticated admin user.

#### Send Notifications to All Admins
```http
POST /api/v1/push/admin/notify
Content-Type: application/json
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "title": "System Alert",
  "body": "Database maintenance scheduled for tonight",
  "data": {
    "type": "system_alert",
    "priority": "high"
  },
  "icon": "/icons/alert.png",
  "tag": "system_maintenance"
}
```

**Response:**
```json
{
  "status": "queued"
}
```

#### Send Notifications to Specific Admin
```http
POST /api/v1/push/admin/notify/{admin_id}
Content-Type: application/json
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "title": "Order Alert",
  "body": "New order #12345 received",
  "data": {
    "type": "order_alert",
    "order_id": "12345"
  },
  "icon": "/icons/order.png",
  "tag": "order_12345"
}
```

**Response:**
```json
{
  "status": "queued"
}
```

### 4. Unsubscribe from Push Notifications
```http
DELETE /api/v1/push/subscribe?endpoint=https://fcm.googleapis.com/fcm/send/...
```

**Response:**
```json
{
  "status": "deactivated"
}
```

**Note:** Works for both customer and admin subscriptions.

## Frontend Implementation

### 1. Check Browser Support

```javascript
function isPushSupported() {
  return 'serviceWorker' in navigator && 
         'PushManager' in window && 
         'Notification' in window;
}

if (!isPushSupported()) {
  console.log('Push notifications not supported');
  return;
}
```

### 2. Request Permission

```javascript
async function requestNotificationPermission() {
  if (Notification.permission === 'granted') {
    return true;
  }
  
  if (Notification.permission === 'denied') {
    console.log('Notifications blocked by user');
    return false;
  }
  
  const permission = await Notification.requestPermission();
  return permission === 'granted';
}
```

### 3. Get VAPID Public Key

```javascript
async function getVapidPublicKey() {
  try {
    const response = await fetch('/api/v1/push/public-key');
    const data = await response.json();
    return data.publicKey;
  } catch (error) {
    console.error('Failed to get VAPID public key:', error);
    throw error;
  }
}
```

### 4. Subscribe to Customer Push Notifications

```javascript
async function subscribeToCustomerPush() {
  try {
    // Get VAPID public key
    const vapidPublicKey = await getVapidPublicKey();
    
    // Convert VAPID key to Uint8Array
    const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);
    
    // Subscribe to push service
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: applicationServerKey
    });
    
    // Send subscription to backend (customer endpoint)
    const response = await fetch('/api/v1/push/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        endpoint: subscription.endpoint,
        keys: {
          p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
          auth: arrayBufferToBase64(subscription.getKey('auth'))
        },
        user_agent: navigator.userAgent
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('Successfully subscribed to customer notifications:', result);
      return result;
    } else {
      throw new Error(`Customer subscription failed: ${response.status}`);
    }
  } catch (error) {
    console.error('Customer push subscription failed:', error);
    throw error;
  }
}
```

### 5. Subscribe to Admin Push Notifications

```javascript
async function subscribeToAdminPush(adminToken) {
  try {
    // Get VAPID public key
    const vapidPublicKey = await getVapidPublicKey();
    
    // Convert VAPID key to Uint8Array
    const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);
    
    // Subscribe to push service
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: applicationServerKey
    });
    
    // Send subscription to backend (admin endpoint)
    const response = await fetch('/api/v1/push/admin/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminToken}`
      },
      body: JSON.stringify({
        endpoint: subscription.endpoint,
        keys: {
          p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
          auth: arrayBufferToBase64(subscription.getKey('auth'))
        },
        user_agent: navigator.userAgent
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('Successfully subscribed to admin notifications:', result);
      return result;
    } else {
      throw new Error(`Admin subscription failed: ${response.status}`);
    }
  } catch (error) {
    console.error('Admin push subscription failed:', error);
    throw error;
  }
}

// Helper functions
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');
  
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}
```

### 5. Unsubscribe from Push Notifications

```javascript
async function unsubscribeFromPush() {
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    
    if (subscription) {
      // Unsubscribe from push service
      await subscription.unsubscribe();
      
      // Notify backend
      const response = await fetch(`/api/v1/push/subscribe?endpoint=${encodeURIComponent(subscription.endpoint)}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        console.log('Successfully unsubscribed');
        return true;
      } else {
        console.error('Backend unsubscribe failed:', response.status);
        return false;
      }
    }
  } catch (error) {
    console.error('Unsubscribe failed:', error);
    throw error;
  }
}
```

### 6. Check Subscription Status

```javascript
async function getSubscriptionStatus() {
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    return !!subscription;
  } catch (error) {
    console.error('Failed to check subscription status:', error);
    return false;
  }
}
```

## Service Worker Setup

### 1. Create Service Worker File (`sw.js`)

```javascript
// sw.js
self.addEventListener('push', function(event) {
  console.log('Push event received:', event);
  
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: data.icon || '/icon-192x192.png',
      badge: '/badge-72x72.png',
      tag: data.tag,
      data: data.data,
      actions: [
        {
          action: 'open',
          title: 'Open App',
          icon: '/icon-192x192.png'
        },
        {
          action: 'close',
          title: 'Close',
          icon: '/icon-192x192.png'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

self.addEventListener('notificationclick', function(event) {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

self.addEventListener('notificationclose', function(event) {
  console.log('Notification closed:', event);
});
```

### 2. Register Service Worker

```javascript
// In your main app
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/sw.js')
      .then(function(registration) {
        console.log('ServiceWorker registration successful');
      })
      .catch(function(err) {
        console.log('ServiceWorker registration failed: ', err);
      });
  });
}
```

## Deduplication Strategy

### Server-Side Deduplication (Backend)
The backend automatically prevents duplicate notifications using `event_id`:
- Each notification request should include a unique `event_id`
- Backend stores sent notifications in `notification_log` table
- Same `event_id` + subscription = only sent once
- Use this for business events (e.g., "order_123_shipped", "user_456_login")

### Client-Side Deduplication (Frontend)
Use the `tag` parameter to replace notifications with the same tag:
- Browser automatically replaces notifications with identical `tag`
- Use for UI state updates (e.g., "new_message", "order_status")
- Different from `event_id` - `tag` controls display behavior

### Example Implementation

```javascript
// Backend sends notification with both event_id and tag
const notificationPayload = {
  title: "Order Shipped",
  body: "Your order #12345 has been shipped",
  data: { orderId: "12345", status: "shipped" },
  icon: "/icons/shipped.png",
  tag: "order_12345",           // Client-side: replaces previous order notifications
  event_id: "order_12345_shipped" // Server-side: prevents duplicate sends
};

// Service worker handles tag-based replacement
self.addEventListener('push', function(event) {
  const data = event.data.json();
  
  // Browser automatically replaces notifications with same tag
  const options = {
    body: data.body,
    icon: data.icon,
    tag: data.tag,        // This enables client-side deduplication
    data: data.data
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});
```

### Best Practices

1. **Use `event_id` for business logic**: Prevents server from sending duplicate notifications
2. **Use `tag` for UI behavior**: Controls which notifications replace each other
3. **Combine both**: Most notifications should have both parameters
4. **Make tags meaningful**: Use consistent naming (e.g., "order_{id}", "message_{conversationId}")

### Common Patterns

```javascript
// Order notifications - replace previous order updates
{
  tag: "order_12345",
  event_id: "order_12345_status_changed_" + Date.now()
}

// Chat messages - replace previous message notifications
{
  tag: "chat_room_456",
  event_id: "message_789_sent"
}

// System alerts - each is unique
{
  tag: "system_alert_" + Date.now(),
  event_id: "system_maintenance_" + Date.now()
}
```

## Error Handling

### Common Error Scenarios

1. **Permission Denied**
```javascript
if (Notification.permission === 'denied') {
  // Show UI to guide user to browser settings
  showPermissionDeniedMessage();
}
```

2. **Network Errors**
```javascript
try {
  await subscribeToPush();
} catch (error) {
  if (error.name === 'NetworkError') {
    showNetworkErrorMessage();
  } else {
    showGenericErrorMessage();
  }
}
```

3. **Subscription Failed**
```javascript
try {
  const result = await subscribeToPush();
  if (!result.is_active) {
    console.log('Subscription created but inactive');
  }
} catch (error) {
  console.error('Subscription failed:', error);
}
```

## Testing

### 1. Test Subscription Flow

```javascript
async function testPushNotifications() {
  try {
    // Check support
    if (!isPushSupported()) {
      throw new Error('Push not supported');
    }
    
    // Request permission
    const hasPermission = await requestNotificationPermission();
    if (!hasPermission) {
      throw new Error('Permission denied');
    }
    
    // Subscribe
    const subscription = await subscribeToPush();
    console.log('Test subscription successful:', subscription);
    
    // Test notification (if you have admin access)
    // This would typically be done from backend admin panel
    
  } catch (error) {
    console.error('Test failed:', error);
  }
}
```

### 2. Manual Testing

1. Open browser dev tools
2. Go to Application tab → Service Workers
3. Check if service worker is registered
4. Go to Application tab → Storage → Notifications
5. Verify subscription is stored

## Production Considerations

### 1. PWA Manifest

Add to your `manifest.json`:

```json
{
  "name": "Your App Name",
  "short_name": "App",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "icons": [
    {
      "src": "/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### 2. User Experience

- **Progressive Enhancement**: Make push notifications optional
- **Clear UI**: Show subscription status and controls
- **Permission Handling**: Guide users through permission process
- **Fallback**: Provide alternative notification methods

### 3. Security

- **HTTPS Only**: Push notifications require secure context
- **VAPID Keys**: Never expose private keys to frontend
- **Validation**: Always validate subscription data

### 4. Performance

- **Lazy Loading**: Only load push code when needed
- **Error Recovery**: Handle subscription failures gracefully
- **Cleanup**: Unsubscribe when user logs out

## Admin Notification Management

### Send Notifications from Frontend (Admin Panel)

```javascript
// Send notification to all admins
async function notifyAllAdmins(adminToken, notification) {
  try {
    const response = await fetch('/api/v1/push/admin/notify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminToken}`
      },
      body: JSON.stringify(notification)
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('Admin notification queued:', result);
      return result;
    } else {
      throw new Error(`Admin notification failed: ${response.status}`);
    }
  } catch (error) {
    console.error('Failed to send admin notification:', error);
    throw error;
  }
}

// Send notification to specific admin
async function notifySpecificAdmin(adminToken, adminId, notification) {
  try {
    const response = await fetch(`/api/v1/push/admin/notify/${adminId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminToken}`
      },
      body: JSON.stringify(notification)
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('Admin notification queued:', result);
      return result;
    } else {
      throw new Error(`Admin notification failed: ${response.status}`);
    }
  } catch (error) {
    console.error('Failed to send admin notification:', error);
    throw error;
  }
}

// Example usage
const orderAlert = {
  title: "New Order Received",
  body: "Order #12345 has been placed",
  data: {
    type: "order_alert",
    order_id: "12345",
    customer: "John Doe"
  },
  icon: "/icons/order.png",
  tag: "order_12345"
};

// Notify all admins
await notifyAllAdmins(adminToken, orderAlert);

// Notify specific admin
await notifySpecificAdmin(adminToken, 1, orderAlert);
```

## Example Integration

### Customer Push Notification Manager

```javascript
class CustomerPushNotificationManager {
  constructor() {
    this.isSupported = isPushSupported();
    this.isSubscribed = false;
  }
  
  async init() {
    if (!this.isSupported) return false;
    
    const hasPermission = await requestNotificationPermission();
    if (!hasPermission) return false;
    
    this.isSubscribed = await getSubscriptionStatus();
    return true;
  }
  
  async subscribe() {
    if (!this.isSupported) throw new Error('Not supported');
    
    const result = await subscribeToCustomerPush();
    this.isSubscribed = true;
    return result;
  }
  
  async unsubscribe() {
    if (!this.isSupported) return false;
    
    const success = await unsubscribeFromPush();
    this.isSubscribed = false;
    return success;
  }
  
  getStatus() {
    return {
      supported: this.isSupported,
      subscribed: this.isSubscribed,
      permission: Notification.permission
    };
  }
}
```

### Admin Push Notification Manager

```javascript
class AdminPushNotificationManager {
  constructor(adminToken) {
    this.isSupported = isPushSupported();
    this.isSubscribed = false;
    this.adminToken = adminToken;
  }
  
  async init() {
    if (!this.isSupported) return false;
    
    const hasPermission = await requestNotificationPermission();
    if (!hasPermission) return false;
    
    this.isSubscribed = await getSubscriptionStatus();
    return true;
  }
  
  async subscribe() {
    if (!this.isSupported) throw new Error('Not supported');
    if (!this.adminToken) throw new Error('Admin token required');
    
    const result = await subscribeToAdminPush(this.adminToken);
    this.isSubscribed = true;
    return result;
  }
  
  async unsubscribe() {
    if (!this.isSupported) return false;
    
    const success = await unsubscribeFromPush();
    this.isSubscribed = false;
    return success;
  }
  
  async notifyAllAdmins(notification) {
    if (!this.adminToken) throw new Error('Admin token required');
    return await notifyAllAdmins(this.adminToken, notification);
  }
  
  async notifySpecificAdmin(adminId, notification) {
    if (!this.adminToken) throw new Error('Admin token required');
    return await notifySpecificAdmin(this.adminToken, adminId, notification);
  }
  
  getStatus() {
    return {
      supported: this.isSupported,
      subscribed: this.isSubscribed,
      permission: Notification.permission,
      hasAdminToken: !!this.adminToken
    };
  }
}
```

### Usage Examples

```javascript
// Customer usage
const customerPushManager = new CustomerPushNotificationManager();
await customerPushManager.init();

document.getElementById('subscribe-customer-btn').addEventListener('click', async () => {
  try {
    await customerPushManager.subscribe();
    console.log('Subscribed to customer notifications');
  } catch (error) {
    console.error('Customer subscription failed:', error);
  }
});

// Admin usage
const adminToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
const adminPushManager = new AdminPushNotificationManager(adminToken);
await adminPushManager.init();

document.getElementById('subscribe-admin-btn').addEventListener('click', async () => {
  try {
    await adminPushManager.subscribe();
    console.log('Subscribed to admin notifications');
  } catch (error) {
    console.error('Admin subscription failed:', error);
  }
});

// Send admin notification
document.getElementById('send-alert-btn').addEventListener('click', async () => {
  try {
    await adminPushManager.notifyAllAdmins({
      title: "System Alert",
      body: "Database maintenance scheduled",
      data: { type: "system_alert" }
    });
    console.log('Admin notification sent');
  } catch (error) {
    console.error('Failed to send admin notification:', error);
  }
});
```

## Dual Subscription Scenarios

### Admin Who Also Wants Customer Notifications

In some cases, an admin might want to receive both admin notifications (order alerts, system alerts) and customer notifications (promotions, general updates). Here's how to handle this:

```javascript
class DualPushNotificationManager {
  constructor(adminToken) {
    this.isSupported = isPushSupported();
    this.customerSubscribed = false;
    this.adminSubscribed = false;
    this.adminToken = adminToken;
  }
  
  async init() {
    if (!this.isSupported) return false;
    
    const hasPermission = await requestNotificationPermission();
    if (!hasPermission) return false;
    
    // Check both subscription types
    this.customerSubscribed = await this.getCustomerSubscriptionStatus();
    this.adminSubscribed = await this.getAdminSubscriptionStatus();
    return true;
  }
  
  async subscribeToCustomer() {
    if (!this.isSupported) throw new Error('Not supported');
    
    const result = await subscribeToCustomerPush();
    this.customerSubscribed = true;
    return result;
  }
  
  async subscribeToAdmin() {
    if (!this.isSupported) throw new Error('Not supported');
    if (!this.adminToken) throw new Error('Admin token required');
    
    const result = await subscribeToAdminPush(this.adminToken);
    this.adminSubscribed = true;
    return result;
  }
  
  async subscribeToBoth() {
    const results = [];
    
    // Subscribe to customer notifications
    try {
      const customerResult = await this.subscribeToCustomer();
      results.push({ type: 'customer', result: customerResult });
    } catch (error) {
      console.error('Customer subscription failed:', error);
    }
    
    // Subscribe to admin notifications
    try {
      const adminResult = await this.subscribeToAdmin();
      results.push({ type: 'admin', result: adminResult });
    } catch (error) {
      console.error('Admin subscription failed:', error);
    }
    
    return results;
  }
  
  getStatus() {
    return {
      supported: this.isSupported,
      customerSubscribed: this.customerSubscribed,
      adminSubscribed: this.adminSubscribed,
      permission: Notification.permission,
      hasAdminToken: !!this.adminToken
    };
  }
}

// Usage for admin who wants both types
const dualManager = new DualPushNotificationManager(adminToken);
await dualManager.init();

// Subscribe to both types
document.getElementById('subscribe-both-btn').addEventListener('click', async () => {
  try {
    const results = await dualManager.subscribeToBoth();
    console.log('Subscription results:', results);
  } catch (error) {
    console.error('Dual subscription failed:', error);
  }
});
```

### Important Notes for Dual Subscriptions

1. **Same Browser Permission**: Both subscriptions use the same browser notification permission
2. **Different Database Records**: Creates separate subscription records (one with `user_id=NULL`, one with `user_id=admin_id`)
3. **Targeted Notifications**: 
   - Customer notifications go to `user_id=NULL` subscriptions
   - Admin notifications go to `user_id=admin_id` subscriptions
4. **Same Device**: Both notifications appear on the same device, but are targeted differently

## Troubleshooting

### Common Issues

1. **"Push subscription failed"**
   - Check if VAPID public key is correctly retrieved
   - Verify service worker is registered
   - Check browser console for errors

2. **"Notifications not showing"**
   - Verify service worker is active
   - Check notification permission
   - Test with browser dev tools

3. **"Subscription not persisting"**
   - Check backend API responses
   - Verify database connection
   - Check for CORS issues

### Debug Tools

- Browser Dev Tools → Application → Service Workers
- Browser Dev Tools → Application → Storage → Notifications
- Network tab to monitor API calls
- Console for error messages

---

This guide provides everything needed to integrate push notifications into your frontend application. The backend API is designed to be simple and reliable, with proper error handling and deduplication built-in.
