# Shabaka AdScreen - SaaS Location Écrans Publicitaires

## Overview
Shabaka AdScreen is a SaaS platform designed to enable establishments (bars, restaurants, shopping centers) to monetize their advertising screens through a self-service rental system. Advertisers can access the platform via a link or QR code, select time slots, upload appropriate content, make payments, and receive performance reports. The project aims to provide a comprehensive solution for screen monetization, offering flexibility and detailed control for both establishments and advertisers.

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
    - **Screen Player**: Fullscreen web player with auto-loop, real-time overlay display, heartbeat and status logging, playback statistics, 10-second control timeout, 30-second playlist refresh.
    - **Administration**: Site settings (SEO, commissions), configurable admin WhatsApp number, maintenance mode, global statistics.
    - **Weekly Automated Billing**: Automatic invoice generation, revenue/commission summaries, payment proof upload/validation.
    - **Playlist Priorities**: Paid content (100) > Internal content (80) > Broadcast content (200) > Fillers/Demos (20).
    - **Overlay System**: Comprehensive configuration for tickers (header, body, footer) and image overlays (all positions + custom X/Y, size, opacity), with real-time previews.
    - **Broadcast/Diffusion System**: Superadmin feature to push content to connected screens based on geographic and organizational targeting:
        - **Targeting modes**: Country, city, organization, or specific screen
        - **Content types**: Overlay (ticker, image, corner) or playlist content
        - **Scheduling**: Optional start/end datetime for timed broadcasts
        - **Hierarchical targeting**: Selecting a country affects all active screens in that country
        - **Integration**: Broadcasts automatically appear in player API responses when active
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