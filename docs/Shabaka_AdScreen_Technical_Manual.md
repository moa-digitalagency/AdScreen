![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue) ![Framework](https://img.shields.io/badge/Framework-Flask-green) ![Database](https://img.shields.io/badge/Database-PostgreSQL-orange) ![Status](https://img.shields.io/badge/Status-Proprietary-red) ![License](https://img.shields.io/badge/License-MOA%20Private-red) ![Owner](https://img.shields.io/badge/Owner-MOA%20Digital%20Agency-purple)

# Shabaka AdScreen - Technical Manual / Manuel Technique

**ENGLISH VERSION BELOW | VERSION FRANÇAISE PLUS BAS**

---

## 🇬🇧 ENGLISH VERSION

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

---

## 🇫🇷 VERSION FRANÇAISE

Ce document regroupe l'architecture technique, l'audit de sécurité, le schéma de base de données, la référence API et le guide de déploiement de la plateforme Shabaka AdScreen.

### 1. Vue d'Ensemble de l'Architecture

Shabaka AdScreen est une application **Monolithique Modulaire** robuste construite sur le framework **Flask** (Python). Elle suit le modèle **MVC (Modèle-Vue-Contrôleur)** :
*   **Modèles** : Définis avec **SQLAlchemy** (ORM).
*   **Vues** : Templating **Jinja2** couplé à **Tailwind CSS**.
*   **Contrôleurs** : Routes organisées en **Blueprints**.

#### Structure du Projet
L'application est structurée autour de Blueprints pour isoler les domaines fonctionnels :
```
/
├── app.py                 # Point d'entrée, config, init des extensions
├── models/                # Définitions des schémas de BDD
│   ├── user.py            # Gestion des utilisateurs et rôles
│   ├── screen.py          # Configuration des écrans
│   ├── booking.py         # Logique de réservation
│   └── ...
├── routes/                # Contrôleurs (Blueprints)
│   ├── auth_routes.py     # Login, Register
│   ├── admin_routes.py    # Back-office Superadmin
│   ├── org_routes.py      # Dashboard Organisation
│   ├── screen_routes.py   # Gestion technique des écrans
│   ├── booking_routes.py  # Tunnel de réservation public
│   ├── player_routes.py   # Logique d'affichage Player
│   ├── mobile_api_routes.py # API JSON pour App Mobile
│   └── ...
├── services/              # Logique métier complexe
│   ├── hls_converter.py   # Proxy et Conversion Vidéo (FFmpeg)
│   ├── playlist_service.py # Algorithme de sélection de contenu
│   └── billing_service.py # Génération de factures hebdo
└── static/                # Assets (CSS, JS, Uploads)
```

### 2. Stack Technologique

*   **Backend** : Python 3.11+, Flask 3.0+, Gunicorn, Gevent.
*   **Base de Données** : PostgreSQL 14+ (Production), SQLite (Dev). ORM : SQLAlchemy 2.0+.
*   **Frontend** : Jinja2 (SSR), Tailwind CSS 3.4, Vanilla JS (ES6+), hls.js.
*   **Média** : FFmpeg (Transcodage/Streaming), Pillow (Traitement d'images).
*   **Sécurité** : Flask-Login (Session), PyJWT (Token API), Bleach (Assainissement), Flask-Limiter.

### 3. Schéma de Base de Données

#### Identité et Accès
*   `User` : `id`, `email`, `password_hash`, `role` (superadmin, admin, manager), `organization_id`.
*   `Organization` : `id`, `name`, `currency`, `commission_rate`, `vat_rate`.

#### Infrastructure
*   `Screen` : `id`, `unique_code`, `resolution_width`, `resolution_height`, `orientation`, `current_mode` (playlist/iptv).
*   `TimeSlot` : `duration_seconds` (10, 15, 30), `price_per_play`.
*   `TimePeriod` : `start_hour`, `end_hour`, `price_multiplier`.

#### Contenu et Réservation
*   `Content` : `filename`, `content_type` (image/video), `status`, `duration_seconds`.
*   `Booking` : `num_plays` (quota acheté), `plays_completed`, `total_price`, `status`.
*   `Invoice` : `week_start`, `gross_revenue`, `commission_amount`, `status` (pending/paid).

#### Logs
*   `StatLog` : Preuve de diffusion (`played_at`, `duration`).
*   `HeartbeatLog` : Historique de connectivité du player.

### 4. Audit de Sécurité

#### 4.1 Authentification
*   **Hachage** : PBKDF2-SHA256 via `werkzeug.security`.
*   **Sessions** : `HttpOnly`, `SameSite=Lax`, `Secure` (Prod).
*   **JWT** : Utilisé pour l'API Mobile (Access Token 24h, Refresh Token 30j).

#### 4.2 Mécanismes de Protection
*   **CSRF** : Validation manuelle des tokens sur toutes les méthodes changeant l'état (`POST`, `PUT`, `DELETE`), sauf endpoints API.
*   **Rate Limiting** :
    *   Login : 5 req/min.
    *   API Mobile : 60 req/min.
    *   Player Heartbeat : 120 req/min.
*   **En-têtes** : `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `HSTS`.

#### 4.3 Validation des Entrées
*   **Uploads** : Vérification stricte du type MIME (Magic numbers) via Pillow/ffprobe. Fichiers renommés avec UUIDs.
*   **SSRF** : Le proxy de streaming valide les IPs cibles pour empêcher le scan du réseau local.

### 5. Référence API

#### 5.1 Management API (`/mobile/api/v1`)
*   **Auth** : Bearer Token (JWT).
*   `POST /auth/login` : Obtention des tokens Access/Refresh.
*   `GET /dashboard/summary` : Statistiques de l'organisation.
*   `GET /dashboard/screens` : Liste des écrans et statut.

#### 5.2 Player API (`/player/api`)
*   **Auth** : Cookie de Session.
*   `GET /playlist` : Récupère la playlist JSON (Prochains éléments à jouer).
*   `POST /heartbeat` : Envoie le signal de vie.
*   `POST /log-play` : Signale la lecture d'un contenu (Décrémente le quota).

### 6. Guide de Déploiement

#### 6.1 Prérequis
*   VPS avec Ubuntu 20.04/22.04.
*   Python 3.11+, PostgreSQL, Nginx, FFmpeg.

#### 6.2 Étapes d'Installation
1.  **Cloner** : `git clone <repo_url>`
2.  **Env** : Créer un fichier `.env` avec `DATABASE_URL`, `SESSION_SECRET`, `FLASK_ENV=production`.
3.  **Deps** : `pip install -r requirements.txt`.
4.  **DB** : `python init_db.py`.
5.  **Service** :
    *   Utiliser **Gunicorn** avec des workers Gevent : `gunicorn -k gevent -w 4 -b 127.0.0.1:8000 app:app`
    *   Configurer **Nginx** comme reverse proxy (Terminaison SSL via Certbot).
