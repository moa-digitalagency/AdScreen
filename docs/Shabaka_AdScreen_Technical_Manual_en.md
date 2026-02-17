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
*   **System:** PostgreSQL Compatible (Prod) and SQLite (Dev).
*   **Migrations:** Managed via `init_db.py` (Proprietary initialization script).

---

## 3. Security & Compliance

### 3.1 Authentication
*   Passwords hashed via `werkzeug.security` (PBKDF2 or Scrypt).
*   Session protection via `HttpOnly` and `Secure` cookies.

### 3.2 CSRF Protection
*   Dual implementation: Session Token + Form/Header Token.
*   Strict validation on all mutating methods (POST, PUT, DELETE, PATCH).
*   Exceptions configured for critical Player endpoints (Heartbeat) to avoid service interruptions, secured by IP/Device validation.

### 3.3 Security Headers
*   `X-Content-Type-Options: nosniff`
*   `X-Frame-Options: SAMEORIGIN`
*   `Strict-Transport-Security` (HSTS) in production.

---

## 4. Data Model (Overview)

### 4.1 Core Entities
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

## 5. Key Business Services

### 5.1 Pricing Service (`services/pricing_service.py`)
Calculates campaign costs in real-time based on the complex pricing grid (Duration x Period x Screen).

### 5.2 Playlist Service (`services/playlist_service.py`)
Generates the playlist for each screen respecting the priority queue and purchased playback quotas.

### 5.3 Input Validator (`services/input_validator.py`)
Ensures strict validation of user inputs and uploaded files (MIME types, extensions) to prevent injections.
