© MOA Digital Agency (myoneart.com) - Author: Aisance KALONJI
[ 🇫🇷 Français ](Shabaka_AdScreen_features_full_list.md) | [ 🇬🇧 English ]

# FEATURE BIBLE - SHABAKA ADSCREEN

> **STATUS:** CONFIDENTIAL & PROPRIETARY.
> This document lists all business rules, algorithms, and processes of the Shabaka AdScreen application.

---

## 1. User & Organization Management

### 1.1 Roles & Permissions
*   **Superadmin:** Full access. Organization management, global content validation, system configuration.
*   **Organization Administrator (Org Admin):** Management of own screens, local content validation, access to entity billing.
*   **Standard User:** Campaign creation, content upload, payment.

### 1.2 Hierarchy
*   A user belongs to one or more **Organizations**.
*   Advertising commissions are paid to the Organization that owns the screen.

---

## 2. Screen Management

### 2.1 Key Attributes
*   **Status:** Online (Active), Offline (Inactive > 5min), Maintenance (Manually disabled).
*   **Orientation:** Landscape (16:9) or Portrait (9:16).
*   **Technical Configuration:** Resolution, Pairing Code.

### 2.2 Heartbeat & Monitoring
*   Each screen sends a regular "Heartbeat" to the server (`/api/screen/heartbeat`).
*   **Offline Logic:** If no heartbeat is received for > 5 minutes, the screen automatically switches to `Offline` status.
*   **Synchronization:** The heartbeat returns the current playlist hash to trigger an update if necessary.

---

## 3. Content Management

### 3.1 Content Types & Priority
The Player uses a strict priority queue to decide which content to display:

1.  **Broadcast (Priority 200):** Urgent messages or critical system announcements. Interrupts everything else.
2.  **Paid Content (Priority 100):** Validated paid advertisements (AdContent).
3.  **Internal Content (Priority 80):** Organization's own content (internal promotions).
4.  **AdContent (Priority 50):** Network ads (if applicable).
5.  **Filler (Priority 20):** Default filler content (Weather, News, Agency Logo) to avoid black screens.

### 3.2 Technical Validation
*   **Videos:** Mandatory MP4 format. Videos are processed via FFmpeg to generate HLS (HTTP Live Streaming) streams, allowing for adaptive and robust playback, even with fluctuating bandwidth.
*   **Images:** JPG, PNG. Configurable display duration (default: 10s).
*   **Max Size:** Limited by server configuration (default 100MB).

---

## 4. Booking Engine & Pricing

### 4.1 Pricing Algorithm
The price of a campaign is dynamically calculated according to the formula:

`Total Price = (Slot Base Price) x (Period Multiplier) x (Number of Plays)`

*   **Base Price (TimeSlot):** Defined by the screen for a given duration (e.g., 15s = €2).
*   **Multiplier (TimePeriod):** Coefficient according to the time of day (e.g., Peak Hour 18h-20h = x1.5).
*   **Number of Plays:** Quantity of plays purchased.

### 4.2 Commission Rules
*   Each screen generates revenue for its owning Organization.
*   The system automatically calculates the share going to MOA Digital Agency (service fee) and the share paid to the Organization.

---

## 5. Billing & Payments

### 5.1 Invoice Workflow (AdContentInvoice)
1.  **Pending:** Invoice generated, payment not received.
2.  **Paid:** Payment confirmed (Proof uploaded or transaction validated).
3.  **Validated:** Invoice verified by MOA accounting, commission released.

### 5.2 Payment Proof
*   Users can upload proof of transfer (PDF/JPG).
*   Manual validation by an Admin changes the status to `Paid`.

---

## 6. Player & Broadcasting

### 6.1 Playback Logic
*   The Player is a Web application (HTML/JS) running on the screen's browser.
*   It caches content via the `CacheStorage` API and a Service Worker for offline operation (Offline Fallback).
*   It uses `hls.js` for playback of video streams, with a fallback to `mpegts.js` if necessary.
*   It polls the `/player/api/playlist` API to get the playback order. In case of an error or empty screen, the backend returns a 200 status with "Filler" content to ensure the screen never goes black.

### 6.2 Player Security
*   Session Token Authentication.
*   CSRF Protection disabled for critical playback endpoints (Heartbeat, Log Play) to ensure fluidity, but secured by IP/Device ID validation.
