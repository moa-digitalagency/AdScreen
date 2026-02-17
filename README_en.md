![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue) ![Framework](https://img.shields.io/badge/Framework-Flask-green) ![Database](https://img.shields.io/badge/Database-PostgreSQL-orange) ![Status: Private/Internal](https://img.shields.io/badge/Status-Private%2FInternal-red) ![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red) ![Owner: MOA Digital Agency](https://img.shields.io/badge/Owner-MOA%20Digital%20Agency-purple)

[ 🇫🇷 Français ](README.md) | [ 🇬🇧 English ]

# SHABAKA ADSCREEN

> **WARNING:** This project is **PROPRIETARY** and **PRIVATE** software.
> **Owner:** MOA Digital Agency (myoneart.com)
> **Author:** Aisance KALONJI
> **License:** Strict internal use only. Any reproduction or distribution is prohibited.

---

## Description
**Shabaka AdScreen** is a complete SaaS platform for Digital Signage management. It orchestrates a network of connected screens, manages the sale of advertising space via a dynamic pricing algorithm, and ensures the smooth delivery of media content (Videos, Images).

## Technical Architecture

```mermaid
graph TD
    Client[Client / Advertiser] -->|HTTPS| Proxy[Nginx / Load Balancer]
    Screen[Physical Screen] -->|HTTPS| Proxy

    Proxy -->|WSGI| App[Flask Application (Monolithic)]

    subgraph "Core Application"
        App -->|Route| Blueprints{Blueprints}
        Blueprints -->|Admin| AdminBP[Admin Panel]
        Blueprints -->|SaaS| OrgBP[Org Dashboard]
        Blueprints -->|Public| BookingBP[Booking Engine]
        Blueprints -->|Device| PlayerBP[Player API]

        App -->|Auth| Security[Flask-Login / JWT]
        App -->|Task| Services[Business Services]
    end

    subgraph "Data & Storage"
        Services -->|ORM| DB[(PostgreSQL)]
        Services -->|I/O| Storage[File System / S3]
        Services -->|Cache| Cache[Redis / Memcached]
    end

    Services -->|Compute| Pricing[Pricing Service]
    Services -->|Logic| Playlist[Playlist Generator]

    PlayerBP -->|Heartbeat| Screen
    PlayerBP -->|JSON| Screen
```

## Table of Contents
1.  [Key Features](#key-features)
2.  [Installation & Startup](#installation--startup)
3.  [Documentation](#documentation)

## Key Features
*   **Multi-Tenant Management:** Autonomous organizations with their own screens.
*   **Dynamic Pricing:** Algorithm based on duration, period (Peak/Off-peak), and screen popularity.
*   **Smart Player:** Local caching, priority queue (Emergency > Paid > Internal), and offline operation.
*   **Automated Billing:** Invoice generation, commission calculation, and proof of play.

## Installation & Startup

### Prerequisites
*   Python 3.11+
*   PostgreSQL (or SQLite for dev)
*   FFmpeg (for video processing)

### Commands
```bash
# 1. Clone the repository (Internal only)
git clone <repo_url>

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize the database
python init_db.py

# 4. Start the development server
python main.py
```

## Documentation
For a deep understanding of the system, refer to the official documents in the `docs/` folder:

*   📖 **[Feature Bible](docs/Shabaka_AdScreen_features_full_list_en.md)**: Exhaustive list of business rules.
*   ⚙️ **[Technical Manual](docs/Shabaka_AdScreen_Technical_Manual_en.md)**: Stack, Architecture, Security.
*   🎓 **[User Guide](docs/Shabaka_AdScreen_User_Guide_en.md)**: Tutorials for Admins and Clients.
