![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue) ![Framework](https://img.shields.io/badge/Framework-Flask-green) ![Database](https://img.shields.io/badge/Database-PostgreSQL-orange) ![Status](https://img.shields.io/badge/Status-Proprietary-red) ![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red) ![Owner: MOA Digital Agency](https://img.shields.io/badge/Owner-MOA%20Digital%20Agency-purple)

# Shabaka AdScreen - User Guide

This guide is intended for venue managers (bars, hotels, malls) and advertisers wishing to broadcast content.

### 1. For Screen Owners (Organizations)

You manage a venue open to the public and want to monetize your screens.

#### 1.1 Accessing your Space
Login at `/login`. You will arrive at your **Dashboard** showing:
*   Active screens count.
*   Revenue generated this week.
*   Content pending validation.

#### 1.2 Adding a New Screen
1.  Go to **Screens** > **Add**.
2.  Give it a name (e.g., "Main Lobby").
3.  Define the **exact resolution** (e.g., 1920x1080).
4.  Choose **orientation** (Landscape or Portrait).
5.  Set the **Base Price per Minute** (e.g., €1.00). This rate is the basis for slot calculations.

#### 1.3 Configuring Prices
Once created, configure sales options:
*   **Time Slots**: Define sellable durations (10s, 15s, 30s).
*   **Time Periods**: Apply multipliers based on time of day.
    *   *Example: Create a "Happy Hour" period from 6 PM to 9 PM with a x1.5 multiplier.*

#### 1.4 Managing the Playlist
*   **Validation**: When a client books a slot, you get a notification. Go to **Content** > **To Validate**. Check that the visual meets your ethical standards.
*   **Self-Promo**: You can broadcast your own ads (Menu, Events) for free via the **Internal Content** tab. These have slightly lower priority than paid ads.
*   **Overlays**: Add scrolling messages (tickers) at the bottom of the screen for quick announcements.

#### 1.5 Billing
Every Sunday night, an invoice is generated calculating the commission due to the platform.
1.  Go to **Billing**.
2.  Download the pending invoice.
3.  Transfer the commission amount.
4.  Upload the proof of transfer to unlock your account.

### 2. For Advertisers (Clients)

You want to broadcast an ad on a Shabaka network screen.

#### 2.1 Booking a Space
1.  Scan the **QR Code** displayed on the screen or click the booking link provided by the venue.
2.  You access the screen's page with rates and availability.

#### 2.2 Choosing Booking Mode
The system offers two options:

**Option A: Pay per Play (Classic)**
*   Buy a stock of plays (e.g., 100 plays).
*   Your ad plays until the stock runs out.
*   *Best for: Flash sales or short events.*

**Option B: Date Range (Campaign)**
*   Choose start and end dates.
*   Define plays **per day** (e.g., 20/day for 7 days).
*   The system calculates total price and guarantees fair distribution.
*   *Best for: Brand awareness.*

#### 2.3 Ad Configuration
*   **Media Type**: Image or Video.
*   **Duration**: Select display time (e.g., 15 seconds).
*   **Period**: Choose time of day (Morning, Noon, Evening).

#### 2.4 Uploading Content
Strictly follow the technical constraints:
*   **Resolution**: Must match screen exactly (e.g., 1920x1080).
*   **Size**: Max 100 MB.
*   **Format**: JPG/PNG for images, MP4 for videos.

### 3. FAQ

**Q: My screen is black, what to do?**
A: Check the player's internet connection. If offline > 2 mins, it shows "Offline" in dashboard. Restart player browser.

**Q: Can I stream Live TV?**
A: Yes, if "IPTV" mode is enabled. Go to screen config and provide an M3U8 stream URL.
