**© MOA Digital Agency (myoneart.com) - Author: Aisance KALONJI**
*This code is the exclusive property of MOA Digital Agency. Internal use only. Unauthorized reproduction or distribution is strictly prohibited.*

[Passer à la version Française](./Shabaka_AdScreen_features_full_list.md)

---

# Shabaka AdScreen - Comprehensive Feature List (The Bible)

This document is the absolute reference for all features, business rules, validations, and system behaviors of the Shabaka AdScreen platform. It serves as the ground truth for developers, testers, and auditors.

### 1. System Core

#### 1.1 Authentication & Security
*   **Password Hashing**: Uses `werkzeug.security` (Scrypt by default, or PBKDF2-SHA256 depending on configuration) for secure storage.
*   **Session Management**:
    *   `HttpOnly`, `SameSite=Lax` cookies.
    *   `Secure` flag enabled in production (via `FLASK_ENV=production` env var).
    *   Session fixation protection via ID regeneration.
*   **CSRF Protection (Cross-Site Request Forgery)**:
    *   Manual implementation via `app.before_request`.
    *   Unique token per session (`_csrf_token`).
    *   Verification on all `POST`, `PUT`, `DELETE`, `PATCH` methods.
    *   **Exceptions**: API endpoints (`api.*`, `mobile_api.*`) and Webhooks (`billing.cron_generate_invoices`).
*   **Security Headers**:
    *   `X-Content-Type-Options: nosniff`
    *   `X-Frame-Options: SAMEORIGIN`
    *   `Referrer-Policy: strict-origin-when-cross-origin`
    *   `Strict-Transport-Security: max-age=31536000; includeSubDomains` (if HTTPS).
*   **Rate Limiting**:
    *   Library: `Flask-Limiter`.
    *   Storage: Memory (Dev) or Redis (Prod).
    *   Default rules:
        *   Login: **5 requests / minute**.
        *   Mobile API (Read): **60 requests / minute**.
        *   Player Heartbeat: **120 requests / minute**.

#### 1.2 Input Validation
All incoming data is sanitized via `services/input_validator.py`.
*   **Strings**: HTML cleaning (removal of `<script>` tags, etc.) and truncation to 255 characters by default.
*   **Emails**: Validation via `email-validator` (RFC syntax check).
*   **Phone Numbers**: Regex `^\+?[\d]{8,15}$` (International format, 8 to 15 digits).
*   **Screen Codes**: Regex `^[A-Za-z0-9\-_]+$` (Alphanumeric, dashes, underscores only).
*   **URLs**:
    *   Must start with `http://` or `https://`.
    *   **SSRF** (Server-Side Request Forgery) protection: DNS resolution and verification that the target IP is not private/local (unless excepted).
*   **Dates**: Strict format `YYYY-MM-DD`.
*   **Positive Integers**: Strict verification of bounds (min/max).

### 2. Screen Management

#### 2.1 Configuration
*   **Unique Identifier**: Randomly generated code or manually defined (validated by Regex).
*   **Resolution**: Width and Height in pixels (e.g., 1920x1080). Used to validate uploads.
*   **Orientation**: 'landscape' or 'portrait'.
*   **Operating Modes**:
    1.  **Playlist**: Loop of media content.
    2.  **IPTV**: Streaming of HLS/M3U8 streams.
        *   Proxying support to bypass CORS.
        *   MPEG-TS to HLS conversion on the fly via FFmpeg (if enabled).

#### 2.2 Monitoring
*   **Heartbeat**: The player sends a ping every **30 seconds**.
*   **Statuses**:
    *   `Online`: Heartbeat received < 2 minutes.
    *   `Playing`: Currently playing.
    *   `Offline`: No signal > 2 minutes.
*   **Logs**: History kept in the `heartbeat_log` table.

### 3. Booking Engine

#### 3.1 Booking Modes
The system supports two distinct booking logics:
1.  **By Number of Plays (Plays Mode)**:
    *   The client purchases a fixed number of plays (e.g., 100 plays).
    *   Validity: Until the quota is exhausted.
2.  **By Date (Dates Mode)**:
    *   The client purchases a period (e.g., from 01/01 to 07/01).
    *   Goal: X plays per day.
    *   **Fair Distribution Algorithm**: The system calculates daily availability and smooths distribution over the period.

