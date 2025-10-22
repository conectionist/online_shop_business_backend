# Frontend Guide: Admin Push Topics, Broadcast, and TTL

This guide explains how a frontend (admin UI) can integrate with the backend push notification features implemented today: admin-only topic subscriptions, topic-aware broadcast, automatic business triggers, and optional TTL.

## Overview

- Admin-only subscriptions: public subscribe is gated by config and off by default
- Topics: subscribe admin devices to topics (e.g., `admin_login`, `list_published`)
- Automatic triggers:
  - Successful admin login → sends `admin_login` topic notification
  - List marked as published → sends `list_published` topic notification
- Broadcast endpoint (admin only): send to a specific topic, or to all active subscriptions
- Optional TTL: control push expiry via `ttl_seconds`

## Prerequisites

- Backend running at `/api/v1`
- Admin credentials (JWT-based auth)
- Service worker set up (HTTPS in production)

## Endpoints Added/Relevant

- GET `/api/v1/push/public-key` → VAPID public key
- POST `/api/v1/push/admin/subscribe` → create admin subscription
- GET `/api/v1/push/topics` → list topics (admin only)
- POST `/api/v1/push/topics/subscribe` → subscribe a `subscription_id` to topics (admin only)
- DELETE `/api/v1/push/topics/subscribe` → unsubscribe (admin only)
- POST `/api/v1/push/broadcast?topic=optional` → topic-aware broadcast (admin only)

Existing admin send endpoints (unchanged):
- POST `/api/v1/push/admin/notify` → all admins
- POST `/api/v1/push/admin/notify/{admin_id}` → specific admin

## Public Subscribe Gating

- Env flag: `ALLOW_PUBLIC_PUSH_SUBSCRIBE` (default: false)
- When `false`, `POST /push/subscribe` returns 403 (disabled). Use admin subscribe only.

## Topics

Initial topics seeded:
- `admin_login` → fired when any admin logs in
- `new_order` → reserved for future order-flow triggers
- `list_published` → fired when a list becomes published (create/update)

### List Topics (admin)

```bash
curl -sS \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/push/topics | jq
# [{ "id": 1, "name": "admin_login", ... }, ...]
```

### Subscribe a Device to Topics (admin)

1) Create an admin subscription using a real PushSubscription (see JS below). For testing without real push, you can use dummy keys to create a DB row.

```bash
SUB_ID=$(curl -sS -X POST http://localhost:8000/api/v1/push/admin/subscribe \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "endpoint": "https://example.com/fake", 
    "keys": {"p256dh": "dummy", "auth": "dummy"},
    "user_agent": "AdminApp/1.0"
  }' | jq -r .id)
```

2) Subscribe it to topics by ID (e.g., `admin_login` and `list_published`).

```bash
curl -sS -X POST http://localhost:8000/api/v1/push/topics/subscribe \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"subscription_id": '$SUB_ID', "topic_ids": [<ADMIN_LOGIN_ID>, <LIST_PUBLISHED_ID>] }'
```

3) Unsubscribe similarly via DELETE.

```bash
curl -sS -X DELETE http://localhost:8000/api/v1/push/topics/subscribe \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"subscription_id": '$SUB_ID', "topic_ids": [<ADMIN_LOGIN_ID>] }'
```

## Admin Subscribe Flow (Frontend)

### 1) Get VAPID Public Key

```javascript
async function getVapidPublicKey() {
  const res = await fetch('/api/v1/push/public-key');
  const data = await res.json();
  return data.publicKey; // Base64URL-encoded
}
```

### 2) Request Permission and Register Service Worker

```javascript
function isPushSupported() {
  return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
}

async function requestPermission() {
  if (Notification.permission === 'granted') return true;
  if (Notification.permission === 'denied') return false;
  const perm = await Notification.requestPermission();
  return perm === 'granted';
}

// Register once at app bootstrap
navigator.serviceWorker.register('/sw.js');
```

### 3) Subscribe and Send to Backend (Admin)

```javascript
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
  return outputArray;
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
  return window.btoa(binary);
}

async function subscribeAdminPush(adminToken) {
  if (!isPushSupported()) throw new Error('Push not supported');
  const ok = await requestPermission();
  if (!ok) throw new Error('Permission denied');

  const registration = await navigator.serviceWorker.ready;
  const vapidKey = await getVapidPublicKey();
  const applicationServerKey = urlBase64ToUint8Array(vapidKey);

  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey
  });

  const body = {
    endpoint: subscription.endpoint,
    keys: {
      p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
      auth: arrayBufferToBase64(subscription.getKey('auth'))
    },
    user_agent: navigator.userAgent
  };

  const res = await fetch('/api/v1/push/admin/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${adminToken}` },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error('Admin subscribe failed');
  return await res.json(); // { id, endpoint, is_active }
}
```

### 4) Subscribe the New Subscription to Topics (Admin)

Store the returned `id` (subscription_id) and then call the topics subscribe endpoint.

```javascript
async function subscribeToTopics(adminToken, subscriptionId, topicIds) {
  const res = await fetch('/api/v1/push/topics/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${adminToken}` },
    body: JSON.stringify({ subscription_id: subscriptionId, topic_ids: topicIds })
  });
  if (!res.ok) throw new Error('Topic subscribe failed');
  return await res.json(); // { created: n }
}
```

## Broadcast (Admin)

Topic-aware send:

```bash
curl -sS -X POST "http://localhost:8000/api/v1/push/broadcast?topic=admin_login" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "title":"Ops Alert",
    "body":"This is a topic broadcast",
    "event_id":"ops_alert_1",
    "ttl_seconds": 180
  }'
```

To broadcast to all active subscriptions (both customer and admin, if enabled), omit `topic`:

```bash
curl -sS -X POST http://localhost:8000/api/v1/push/broadcast \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Hello","body":"Everyone","event_id":"hello_all"}'
```

## Service Worker Example (`sw.js`)

```javascript
self.addEventListener('push', (event) => {
  if (!event.data) return;
  const data = event.data.json();
  const options = {
    body: data.body,
    icon: data.icon || '/icon-192x192.png',
    tag: data.tag,
    data: data.data,
  };
  event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action === 'open' || !event.action) {
    event.waitUntil(clients.openWindow('/'));
  }
});
```

## Automatic Business Triggers

- Admin login → backend schedules a background send to `admin_login` subscribers
- List published (`is_published=true` on create/update) → backend sends to `list_published` subscribers

These are server-driven; the frontend only needs to be subscribed to the topic.

## TTL (Expiration)

Include `ttl_seconds` in `SendNotificationRequest` when calling admin endpoints or broadcast. The backend forwards this to the push service as TTL.

Ranges: 1..86400 seconds.

## Testing Tips

- Without real VAPID keys and real endpoints, network sends will fail; use container logs to verify flows:

```bash
docker compose logs api --no-log-prefix --tail 200 | egrep "Topic send complete|Admin broadcast|Prune pass|Push failed|VAPID"
```

- E2E testing requires:
  - Generate VAPID keys and configure env (`VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`); rebuild containers
  - Register service worker and create a real PushSubscription in the browser
  - Use admin subscribe and topics subscribe as shown above

## Security Notes

- Topics endpoints are admin-only and require that `subscription_id` belongs to the authenticated admin
- Public subscribe is disabled by default; use admin subscribe for admin devices
- Never expose `VAPID_PRIVATE_KEY` to the frontend; only the public key is shared

---
This guide complements the existing `FRONTEND_PUSH_NOTIFICATIONS_GUIDE.md` by adding topics, broadcast, and TTL usage for the admin app.
