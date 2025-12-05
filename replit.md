# Shabaka AdScreen - SaaS Location Écrans Publicitaires

## Overview
Shabaka AdScreen is a SaaS platform designed to enable establishments (bars, restaurants, shopping centers) to monetize their advertising screens through a self-service rental system. Advertisers can access the platform via a link or QR code, select time slots, upload appropriate content, make payments, and receive performance reports. The project aims to provide a comprehensive solution for screen monetization, offering flexibility and detailed control for both establishments and advertisers.

## Current State (December 2025)
- **Database initialized**: Schema ready for data with demo accounts
- **Demo data loaded**: 7 organizations, 10 screens, 4 countries, 5 broadcasts
- **Multi-currency support**: EUR, MAD, XOF, TND + 200 other currencies
- **208 countries** with 4,600+ cities for geographic targeting
- **Admin permissions**: Granular access control for sub-admins
- **OnlineTV streaming**: HLS.js integration for M3U/M3U8 stream playback with overlays support

### Demo Accounts (created by init_db_demo.py)
- **Superadmin**: admin@shabaka-adscreen.com / admin123
- **Admin Démo**: admin-demo@shabaka-adscreen.com / admin123
- **Establishments** (password: demo123):
  - FR: manager@restaurant-paris.fr, manager@bar-lyon.fr, manager@atlantis-mall.fr, manager@cafe-gratuit.fr (free)
  - MA: manager@cafe-marrakech.ma
  - SN: manager@dakar-beach.sn
  - TN: manager@tunis-cafe.tn
- **Player password**: screen123

### Design Standards (Generated Images)

