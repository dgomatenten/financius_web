# Android Integration Quick Start

**Get up and running in 10 minutes**

---

## 1. Setup (5 min)

### Add HTTP Client Dependency

Add Retrofit to `build.gradle`:
```gradle
dependencies {
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.squareup.okhttp3:okhttp:4.9.1'
}
```

### Create API Service

```kotlin
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*

interface FinanciusApi {
    
    @POST("auth/register")
    suspend fun register(@Body req: RegisterRequest): ApiResponse<AuthData>
    
    @POST("auth/login")
    suspend fun login(@Body req: LoginRequest): ApiResponse<AuthData>
    
    @GET("pairing/qr")
    suspend fun getQrToken(): ApiResponse<QrPayload>
    
    @POST("sync")
    suspend fun syncData(@Body payload: SyncPayload): ApiResponse<SyncResult>
    
    @GET("sync/status")
    suspend fun getSyncStatus(): ApiResponse<SyncStatus>
}

// Create instance
val retrofitClient = Retrofit.Builder()
    .baseUrl("https://api.financius.com/api/v1/")
    .addConverterFactory(GsonConverterFactory.create())
    .client(createOkHttpClient())
    .build()

val apiService = retrofitClient.create(FinanciusApi::class.java)
```

### Setup Interceptor for JWT

```kotlin
import okhttp3.OkHttpClient
import okhttp3.Interceptor

fun createOkHttpClient(): OkHttpClient {
    return OkHttpClient.Builder()
        .addInterceptor(AuthInterceptor(getStoredToken()))
        .build()
}

class AuthInterceptor(private val getToken: () -> String?) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): okhttp3.Response {
        val originalRequest = chain.request()
        val token = getToken()
        
        val newRequest = if (token != null) {
            originalRequest.newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        } else {
            originalRequest
        }
        
        return chain.proceed(newRequest)
    }
}
```

---

## 2. User Authentication (2 min)

### Register

```kotlin
class AuthViewModel : ViewModel() {
    
    suspend fun register(email: String, password: String) {
        try {
            val response = apiService.register(
                RegisterRequest(email, password)
            )
            
            if (response.data != null) {
                // Save tokens securely
                saveToken("accessToken", response.data.accessToken)
                saveToken("refreshToken", response.data.refreshToken)
                
                // Navigate to next screen
                navigateToHome()
            } else {
                showError(response.error?.message ?: "Registration failed")
            }
        } catch (e: Exception) {
            showError("Network error: ${e.message}")
        }
    }
    
    private fun saveToken(key: String, value: String) {
        val prefs = context.getSharedPreferences("auth", Context.MODE_PRIVATE)
        prefs.edit().putString(key, value).apply()
    }
}
```

### Login

```kotlin
suspend fun login(email: String, password: String) {
    try {
        val response = apiService.login(LoginRequest(email, password))
        
        if (response.data != null) {
            saveToken("accessToken", response.data.accessToken)
            saveToken("refreshToken", response.data.refreshToken)
            navigateToHome()
        } else {
            showError(response.error?.message ?: "Login failed")
        }
    } catch (e: Exception) {
        showError("Network error: ${e.message}")
    }
}
```

---

## 3. Device Pairing (2 min)

### Generate QR Code

```kotlin
suspend fun generateQrCode() {
    try {
        val response = apiService.getQrToken()
        
        if (response.data != null) {
            val qrPayload = response.data.qrPayload
            
            // Generate QR code from JSON
            val jsonString = Gson().toJson(qrPayload)
            val qrCodeBitmap = generateQrCode(jsonString)
            
            displayQrCode(qrCodeBitmap)
        }
    } catch (e: Exception) {
        showError("Failed to generate QR code")
    }
}

fun generateQrCode(text: String): Bitmap {
    val writer = QRCodeWriter()
    val bitMatrix = writer.encode(text, BarcodeFormat.QR_CODE, 512, 512)
    val width = bitMatrix.width
    val height = bitMatrix.height
    val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.RGB_565)
    
    for (x in 0 until width) {
        for (y in 0 until height) {
            bitmap.setPixel(x, y, if (bitMatrix[x, y]) Color.BLACK else Color.WHITE)
        }
    }
    
    return bitmap
}
```

---

## 4. Data Sync (1 min)

### Collect and Push Data

