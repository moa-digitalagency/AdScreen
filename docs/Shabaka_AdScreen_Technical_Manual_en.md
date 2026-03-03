© MOA Digital Agency (myoneart.com) - Author: Aisance KALONJI
[ 🇫🇷 Français ](Shabaka_AdScreen_Technical_Manual.md) | [ 🇬🇧 English ]

# TECHNICAL MANUAL - SHABAKA ADSCREEN

> **CONFIDENTIAL:** This document details the internal architecture and technology stack of the proprietary Shabaka AdScreen solution.

---

## 1. Global Architecture

### 1.1 Architecture Type
**Monolithic Modular** application based on the **Flask** (Python) framework.
The application is structured around **Blueprints** to isolate functional domains and facilitate maintenance.

### 1.2 Folder Structure
*   `app.py`: Entry point, configuration, extension initialization (DB, Login, CSRF).
*   `models/`: SQLAlchemy data models (ORM).
*   `routes/`: Controllers (Blueprints) handling HTTP requests.
*   `services/`: Complex business logic (Calculations, Processing, I/O).
*   `templates/`: Jinja2 Views (Server-Side Rendering).
*   `static/`: Frontend Assets (JS, CSS, Images).

### 1.3 Main Blueprints
*   `auth_bp`: Authentication and session management.
*   `admin_bp`: Superadmin Back-office.
*   `org_bp`: Organization Management (SaaS).
*   `screen_bp`: Technical screen management.
*   `player_bp`: Display interface for physical screens.
*   `booking_bp`: Campaign booking engine.
*   `api_bp` / `mobile_api_bp`: API interfaces for integrations and mobile.

---

## 2. Technology Stack

### 2.1 Backend
*   **Language:** Python 3.x
*   **Framework:** Flask
*   **ORM:** SQLAlchemy (Supports SQLite and PostgreSQL)
*   **Auth:** Flask-Login, PyJWT (for Mobile API)

### 2.2 Frontend
*   **Template Engine:** Jinja2
*   **CSS Framework:** Tailwind CSS (via CDN or build process)
*   **JavaScript:** Vanilla JS (ES6+), no heavy client-side framework for the dashboard.

### 2.3 Database
*   **System:** PostgreSQL Compatible (Prod) and SQLite (Dev/Test).
*   **Migrations:** Managed via `init_db.py` (Proprietary initialization script). The SQLAlchemy ORM handles dialect abstraction.

---

## 3. High Availability Architecture (24/7)

To ensure uninterrupted content broadcasting on screens (fault tolerance), the Player integrates a robust high availability architecture:

### 3.1 Caching and Service Worker (Offline Fallback)
*   **Active Caching:** The Player utilizes the `CacheStorage` API and a **Service Worker** (`static/js/player-sw.js`) to cache the web application and multimedia content (videos, images) as they are played.
*   **Network Fault Tolerance:** In the event of an internet connection loss, the Service Worker intercepts media requests and serves the cached versions. The Player continues to loop through the last valid playlist.
*   **Automatic Recovery:** As soon as the connection is restored, the Player downloads new content in the background and updates its cache seamlessly.

### 3.2 Smart Queue and LocalStorage
*   **Local State Management:** The current playlist index, pending broadcast logs, and the last valid configuration are saved in the screen browser's `LocalStorage`.
*   **Continuity After Restart:** In case of a power outage and physical screen restart, the Player retrieves its state from `LocalStorage` and resumes broadcasting immediately, without waiting for a distant server response if it's unreachable.
*   **Deferred Synchronization:** Broadcast statistics (logs) generated during an offline period are stacked locally and sent to the server as a batch as soon as connectivity returns, guaranteeing that no billing data is lost.

---

## 4. Security & Compliance

### 4.1 Authentication
*   Passwords hashed via `werkzeug.security` (PBKDF2 or Scrypt).
*   Session protection via `HttpOnly` and `Secure` cookies.

### 4.2 CSRF Protection
*   Dual implementation: Session Token + Form/Header Token.
*   Strict validation on all mutating methods (POST, PUT, DELETE, PATCH).
*   Exceptions configured for critical Player endpoints (Heartbeat) to avoid service interruptions, secured by IP/Device validation.

### 4.3 Security Headers
*   `X-Content-Type-Options: nosniff`
*   `X-Frame-Options: SAMEORIGIN`
*   `Strict-Transport-Security` (HSTS) in production.

---

## 5. Data Model (Overview)

### 5.1 Core Entities
*   **User:** System user (Roles: Superadmin, Org Admin, User).
*   **Organization:** Legal entity owning screens.
*   **Screen:** Physical display device.
*   **Booking:** Advertising space reservation.
*   **TimeSlot / TimePeriod:** Definition of slots and pricing.

### 4.2 Content Entities
*   **AdContent:** Paid advertising content.
*   **Broadcast:** Priority content (Emergency).
*   **InternalContent:** Organization's own content.
*   **Filler:** Filler content.

### 4.3 Billing Entities
*   **AdContentInvoice:** Invoice generated for a campaign.
*   **AdContentStat:** Proof of play (Daily logs).

---

## 6. Key Business Services

### 6.1 Pricing Service (`services/pricing_service.py`)
Calculates campaign costs in real-time based on the complex pricing grid (Duration x Period x Screen).

### 5.2 Playlist Service (`services/playlist_service.py`)
Generates the playlist for each screen respecting the priority queue and purchased playback quotas.

### 5.3 Input Validator (`services/input_validator.py`)
Ensures strict validation of user inputs and uploaded files (MIME types, extensions) to prevent injections.
