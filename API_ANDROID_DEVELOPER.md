# Financius Android API Documentation

**Version:** 1.0.0  
**Last Updated:** May 17, 2026  
**Base URL:** `https://api.financius.com` (or `http://localhost:5000` for local development)

----

## Table of Contents

1. [Authentication](#authentication)
2. [Device Pairing](#device-pairing)
3. [Data Sync](#data-sync)
4. [Error Handling](#error-handling)
5. [Data Models](#data-models)
6. [Examples](#examples)
7. [Best Practices](#best-practices)

----

## Authentication

### Registration

Register a new user account.

**Endpoint:** `POST /api/v1/auth/register`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

**Response (201 Created):**
```json
{
  "data": {
    "user": {
      "id": "user@example.com",
      "email": "user@example.com"
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600
  },
  "error": null,
  "meta": {
    "requestId": "abc-123-def"
  }
}
```

**Error (409 Conflict - Email already registered):**
```json
{
  "data": null,
  "error": {
    "code": "duplicate_email",
    "message": "Email already registered"
  },
  "meta": {
    "requestId": "abc-123-def"
  }
}
```

### Login

Authenticate with email and password.

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

**Response (200 OK):**
```json
{
  "data": {
    "user": {
      "id": "user@example.com",
      "email": "user@example.com"
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600
  },
  "error": null,
  "meta": {
    "requestId": "abc-123-def"
  }
}
```

**Error (401 Unauthorized):**
```json
{
  "data": null,
  "error": {
    "code": "invalid_credentials",
    "message": "Invalid email or password"
  },
  "meta": {
    "requestId": "abc-123-def"
  }
}
```

### Token Management

- **Access Token:** Valid for 1 hour
- **Refresh Token:** Valid for 30 days
- Store both securely on the device
- Include access token in all authenticated requests via `Authorization: Bearer {token}` header

----

## Device Pairing

### Generate QR Code Token

Generate a pairing token to establish a new device connection.

**Endpoint:** `GET /api/v1/pairing/qr`

**Headers:**
```
Authorization: Bearer {accessToken}
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "data": {
    "qrPayload": {
      "serverBaseUrl": "https://api.financius.com",
      "pairingToken": "ZVF8fC5dGjkhobZAgd6_-2dwEqBZSrjj",
      "expiresAt": "2026-05-17T16:00:00+00:00"
    }
  },
  "error": null,
  "meta": {
    "requestId": "abc-123-def"
  }
}
```

### QR Code Payload Format

Embed this JSON in the QR code:
```json
{
  "serverBaseUrl": "https://api.financius.com",
  "pairingToken": "ZVF8fC5dGjkhobZAgd6_-2dwEqBZSrjj",
  "expiresAt": "2026-05-17T16:00:00+00:00"
}
```

**QR Code Lifetime:** 5 minutes (300 seconds)

----

## Data Sync

### Push Data (Sync Receipts, Categories, Shops, Cards)

Upload receipts, categories, shops, and payment cards from your device to the server.

**Endpoint:** `POST /api/v1/sync`

**Headers:**
```
Authorization: Bearer {accessToken}
Content-Type: application/json
```

**Request:**
```json
{
  "deviceId": "device-alice-pixel-6",
  "receipts": [
    {
      "externalId": "rcpt-20260517-001",
      "date": "2026-05-17T10:30:00Z",
      "shopExternalId": "shop-whole-foods-sf",
      "categoryExternalId": "cat-groceries",
      "paymentCardExternalId": "card-chase-001",
      "total": 45.50,
      "currency": "USD",
      "lineItems": [
        {
          "categoryId": "cat-groceries",
          "amount": 25.00,
          "qty": 1,
          "name": "Milk and Bread"
        },
        {
          "categoryId": "cat-drinks",
          "amount": 20.50,
          "qty": 2,
          "name": "Coffee"
        }
      ]
    }
  ],
  "categories": [
    {
      "externalId": "cat-groceries",
      "name": "Groceries",
      "icon": "🛒",
      "color": "#FF6B6B"
    },
    {
      "externalId": "cat-drinks",
      "name": "Beverages",
      "icon": "☕",
      "color": "#4ECDC4"
    }
  ],
  "shops": [
    {
      "externalId": "shop-whole-foods-sf",
      "name": "Whole Foods Market",
      "location": "San Francisco, CA",
      "latitude": 37.7749,
      "longitude": -122.4194
    }
  ],
  "cards": [
    {
      "externalId": "card-chase-001",
      "name": "Chase Sapphire",
      "lastFour": "4242",
      "issuer": "Visa"
    }
  ]
}
```

Notes:
- To have shop name appear in receipt APIs and analytics top-shops, include shop linkage on each receipt via shopExternalId.
- categoryExternalId and paymentCardExternalId are also supported for direct receipt linkage during sync.

**Response (200 OK):**
```json
{
  "data": {
    "accepted": {
      "receipts": 1,
      "categories": 2,
      "shops": 1,
      "cards": 1
    },
    "lastSyncAt": "2026-05-17T15:55:10.781858+00:00",
    "syncId": "92e67e2c-6654-4379-b9f4-8da2b1c99bc3"
  },
  "error": null,
  "meta": {
    "requestId": "abc-123-def"
  }
}
```

### Get Sync Status

Check the last sync timestamp and sync status.

**Endpoint:** `GET /api/v1/sync/status`

**Headers:**
```
Authorization: Bearer {accessToken}
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "data": {
    "lastSyncAt": "2026-05-17T15:55:10.781858+00:00",
    "status": "idle"
  },
  "error": null,
  "meta": {
    "requestId": "abc-123-def"
  }
}
```

----

## Error Handling

### Common HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | Success | Data synced, status retrieved |
| 201 | Created | User registered |
| 400 | Bad Request | Missing required fields |
| 401 | Unauthorized | Invalid token or invalid credentials |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Email already registered |
| 500 | Server Error | Internal server error |

### Error Response Format

All errors follow this envelope:
```json
{
  "data": null,
  "error": {
    "code": "error_code",
    "message": "Human-readable error message"
  },
  "meta": {
    "requestId": "unique-request-id-for-debugging"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_credentials` | 401 | Email/password mismatch |
| `duplicate_email` | 409 | Email already registered |
| `invalid_token` | 401 | Token expired or malformed |
| `user_not_found` | 404 | User doesn't exist |
| `internal_error` | 500 | Server error (contact support) |

----

## Data Models

### Receipt

```json
{
  "externalId": "rcpt-20260517-001",
  "date": "2026-05-17T10:30:00Z",
  "total": 45.50,
  "currency": "USD",
  "lineItems": [
    {
      "categoryId": "cat-groceries",
      "amount": 25.00,
      "qty": 1,
      "name": "Milk and Bread"
    }
  ]
}
```

**Fields:**
- `externalId` (string, required): Unique receipt ID on the device (for idempotency)
- `date` (ISO 8601 datetime, required): Receipt date/time in UTC
- `total` (number, required): Total amount
- `currency` (string): ISO 4217 code (default: USD)
- `lineItems` (array): Receipt line items

### Receipt Line Item

```json
{
  "categoryId": "cat-groceries",
  "amount": 25.00,
  "qty": 1,
  "name": "Milk and Bread"
}
```

**Fields:**
- `categoryId` (string, required): Reference to category externalId
- `amount` (number, required): Item amount
- `qty` (number): Quantity (default: 1)
- `name` (string): Item description

### Category

```json
{
  "externalId": "cat-groceries",
  "name": "Groceries",
  "icon": "🛒",
  "color": "#FF6B6B"
}
```

**Fields:**
- `externalId` (string, required): Unique category ID on the device
- `name` (string, required): Display name
- `icon` (string): Emoji or icon identifier
- `color` (string): Hex color code

### Shop

```json
{
  "externalId": "shop-whole-foods-sf",
  "name": "Whole Foods Market",
  "location": "San Francisco, CA",
  "latitude": 37.7749,
  "longitude": -122.4194
}
```

**Fields:**
- `externalId` (string, required): Unique shop ID on the device
- `name` (string, required): Shop name
- `location` (string): Address or location description
- `latitude` (number): GPS latitude
- `longitude` (number): GPS longitude

### Payment Card

```json
{
  "externalId": "card-chase-001",
  "name": "Chase Sapphire",
  "lastFour": "4242",
  "issuer": "Visa"
}
```

**Fields:**
- `externalId` (string, required): Unique card ID on the device
- `name` (string, required): Card name/label
- `lastFour` (string): Last 4 digits (no full PAN for security)
- `issuer` (string): Card network (Visa, Mastercard, etc.)

----

## Examples

### Example 1: Complete User Journey

**Step 1: Register**
```bash
curl -X POST https://api.financius.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePass123"
  }'
```

Response:
```json
{
  "data": {
    "user": { "id": "alice@example.com", "email": "alice@example.com" },
    "accessToken": "eyJhbGc...",
    "refreshToken": "eyJhbGc...",
    "expiresIn": 3600
  },
  "error": null,
  "meta": { "requestId": "abc-123" }
}
```

**Step 2: Generate QR Pairing Token**
```bash
curl -X GET https://api.financius.com/api/v1/pairing/qr \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json"
```

Response:
```json
{
  "data": {
    "qrPayload": {
      "serverBaseUrl": "https://api.financius.com",
      "pairingToken": "ZVF8fC5dGjkhobZAgd6_-2dwEqBZSrjj",
      "expiresAt": "2026-05-17T16:00:00+00:00"
    }
  },
  "error": null,
  "meta": { "requestId": "def-456" }
}
```

**Step 3: Sync Receipt**
```bash
curl -X POST https://api.financius.com/api/v1/sync \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "device-alice-pixel-6",
    "receipts": [
      {
        "externalId": "rcpt-20260517-001",
        "date": "2026-05-17T10:30:00Z",
        "total": 45.50,
        "currency": "USD",
        "lineItems": [
          {
            "categoryId": "cat-groceries",
            "amount": 45.50,
            "qty": 1,
            "name": "Groceries at Whole Foods"
          }
        ]
      }
    ],
    "categories": [
      {
        "externalId": "cat-groceries",
        "name": "Groceries",
        "icon": "🛒"
      }
    ],
    "shops": [],
    "cards": []
  }'
```

Response:
```json
{
  "data": {
    "accepted": {
      "receipts": 1,
      "categories": 1,
      "shops": 0,
      "cards": 0
    },
    "lastSyncAt": "2026-05-17T15:55:10+00:00",
    "syncId": "92e67e2c-6654-4379-b9f4-8da2b1c99bc3"
  },
  "error": null,
  "meta": { "requestId": "ghi-789" }
}
```

### Example 2: Idempotent Sync (Same Data Twice)

**First Sync:**
```bash
curl -X POST https://api.financius.com/api/v1/sync \
  -H "Authorization: Bearer {token}" \
  -d '{
    "deviceId": "device-1",
    "receipts": [{"externalId": "rcpt-001", "date": "2026-05-17T10:00:00Z", "total": 50.00, "currency": "USD", "lineItems": []}],
    "categories": [],
    "shops": [],
    "cards": []
  }'
```

Response: `"accepted": { "receipts": 1, "categories": 0, "shops": 0, "cards": 0 }`

**Second Sync (Same externalId):**
```bash
curl -X POST https://api.financius.com/api/v1/sync \
  -H "Authorization: Bearer {token}" \
  -d '{
    "deviceId": "device-1",
    "receipts": [{"externalId": "rcpt-001", "date": "2026-05-17T10:00:00Z", "total": 50.00, "currency": "USD", "lineItems": []}],
    "categories": [],
    "shops": [],
    "cards": []
  }'
```

Response: `"accepted": { "receipts": 1, "categories": 0, "shops": 0, "cards": 0 }` ✅

**Result:** No duplicates! Second sync updated the existing record, not created a new one.

----

## Best Practices

### 1. Use Unique External IDs

Always generate unique `externalId` values for receipts, categories, shops, and cards on the client side:

```kotlin
// Android Kotlin example
val externalId = "rcpt-${System.currentTimeMillis()}-${UUID.randomUUID()}"
```

This enables **idempotent syncing** - re-sending the same data won't create duplicates.

### 2. Sync in Batches

Group multiple receipts into a single sync request rather than syncing one at a time:

```json
{
  "deviceId": "device-1",
  "receipts": [
    { "externalId": "rcpt-001", ... },
    { "externalId": "rcpt-002", ... },
    { "externalId": "rcpt-003", ... }
  ],
  "categories": [...],
  "shops": [],
  "cards": []
}
```

### 3. Handle Token Expiration

Implement refresh token flow when access token expires:

```kotlin
// Pseudocode
if (response.status == 401 && response.error.code == "invalid_token") {
    refreshAccessToken()
    retryRequest()
}
```

### 4. Use Timestamps with Timezone

Always include timezone information in date fields (use UTC Z suffix):

```
✅ Correct:   "2026-05-17T10:30:00Z"
❌ Incorrect: "2026-05-17T10:30:00"
```

### 5. Retry on Network Errors

Implement exponential backoff for network failures:

```kotlin
// Pseudocode
var delay = 1000 // 1 second
for (attempt in 1..3) {
    try {
        syncData()
        return
    } catch (e: NetworkException) {
        Thread.sleep(delay)
        delay *= 2 // Exponential backoff
    }
}
```

### 6. Validate Before Sync

Check data validity before sending:

- ✅ All required fields present
- ✅ Amounts are non-negative
- ✅ External IDs are unique within the request
- ✅ Currency codes are valid ISO 4217

### 7. Store Tokens Securely

Use Android's EncryptedSharedPreferences:

```kotlin
val encryptedPrefs = EncryptedSharedPreferences.create(
    context,
    "secret_shared_prefs",
    MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)

encryptedPrefs.edit().putString("accessToken", token).apply()
```

### 8. Log Request IDs

Always log the `meta.requestId` from responses for debugging:

```kotlin
Log.d("Sync", "Request ID: ${response.meta.requestId}")
```

This helps support team troubleshoot issues quickly.

----

## Contact & Support

- **API Status:** https://status.financius.com
- **Support Email:** support@financius.com
- **Documentation:** https://docs.financius.com
- **Issues:** Report bugs with the `requestId` from error responses

----

**Last Updated:** May 17, 2026  
**API Version:** 1.0.0