#### QR Code Complet (Full Page)
- **Resolution**: Full screen resolution (responsive to device)
- **Layout**: Professional light-theme with emerald gradients
- **QR Size**: 25% of screen height
- **Styling**: Header/footer gradients (#10b981 to #14b8a6), centered QR with info
- **Colors**: Emerald theme (#10b981), accent light (#d1fae5), text dark (#0f172a)
- **Pattern**: Subtle dotted pattern background

#### Fillers (Default Content)
- **Resolution**: Actual screen resolution width × height (matches orientation)
- **Layout**: Responsive to screen dimensions and aspect ratio
- **QR Size**: 20% of screen width (proportional sizing)
- **Styling**: Gradient header/footer, centered QR, responsive text
- **Proportions**: All elements scale intelligently with screen size
- **Pattern**: Subtle dotted pattern

## User Preferences
Not specified.

## System Architecture

### UI/UX Decisions
- **Templates**: Jinja2 for dynamic content.
- **Styling**: Tailwind CSS (CDN) for a utility-first approach to design.
- **Icons**: Font Awesome for a rich icon library.
- **Fonts**: Inter and JetBrains Mono (Google Fonts) for modern typography.
- **Design Elements**:
    - Modern gradient backgrounds (emerald/green tones: #10b981, #059669, #34d399, #047857) with glassmorphism effects.
    - Decorative circles and wave effects for visual appeal.
    - Gradient accent bars and professional styling with shadows and rounded corners.
    - Responsive design for mobile and tablet, adapting content and layouts for various screen sizes (320px to 1920px).
    - Color-coded date/time sections (green/red) for clarity.
    - Real-time previews for overlay configurations and content validation.
    - Unified emerald brand color scheme across QR codes, fillers, and UI components.

### Technical Implementations
- **Backend Framework**: Flask (Python 3.11).
- **Database**: PostgreSQL with SQLAlchemy ORM.
- **Authentication**: Flask-Login using session management.
- **Media Validation**: Pillow for images and ffmpeg for videos, ensuring content adheres to specified ratios, resolutions, and durations.
- **QR Code Generation**: `qrcode[pil]` library.
- **Core Features**:
    - **User Roles**: Superadmin, Establishment (organization), Client/Advertiser, and Screen (player).
    - **Establishment Management**: CRUD operations, configurable slots and day periods, custom commissions, QR code generation.
    - **Registration System**: Form-based requests, WhatsApp notifications to admin, admin validation, account creation with custom commission.
    - **Screen Management**: Naming, live preview, multi-positional overlays (scrolling banners, static images), customizable colors, font sizes, scroll speeds, and overlay durations/frequencies.
    - **Content Management**: Strict upload validation, content queues, internal establishment content, filler/demo content, content action controls (suspend, activate, delete), resolution-adaptive previews, real-time admin playlist view.
    - **Booking System**: Unique reservation numbers, detailed receipts with QR codes, content adaptation, status tracking, precise time selection.
    - **Screen Player**: Fullscreen web player with auto-loop, real-time overlay display, heartbeat and status logging, playback statistics, 10-second control timeout, 30-second playlist refresh, audio support with mute toggle.
    - **OnlineTV Mode**: Stream live TV channels via M3U/HLS with HLS.js library, overlays remain active during streaming, automatic fallback for compatibility.
    - **MPEG-TS to HLS Conversion**: Server-side FFmpeg conversion for MPEG-TS streams that don't play natively in browsers.
    - **HLS Converter Service**: `services/hls_converter.py` manages FFmpeg processes, segment storage, and manifest rewriting.
    - **Segment Routes**: `/player/tv-stream/<code>` (manifest) and `/player/tv-segment/<code>/<segment>` (segments).
    - **Fallback Strategy**: Player tries direct MPEG-TS first via mpegts.js, then falls back to HLS conversion if needed.
    - **Smart Stream Detection**: Auto-detects MPEG-TS vs HLS based on URL patterns.
    - **Segment Persistence**: Segments are kept on disk (not deleted) to ensure player can fetch them reliably.
    - **Administration**: Site settings (SEO, commissions), configurable admin WhatsApp number, maintenance mode, global statistics.
    - **Weekly Automated Billing**: Automatic invoice generation, revenue/commission summaries, payment proof upload/validation.
    - **Playlist Priorities**: Paid content (100) > Internal content (80) > Broadcast content (200) > Fillers/Demos (20).
    - **Overlay System**: Comprehensive configuration for tickers (header, body, footer) and image overlays (all positions + custom X/Y, size, opacity), with real-time previews.
    - **Overlay Priority System** (December 2025):
        - **Priority levels**: Configurable 1-100 (higher priority displays first)
        - **Source tracking**: LOCAL (organization-created) vs BROADCAST (super-admin pushed)
        - **Pause/Resume**: Organization users can pause, resume, or delete overlays locally
        - **Broadcast priority**: Broadcast overlays automatically take priority (priority=100)
        - **Auto-pause**: When broadcast overlays are active, local overlays with same/lower priority are automatically paused
        - **Auto-resume**: When broadcast ends, previously paused local overlays automatically resume
        - **Status indicators**: Visual badges showing paused, broadcast source, and priority level
    - **Broadcast/Diffusion System**: Superadmin feature to push content to connected screens based on geographic and organizational targeting:
        - **Targeting modes**: Country, city, organization, or specific screen
        - **Organization type targeting**: Filter by paid establishments only, free establishments only, or all
        - **Content types**: Overlay (ticker, image, corner) or playlist content
        - **Scheduling modes**: Immediate (instant activation) or Scheduled (specific datetime)
        - **Advanced scheduling** (December 2025):
            - **Recurrence patterns**: One-time, daily, weekly (with day selection), monthly
            - **Priority system**: Configurable 20-200 (higher priority plays first)
            - **Override playlist**: Option to shift existing content for scheduled broadcasts
            - **Recurrence configuration**: Interval, end date, time of day, days of week
        - **Hierarchical targeting**: Selecting a country affects all active screens in that country
        - **Integration**: Broadcasts automatically appear in player API responses when active
    - **Multi-tenant Support**:
        - **Paid vs Free Establishments**: `is_paid` flag on organizations controls feature access
        - **Feature Restrictions**: Free establishments limited to internal content and overlays (no booking, billing, time slots)
        - **Decorator-based Access Control**: `@paid_org_required` decorator for paid-only routes
        - **Conditional UI**: Menus dynamically show/hide based on establishment type
    - **Ad Content Control** (December 2025):
        - **allow_ad_content**: Organization-level toggle to accept/reject superadmin advertising content
        - **Default behavior**: Opt-in (TRUE by default) - all organizations accept ads unless explicitly disabled
        - **Settings location**: Toggle in organization settings under "Publicité" section
        - **Filtering logic**: AdContent targets respect organization preferences during delivery
        - **NULL handling**: NULL values treated as TRUE to maintain default-on behavior
    - **Superadmin Authentication**:
        - **Environment Variables**: SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD for secure credential storage
        - **Dynamic Verification**: Credentials verified at login time from environment
    - **Admin User Management**:
        - **Role-based Permissions**: ADMIN_PERMISSIONS dictionary with granular access control
        - **Permission Categories**: broadcasts, organizations, screens, users, reports, settings, bookings, billing
        - **User CRUD**: Full admin interface for creating, editing, and managing admin users
    - **Featured Screens**: Super-admins can mark screens for homepage display.
    - **Custom QR Codes**: Simple black/white or detailed QR codes with establishment/screen info.
    - **Advanced Site Settings**: SEO (title, description, keywords, OG image, favicon, Google Analytics), social media links, custom `<head>` code injection, contact info.
    - **Multi-Currency Support**: Dynamic currency display and price calculation based on organization settings, period multipliers, and content duration handling (video last-frame hold).
    - **Public Catalog**: A `/catalog` page displaying available screens, grouped by country and organization, with screen details, accepted formats, indicative prices, and booking buttons.
    - **Customizable Registration Number Label**: Allows organizations to define country-specific labels (e.g., SIRET, ICE, NINEA).
    - **City Selection**: Organizations can specify their city via dynamic dropdown with autocomplete, populated from `utils/world_data.py`. API endpoint `/api/cities/<country_code>` returns cities for a given country code.
    - **World Data Coverage**: 208 countries with ISO codes, flags, continents and default currencies. Over 4,600 cities with 15-30 cities per country (average 22). Dynamic AJAX-based city loading for better UX.

## External Dependencies
- **PostgreSQL**: Primary database for all application data.
- **Pillow**: Python Imaging Library for image processing and validation.
- **ffmpeg**: For video processing and validation.
- **qrcode[pil]**: Python library for generating QR codes.
- **Tailwind CSS (CDN)**: For front-end styling.
- **Font Awesome**: For icons.
- **Google Fonts (Inter, JetBrains Mono)**: For typography.
- **European Central Bank (ECB) API**: For real-time currency exchange rates, used in the admin dashboard for currency conversion.
- **WhatsApp**: For admin notifications regarding registration requests and contact.
- **Gunicorn**: Production WSGI HTTP Server.
- **HLS.js**: JavaScript library for HTTP Live Streaming (HLS) in browsers, used for OnlineTV M3U stream playback.