#### 3.2 Price Calculation
Exact formula applied in `booking_routes.py`:
```python
Base_Slot_Price = Screen_Minute_Price * (Slot_Duration / 60)
Unit_Price      = Base_Slot_Price * Period_Multiplier
Total_Price_Ex_Tax = Unit_Price * Total_Number_Of_Plays
Total_Price_Inc_Tax = Total_Price_Ex_Tax * (1 + VAT_Rate / 100)
```
*   **TimeSlots**: Predefined durations (10s, 15s, 20s, 30s).
*   **TimePeriods**: Time ranges with multiplier (e.g., 6PM-11PM = x1.5).

#### 3.3 Uploaded Media Validation
*   **Images**:
    *   Formats: JPG, PNG, GIF, WebP.
    *   Dimensions: Must match the screen resolution **exactly**.
    *   Size: Max 100 MB (config `MAX_CONTENT_LENGTH`).
*   **Videos**:
    *   Formats: MP4, WebM, MOV.
    *   Duration: Must be **less than or equal** to the reserved slot (0 tolerance).
    *   Analysis: Use of `ffprobe` to extract duration and dimensions.

### 4. The Player (Display Logic)

#### 4.1 Content Prioritization
The playlist generation algorithm (`mobile_api_routes.py`) ranks content by decreasing priority score:
1.  **Broadcasts (200)**: Emergency/system messages (e.g., "Exceptional closure").
2.  **Paid Content (100)**: Active paid advertisements (Quota > 0).
3.  **Internal Content (80)**: Venue self-promotion.
4.  **AdContent (50)**: Ad network ads (Third-party network).
5.  **Fillers (20)**: Default filler content (e.g., "Scan this QR Code").

#### 4.2 Playback & Tracking
*   **Polling**: Retrieval of the JSON playlist every **60 seconds**.
*   **Preloading**: Browser caching of assets to smooth transitions.
*   **Logging**: At the end of each playback, the player calls `/log-play`.
    *   Decrements the `remaining_plays` counter of the Booking.
    *   Updates status to `completed` if quota is reached.
    *   Records an entry in `stat_log` for reports.

#### 4.3 Overlays
*   **Tickers**: Configurable scrolling texts (Speed, Color, Position).
*   **Logic**: Can be associated with a specific period or be permanent.
*   **Compatibility**: Work over Video mode AND IPTV mode.

### 5. Mobile API (Management)

The `/mobile/api/v1` API is dedicated to management applications (Flutter/React Native).

#### 5.1 Specific Error Codes
In addition to standard HTTP codes, the API returns business codes in the JSON (`code`):
*   `MISSING_PASSWORD`: Password not provided.
*   `INVALID_CREDENTIALS`: Incorrect Email/Code or password.
*   `ACCOUNT_DISABLED`: User has been disabled by an admin.
*   `SCREEN_DISABLED`: Screen has been disabled.
*   `REFRESH_FAILED`: Invalid or expired refresh token.
*   `SCREEN_NOT_FOUND`: Non-existent screen ID or outside organization scope.
*   `VALIDATION_ERROR`: Data validation failure (details in `field`).

#### 5.2 JWT Authentication
*   **Access Token**: Expiration 24 hours. Contains `user_id`, `role`, `organization_id`.
*   **Refresh Token**: Expiration 30 days. Allows obtaining a new Access Token without relogin.

### 6. Billing & Finance

#### 6.1 Lifecycle
1.  **Generation**: Cron Job (`billing_routes.py`) executed on **Sunday at 11:59 PM**.
2.  **Calculation**: Sum of paid `Booking`s from the past week.
3.  **Commission**: Application of the platform percentage (defined per Organization).
4.  **Status**: `pending` -> `paid` (Proof sent) -> `validated` (Money received).

#### 6.2 Currencies
*   Multi-currency support (EUR, USD, TND, etc.).
*   Currency symbol is injected globally via the `inject_currency` Context Processor.

### 7. Internationalization (i18n)

*   **Mechanism**: Custom service `services/translation_service.py`.
*   **Storage**: Flat JSON files.
*   **Detection**:
    1.  URL `/set-language/<lang>`.
    2.  Session cookie.
    3.  Browser `Accept-Language` header.
    4.  Default language (`fr`).