```kotlin
suspend fun syncReceiptsAndCategories() {
    try {
        val receipts = getLocalReceipts()
        val categories = getLocalCategories()
        val shops = getLocalShops()
        
        val payload = SyncPayload(
            deviceId = getDeviceId(),
            receipts = receipts,
            categories = categories,
            shops = shops,
            cards = emptyList()
        )
        
        val response = apiService.syncData(payload)
        
        if (response.data != null) {
            val accepted = response.data.accepted
            Log.d("Sync", "Synced: ${accepted.receipts} receipts, ${accepted.categories} categories")
            
            // Clear local sync queue or mark as synced
            markAsSynced(receipts)
            
            showSuccess("Sync completed successfully")
        } else {
            showError(response.error?.message ?: "Sync failed")
        }
    } catch (e: Exception) {
        showError("Network error: ${e.message}")
    }
}

fun getLocalReceipts(): List<Receipt> {
    // Query from local database
    return db.receiptDao().getAllReceipts().map { entity ->
        Receipt(
            externalId = entity.id,  // Use device-generated ID
            date = entity.createdAt,
            total = entity.total.toDouble(),
            currency = entity.currency,
            lineItems = entity.lineItems.map { lineEntity ->
                ReceiptLineItem(
                    categoryId = lineEntity.categoryId,
                    amount = lineEntity.amount.toDouble(),
                    qty = lineEntity.quantity,
                    name = lineEntity.description
                )
            }
        )
    }
}

fun getLocalCategories(): List<Category> {
    return db.categoryDao().getAllCategories().map { entity ->
        Category(
            externalId = entity.id,
            name = entity.name,
            icon = entity.emoji,
            color = entity.hexColor
        )
    }
}

fun getDeviceId(): String {
    val prefs = context.getSharedPreferences("device", Context.MODE_PRIVATE)
    var deviceId = prefs.getString("deviceId", null)
    
    if (deviceId == null) {
        deviceId = "device-${UUID.randomUUID()}"
        prefs.edit().putString("deviceId", deviceId).apply()
    }
    
    return deviceId
}
```

---

## 5. Data Models

### Add these to your project:

```kotlin
// API Response Envelope
data class ApiResponse<T>(
    val data: T?,
    val error: ApiError?,
    val meta: ApiMeta
)

data class ApiError(
    val code: String,
    val message: String
)

data class ApiMeta(
    val requestId: String
)

// Auth
data class RegisterRequest(val email: String, val password: String)
data class LoginRequest(val email: String, val password: String)

data class AuthData(
    val user: User,
    val accessToken: String,
    val refreshToken: String,
    val expiresIn: Int
)

data class User(
    val id: String,
    val email: String
)

// Pairing
data class QrPayload(
    val serverBaseUrl: String,
    val pairingToken: String,
    val expiresAt: String
)

// Sync
data class SyncPayload(
    val deviceId: String,
    val receipts: List<Receipt>,
    val categories: List<Category>,
    val shops: List<Shop>,
    val cards: List<PaymentCard>
)

data class Receipt(
    val externalId: String,
    val date: String,  // ISO 8601: "2026-05-17T10:30:00Z"
    val total: Double,
    val currency: String,
    val lineItems: List<ReceiptLineItem>
)

data class ReceiptLineItem(
    val categoryId: String,
    val amount: Double,
    val qty: Int = 1,
    val name: String
)

data class Category(
    val externalId: String,
    val name: String,
    val icon: String? = null,
    val color: String? = null
)

data class Shop(
    val externalId: String,
    val name: String,
    val location: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null
)

data class PaymentCard(
    val externalId: String,
    val name: String,
    val lastFour: String? = null,
    val issuer: String? = null
)

data class SyncResult(
    val accepted: SyncCounts,
    val lastSyncAt: String,
    val syncId: String
)

data class SyncCounts(
    val receipts: Int,
    val categories: Int,
    val shops: Int,
    val cards: Int
)

data class SyncStatus(
    val lastSyncAt: String?,
    val status: String
)
```

---

## 6. Best Practices

### ✅ DO:

- Store tokens in EncryptedSharedPreferences
- Generate unique `externalId` for each receipt: `"rcpt-${System.currentTimeMillis()}-${UUID.randomUUID()}"`
- Use ISO 8601 dates with Z suffix: `"2026-05-17T10:30:00Z"`
- Batch multiple receipts in one sync request
- Handle 401 errors and refresh token
- Log `requestId` from error responses

### ❌ DON'T:

- Store tokens in plain SharedPreferences
- Re-sync already synced receipts (track sync status)
- Send receipts one at a time
- Hardcode the API URL
- Ignore network errors silently

---

## 7. Example Activity

```kotlin
class SyncActivity : AppCompatActivity() {
    
    private val viewModel: SyncViewModel by viewModels()
    private val apiService by lazy { createApiService() }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_sync)
        
        lifecycleScope.launch {
            // 1. Register/Login
            viewModel.login("user@example.com", "password123")
            
            // 2. Generate QR pairing
            val qrBitmap = viewModel.generateQrCode()
            binding.qrImageView.setImageBitmap(qrBitmap)
            
            // 3. Sync receipts
            binding.syncButton.setOnClickListener {
                lifecycleScope.launch {
                    viewModel.syncReceiptsAndCategories()
                }
            }
        }
    }
}
```

---

## 8. Debugging

### Check Network Requests

Add logging interceptor:

```kotlin
val httpClient = OkHttpClient.Builder()
    .addInterceptor(HttpLoggingInterceptor().setLevel(HttpLoggingInterceptor.Level.BODY))
    .addInterceptor(AuthInterceptor { getToken() })
    .build()
```

### Save Request IDs

```kotlin
Log.d("Financius", "Request ID: ${response.meta.requestId}")
// Include this in bug reports!
```

---

## Need Help?

- Full API docs: See `API_ANDROID_DEVELOPER.md`
- Common errors: Check the [Error Handling](API_ANDROID_DEVELOPER.md#error-handling) section
- Example Kotlin project: Available in `/samples/android/`

---

**Happy coding!** 🚀
