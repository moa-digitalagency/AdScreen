# Shabaka AdScreen - SaaS Location Écrans Publicitaires

## Overview
Shabaka AdScreen is a SaaS platform designed for establishments to monetize their advertising screens through a self-service rental system. Advertisers can book time slots, upload content, make payments, and receive performance reports. The platform provides a comprehensive solution for screen monetization, offering flexibility and control for both establishments and advertisers, aiming for significant market potential in the advertising display sector.

## User Preferences
Not specified.

## System Architecture

### UI/UX Decisions
The platform utilizes Jinja2 templates, styled with Tailwind CSS v3.4 for a utility-first approach. Font Awesome and Google Fonts (Inter, JetBrains Mono) are used for iconography and typography. Design elements include modern gradient backgrounds (emerald/green tones), glassmorphism effects, decorative circles, and wave effects. The design is responsive, adapting to various screen sizes, with color-coded sections, real-time content previews, and a unified emerald brand color scheme.

### Technical Implementations
The backend is built with Flask (Python 3.11) and uses PostgreSQL with SQLAlchemy ORM. Flask-Login manages authentication. Key features include:

-   **User Roles**: Superadmin, Establishment, Client/Advertiser, and Screen (player).
-   **Establishment Management**: CRUD, configurable slots, commissions, QR code generation.
-   **Registration System**: Form-based requests, admin validation, WhatsApp notifications.
-   **Screen Management**: Naming, live preview, multi-positional overlays (scrolling banners, static images) with customizable styles, durations, and frequencies.
-   **Content Management**: Strict validation (Pillow for images, FFmpeg for videos), content queues, internal content, filler content, and content action controls.
-   **Booking System**: Unique reservation numbers, detailed receipts, and precise time selection.
-   **Screen Player**: Fullscreen web player with auto-loop, real-time overlay display, heartbeat logging, playback statistics, and audio support.
-   **Offline Caching**: Service Worker-based offline support with IndexedDB storage, automatic media pre-caching, and log queue synchronization on reconnection.
-   **OnlineTV Mode**: Integrates HLS.js for M3U/HLS stream playback with active overlays.
-   **Adaptive Bitrate Streaming (ABR)**: Automatically adjusts video quality based on bandwidth, with buffer optimization and real-time quality indicators.
-   **MPEG-TS to HLS Conversion**: Server-side FFmpeg conversion for non-native MPEG-TS streams, with a robust fallback strategy.
-   **Administration**: Site settings (SEO, commissions), maintenance mode, global statistics, and automated weekly billing.
-   **Internal Content**: Managed with the same algorithms as client bookings for availability and distribution.
-   **Playlist Priorities**: Structured hierarchy from Paid content (100) to Fillers/Demos (20), with Broadcast content (200) having highest priority.
-   **Overlay Priority System**: Configurable priority levels (1-100), tracking of LOCAL vs BROADCAST sources, and auto-pause/resume functionality for local overlays during broadcast.
-   **Broadcast/Diffusion System**: Superadmin feature for targeting screens geographically or by organization with various content types (overlay, playlist) and advanced scheduling (recurrence patterns, priority, override options).
-   **Multi-tenant Support**: Differentiates between paid and free establishments with feature restrictions and decorator-based access control.
-   **Ad Content Control**: Organization-level toggle (`allow_ad_content`) for accepting/rejecting superadmin advertising content, defaulting to opt-in.
-   **Superadmin Authentication**: Securely managed via environment variables.
-   **Admin User Management**: Role-based permissions and full CRUD interface for admin users.
-   **Custom QR Codes**: Generated with `qrcode[pil]` library.
-   **Advanced Site Settings**: Comprehensive SEO, social media, and custom code injection options.
-   **Multi-Currency Support**: Dynamic currency display and calculations.
-   **Public Catalog**: Displays available screens with details and booking options.
-   **Customizable Registration Number Label**: Allows country-specific labels.
-   **City Selection**: Dynamic dropdown with autocomplete populated from `utils/world_data.py`.
-   **World Data Coverage**: Comprehensive data for 208 countries and over 4,600 cities.

### CSS Theme System
The project uses a comprehensive, reusable CSS theme template based on an emerald/teal color palette, defined via CSS custom properties. It includes pre-designed components for buttons, cards, badges, forms, navigation, notifications, and more, all customizable by updating root CSS variables.

### VPS Deployment
The platform supports standalone VPS deployment with:
-   **init_db.py**: Standalone database initialization script with INIT_DB_MODE to prevent side effects during schema sync.
-   **systemd Integration**: Service file with ExecStartPre for automatic database schema updates on restart.
-   **Environment File**: Secure configuration via `.env` file instead of inline environment variables.
-   **Nginx Configuration**: Optimized reverse proxy settings for streaming with proper timeout and buffer settings.

## External Dependencies
-   **PostgreSQL**: Primary database.
-   **Pillow**: Image processing and validation.
-   **ffmpeg**: Video processing and validation.
-   **qrcode[pil]**: QR code generation.
-   **Tailwind CSS (CDN)**: Front-end styling.
-   **Font Awesome**: Icons.
-   **Google Fonts**: Typography (Inter, JetBrains Mono).
-   **European Central Bank (ECB) API**: Real-time currency exchange rates.
-   **WhatsApp**: Admin notifications.
-   **Gunicorn**: Production WSGI HTTP Server.
-   **HLS.js**: HTTP Live Streaming playback.
-   **mpegts.js**: MPEG-TS stream playback fallback.