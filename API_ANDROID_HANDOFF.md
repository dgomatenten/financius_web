# Financius Android API Handoff

**Version:** 1.1.0  
**Last Updated:** May 18, 2026

## API Base URL

- Production: `https://api.financius.com/api/v1/`
- Local phone testing (same Wi-Fi): `http://10.0.0.42:5000/api/v1/`

## Important Authentication Rule

There is **no API key** for this backend.

All protected endpoints require a backend JWT access token in this header:

```http
Authorization: Bearer <backend accessToken>
```

Do not send Google access tokens directly to protected endpoints like `/sync`.

## Endpoint Summary

| Purpose | Method | Path | Auth Required |
|---|---|---|---|
| Register | POST | `/auth/register` | No |
| Email login | POST | `/auth/login` | No |
| Google login exchange | POST | `/auth/google` | No |
| Refresh access token | POST | `/auth/refresh` | No |
| Logout | POST | `/auth/logout` | No |
| Generate pairing token | GET | `/pairing/qr` | Yes |
| Sync payload | POST | `/sync` | Yes |
| Sync status | GET | `/sync/status` | Yes |
| Health check | GET | `/health` | No |

## Authentication Flows

### Email/Password Flow

1. Call `POST /auth/login`.
2. Save `data.accessToken` and `data.refreshToken`.
3. Use `Authorization: Bearer <accessToken>` for `/sync` and `/sync/status`.

Request:

```json
{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

### Google Login Flow (Required for Android Google Sign-In)

1. Perform Google sign-in in Android app.
2. Obtain **Google ID token** from Google SDK.
3. Exchange Google ID token with backend using `POST /auth/google`.
4. Save backend `accessToken` and `refreshToken` from response.
5. Use backend access token for all protected backend endpoints.

Request to backend:

```json
{
  "idToken": "GOOGLE_ID_TOKEN_HERE"
}
```

Response shape:

```json
{
  "data": {
    "user": {
      "id": "user@example.com",
      "email": "user@example.com"
    },
    "accessToken": "<jwt>",
    "refreshToken": "<jwt>",
    "expiresIn": 3600
  },
  "error": null,
  "meta": {
    "requestId": "abc-123-def"
  }
}
```

### Refresh Flow

When a protected call returns `401` with `invalid_token`:

1. Call `POST /auth/refresh`.
2. Replace stored access token.
3. Retry original request once.

Refresh request:

```json
{
  "refreshToken": "REFRESH_TOKEN_HERE"
}
```

## Protected Sync API

### Sync Payload

**Endpoint:** `POST /sync`  
**Headers:**

```http
Authorization: Bearer <accessToken>
Content-Type: application/json
```

**Minimum valid request body:**

```json
{
  "deviceId": "device-alice-pixel-6",
  "receipts": [],
  "categories": [],
  "shops": [],
  "cards": []
}
```

### Sync Status

**Endpoint:** `GET /sync/status`  
**Headers:**

```http
Authorization: Bearer <accessToken>
```

## Device Pairing

### Generate Pairing Token

**Endpoint:** `GET /pairing/qr`  
**Headers:**

```http
Authorization: Bearer <accessToken>
```

Sample response:

```json
{
  "data": {
    "qrPayload": {
      "serverBaseUrl": "http://10.0.0.42:5000",
      "pairingToken": "ZVF8fC5dGjkhobZAgd6_-2dwEqBZSrjj",
      "expiresAt": "2026-05-18T10:10:00+00:00"
    }
  },
  "error": null,
  "meta": {
    "requestId": "abc-123-def"
  }
}
```

QR token lifetime is 300 seconds.

## Error Handling

All responses use envelope format:

```json
{
  "data": null,
  "error": {
    "code": "error_code",
    "message": "Human-readable error message"
  },
  "meta": {
    "requestId": "unique-request-id"
  }
}
```

Common error codes:

| Code | Status | Meaning |
|---|---|---|
| `invalid_credentials` | 401 | Bad email/password or invalid Google audience |
| `invalid_token` | 401 | Missing, expired, or malformed backend JWT |
| `duplicate_email` | 409 | Email already exists |
| `validation_error` | 400 | Missing required field or invalid payload |

## 401 Troubleshooting Checklist

If `/sync` returns `401`, check these in order:

1. `Authorization` header exists and starts with `Bearer `.
2. Token is backend `accessToken`, not Google access token.
3. Google sign-in path calls `/auth/google` first and stores backend tokens.
4. Base URL points to backend API prefix, for example `http://10.0.0.42:5000/api/v1/`.
5. Access token not expired; if expired, run refresh flow and retry once.

## Copy/Paste cURL (Local Phone Test)

### Health

```bash
curl -sS http://10.0.0.42:5000/api/v1/health
```

### Google Exchange

```bash
curl -X POST http://10.0.0.42:5000/api/v1/auth/google \
  -H "Content-Type: application/json" \
  -d '{"idToken":"GOOGLE_ID_TOKEN_HERE"}'
```

### Sync

```bash
curl -X POST http://10.0.0.42:5000/api/v1/sync \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId":"phone-test-1",
    "receipts":[],
    "categories":[],
    "shops":[],
    "cards":[]
  }'
```

### Refresh

```bash
curl -X POST http://10.0.0.42:5000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refreshToken":"REFRESH_TOKEN_HERE"}'
```

## Android Implementation Notes

1. Use `EncryptedSharedPreferences` for tokens.
2. Add an interceptor to attach `Authorization` header from stored access token.
3. Add an authenticator for one-time refresh/retry on `401`.
4. Use ISO-8601 UTC timestamps with `Z` suffix.
5. Log `meta.requestId` from failures for server-side debugging.

## Support Handoff Notes

When reporting issues, include:

1. Full request path and method.
2. HTTP status.
3. Error body with `error.code` and `meta.requestId`.
4. Whether token source was `/auth/login` or `/auth/google`.
