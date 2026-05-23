# Android Sync Integration Draft (Financius)

## Goal

- Fix sync failures by handling token lifecycle correctly and sending data in batches.
- Backend is stable now for medium payloads; current failures are from invalid or expired token and oversized request batches.

## Base URL

- Local phone test: http://10.0.0.42:5000/api/v1
- Production: use your production API base

## Auth Rules (Critical)

1. Sync endpoints require backend JWT access token.
2. Google sign-in token is not accepted by sync endpoints.
3. Google flow must be:
- Google SDK sign-in
- Get Google ID token
- POST /auth/google
- Store returned accessToken and refreshToken
4. On 401 from sync or status:
- Call POST /auth/refresh with refreshToken
- Replace both accessToken and refreshToken (refresh token rotates)
- Retry original request once

## Required Endpoints and Payloads

### 1) POST /auth/google

Request body:

```json
{
  "idToken": "GOOGLE_ID_TOKEN"
}
```

Use response `data.accessToken` and `data.refreshToken`.

### 2) POST /auth/refresh

Request body:

```json
{
  "refreshToken": "CURRENT_REFRESH_TOKEN"
}
```

Replace both tokens from response.

### 3) POST /sync

Headers:

- Authorization: Bearer ACCESS_TOKEN
- Content-Type: application/json

Body shape:

```json
{
  "deviceId": "device-unique-id",
  "receipts": [],
  "categories": [],
  "shops": [],
  "cards": []
}
```

## Batching Requirement

- Do not send one giant sync payload.
- Recommended: 200 to 500 receipts per request.
- Hard cap: 1500 total items per request across receipts + categories + shops + cards.
- If response says payload has too many items, reduce batch size and retry.

## Implementation Blueprint (Kotlin-Style)

### TokenStore

- saveAccessToken(token)
- saveRefreshToken(token)
- getAccessToken()
- getRefreshToken()
- clear()

### AuthRepository

- exchangeGoogleIdToken(idToken): AuthTokens
- refresh(refreshToken): AuthTokens

### AuthInterceptor

- For protected calls, add Authorization header with Bearer access token.

### TokenAuthenticator (Single Retry on 401)

- If request already retried once, fail.
- Read refresh token from TokenStore.
- Call /auth/refresh.
- If refresh succeeds:
- Update TokenStore with new access and refresh token.
- Retry original request with new access token.
- If refresh fails:
- Clear TokenStore.
- Force user re-login.

### Sync Batching Service

- Build receipt chunks of size 300 (safe default).
- Send sequentially (or low parallelism like 2 max).
- For each chunk:
- POST /sync with same deviceId
- If 401, let authenticator refresh and retry once
- If 400 too many items, split chunk in half and retry
- If network timeout, exponential backoff retry (max 3 attempts)
- Persist checkpoint after each successful chunk so app can resume

## Pseudo-Flow

1. Ensure logged in and token present.
2. Gather unsynced receipts.
3. chunked = receipts.chunked(300)
4. For each chunk:
- payload = {
  deviceId,
  receipts: chunk,
  categories: relatedCategoriesForChunk,
  shops: relatedShopsForChunk,
  cards: relatedCardsForChunk
}
- call /sync
- on success mark chunk synced
5. After all chunks, call /sync/status (optional verification)

## Error Handling Matrix

1. 401 invalid_token:
- Refresh token flow and retry once
2. 400 validation_error receipts must be an array:
- Payload bug on client serialization
3. 400 too many items:
- Reduce batch size
4. 5xx:
- Retry with backoff, keep unsynced state
5. broken pipe or socket write error:
- Treat as transient network or server disconnect, retry same chunk with backoff

## Serialization Guardrails

1. Send JSON object body, not malformed manual payload string.
2. receipts, categories, shops, cards must be arrays.
3. ISO timestamps should include timezone, for example 2026-05-18T10:00:00Z.
4. Keep field names aligned with backend contract.

## Quick Acceptance Checklist

1. Google login can sync without re-login loop.
2. Expired access token auto-refreshes and request succeeds.
3. 200 receipts sync succeeds.
4. 1800 receipts in one request is never attempted by client (must be chunked).
5. No broken pipe for normal batch sizes.
6. requestId from failed responses is logged for support.
