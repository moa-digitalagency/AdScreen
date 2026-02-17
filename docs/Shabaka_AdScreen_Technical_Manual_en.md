![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue) ![Framework](https://img.shields.io/badge/Framework-Flask-green) ![Database](https://img.shields.io/badge/Database-PostgreSQL-orange) ![Status](https://img.shields.io/badge/Status-Proprietary-red) ![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red) ![Owner: MOA Digital Agency](https://img.shields.io/badge/Owner-MOA%20Digital%20Agency-purple)

# Shabaka AdScreen - Technical Manual

This document consolidates the technical architecture, security audit, database schema, API reference, and deployment guide for the Shabaka AdScreen platform.

### 1. Architecture Overview

Shabaka AdScreen is a robust **Monolithic Modular** application built on the **Flask** framework (Python). It follows the **MVC (Model-View-Controller)** pattern:
*   **Models**: Defined with **SQLAlchemy** (ORM).
*   **Views**: **Jinja2** templating coupled with **Tailwind CSS**.
*   **Controllers**: Routes organized into **Blueprints**.

#### Project Structure
The application is structured around Blueprints to isolate functional domains:
```
/
├── app.py                 # Entry point, config, extensions init
├── models/                # DB Schema definitions
│   ├── user.py            # User & Role management
│   ├── screen.py          # Screen configuration
│   ├── booking.py         # Booking logic
│   └── ...
├── routes/                # Controllers (Blueprints)
│   ├── auth_routes.py     # Login, Register
│   ├── admin_routes.py    # Superadmin Back-office
│   ├── org_routes.py      # Organization Dashboard
│   ├── screen_routes.py   # Screen technical management
│   ├── booking_routes.py  # Public booking tunnel
│   ├── player_routes.py   # Player display logic
│   ├── mobile_api_routes.py # JSON API for Mobile App
│   └── ...
├── services/              # Complex business logic
│   ├── hls_converter.py   # Proxy & Video Conversion (FFmpeg)
│   ├── playlist_service.py # Content selection algorithm
│   └── billing_service.py # Weekly invoice generation
└── static/                # Assets (CSS, JS, Uploads)
```

### 2. Tech Stack

*   **Backend**: Python 3.11+, Flask 3.0+, Gunicorn, Gevent.
*   **Database**: PostgreSQL 14+ (Production), SQLite (Dev). ORM: SQLAlchemy 2.0+.
*   **Frontend**: Jinja2 (SSR), Tailwind CSS 3.4, Vanilla JS (ES6+), hls.js.
*   **Media**: FFmpeg (Transcoding/Streaming), Pillow (Image processing).
*   **Security**: Flask-Login (Session), PyJWT (API Token), Bleach (Sanitization), Flask-Limiter.

### 3. Database Schema

#### Identity & Access
*   `User`: `id`, `email`, `password_hash`, `role` (superadmin, admin, manager), `organization_id`.
*   `Organization`: `id`, `name`, `currency`, `commission_rate`, `vat_rate`.

#### Infrastructure
*   `Screen`: `id`, `unique_code`, `resolution_width`, `resolution_height`, `orientation`, `current_mode` (playlist/iptv).
*   `TimeSlot`: `duration_seconds` (10, 15, 30), `price_per_play`.
*   `TimePeriod`: `start_hour`, `end_hour`, `price_multiplier`.

#### Content & Booking
*   `Content`: `filename`, `content_type` (image/video), `status`, `duration_seconds`.
*   `Booking`: `num_plays` (purchased quota), `plays_completed`, `total_price`, `status`.
*   `Invoice`: `week_start`, `gross_revenue`, `commission_amount`, `status` (pending/paid).

#### Logs
*   `StatLog`: Proof of play (`played_at`, `duration`).
*   `HeartbeatLog`: Player connectivity history.

### 4. Security Audit

#### 4.1 Authentication
*   **Hashing**: PBKDF2-SHA256 via `werkzeug.security`.
*   **Sessions**: `HttpOnly`, `SameSite=Lax`, `Secure` (Prod).
*   **JWT**: Used for Mobile API (Access Token 24h, Refresh Token 30d).

#### 4.2 Protection Mechanisms
*   **CSRF**: Manual token validation on all state-changing methods (`POST`, `PUT`, `DELETE`), except API endpoints.
*   **Rate Limiting**:
    *   Login: 5 req/min.
    *   API Mobile: 60 req/min.
    *   Player Heartbeat: 120 req/min.
*   **Headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `HSTS`.

#### 4.3 Input Validation
*   **Uploads**: Strict MIME type check (Magic numbers) via Pillow/ffprobe. Files renamed with UUIDs.
*   **SSRF**: Streaming proxy validates target IPs to prevent local network scanning.

### 5. API Reference

#### 5.1 Management API (`/mobile/api/v1`)
*   **Auth**: Bearer Token (JWT).
*   `POST /auth/login`: Get Access/Refresh tokens.
*   `GET /dashboard/summary`: Organization stats.
*   `GET /dashboard/screens`: List screens and status.

#### 5.2 Player API (`/player/api`)
*   **Auth**: Session Cookie.
*   `GET /playlist`: Get JSON playlist (Next items to play).
*   `POST /heartbeat`: Send "I'm alive" signal.
*   `POST /log-play`: Report content playback (Decrements quota).

### 6. Deployment Guide

#### 6.1 Requirements
*   VPS with Ubuntu 20.04/22.04.
*   Python 3.11+, PostgreSQL, Nginx, FFmpeg.

#### 6.2 Installation Steps
1.  **Clone**: `git clone <repo_url>`
2.  **Env**: Create `.env` file with `DATABASE_URL`, `SESSION_SECRET`, `FLASK_ENV=production`.
3.  **Deps**: `pip install -r requirements.txt`.
4.  **DB**: `python init_db.py`.
5.  **Service**:
    *   Use **Gunicorn** with Gevent workers: `gunicorn -k gevent -w 4 -b 127.0.0.1:8000 app:app`
    *   Set up **Nginx** as reverse proxy (SSL Termination via Certbot).
