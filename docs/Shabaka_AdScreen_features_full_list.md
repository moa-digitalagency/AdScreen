![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue) ![Framework](https://img.shields.io/badge/Framework-Flask-green) ![Database](https://img.shields.io/badge/Database-PostgreSQL-orange) ![Status](https://img.shields.io/badge/Status-Proprietary-red) ![License](https://img.shields.io/badge/License-MOA%20Private-red) ![Owner](https://img.shields.io/badge/Owner-MOA%20Digital%20Agency-purple)

# Shabaka AdScreen - Full Features List (The Bible) / Liste Exhaustive des Fonctionnalités

**ENGLISH VERSION BELOW | VERSION FRANÇAISE PLUS BAS**

---

## 🇬🇧 ENGLISH VERSION

This document is the absolute reference for all features, business rules, validations, and system behaviors of the Shabaka AdScreen platform. It serves as the source of truth for developers, testers, and auditors.

### 1. Core System

#### 1.1 Authentication & Security
*   **Password Hashing**: Uses `werkzeug.security` (Scrypt by default, or PBKDF2-SHA256 depending on config) for secure storage.
*   **Session Management**:
    *   Cookies `HttpOnly`, `SameSite=Lax`.
    *   `Secure` flag enabled in production (via env var `FLASK_ENV=production`).
    *   Protection against session hijacking via ID regeneration.
*   **CSRF Protection (Cross-Site Request Forgery)**:
    *   Manual implementation via `app.before_request`.
    *   Unique token per session (`_csrf_token`).
    *   Verification on all `POST`, `PUT`, `DELETE`, `PATCH` methods.
    *   **Exceptions**: API Endpoints (`api.*`, `mobile_api.*`) and Webhooks (`billing.cron_generate_invoices`).
*   **Security Headers**:
    *   `X-Content-Type-Options: nosniff`
    *   `X-Frame-Options: SAMEORIGIN`
    *   `Referrer-Policy: strict-origin-when-cross-origin`
    *   `Strict-Transport-Security: max-age=31536000; includeSubDomains` (if HTTPS).
*   **Rate Limiting**:
    *   Library: `Flask-Limiter`.
    *   Storage: Memory (Dev) or Redis (Prod).
    *   Default Rules:
        *   Login: **5 requests / minute**.
        *   Mobile API (Read): **60 requests / minute**.
        *   Player Heartbeat: **120 requests / minute**.

#### 1.2 Input Validation
All incoming data is sanitized via `services/input_validator.py`.
*   **Strings**: HTML cleaning (removal of `<script>` tags, etc.) and truncation to 255 chars by default.
*   **Emails**: Validation via `email-validator` (RFC syntax check).
*   **Phones**: Regex `^\+?[\d]{8,15}$` (International format, 8 to 15 digits).
*   **Screen Codes**: Regex `^[A-Za-z0-9\-_]+$` (Alphanumeric, hyphens, underscores only).
*   **URLs**:
    *   Must start with `http://` or `https://`.
    *   **SSRF** Protection (Server-Side Request Forgery): DNS resolution and check that target IP is not private/local (unless exception).
*   **Dates**: Strict format `YYYY-MM-DD`.
*   **Positive Integers**: Strict boundary checks (min/max).

### 2. Screen Management

#### 2.1 Configuration
*   **Unique Identifier**: Randomly generated or manually defined code (validated by Regex).
*   **Resolution**: Width and Height in pixels (e.g., 1920x1080). Used to validate uploads.
*   **Orientation**: 'landscape' or 'portrait'.
*   **Operating Modes**:
    1.  **Playlist**: Loop of media content.
    2.  **IPTV**: Broadcast of HLS/M3U8 streams.
        *   Proxying support to bypass CORS.
        *   MPEG-TS to HLS on-the-fly conversion via FFmpeg (if enabled).

#### 2.2 Monitoring
*   **Heartbeat**: The player sends a ping every **30 seconds**.
*   **Statuses**:
    *   `Online`: Heartbeat received < 2 minutes ago.
    *   `Playing`: Currently playing content.
    *   `Offline`: No signal > 2 minutes.
*   **Logs**: History kept in `heartbeat_log` table.

### 3. Booking Engine

#### 3.1 Booking Modes
The system supports two distinct booking logics:
1.  **By Plays (Plays Mode)**:
    *   The client buys a fixed number of plays (e.g., 100 plays).
    *   Validity: Until quota exhaustion.
2.  **By Date (Dates Mode)**:
    *   The client buys a period (e.g., from 01/01 to 07/01).
    *   Goal: X plays per day.
    *   **Fair Distribution Algorithm**: The system calculates daily availability and smooths distribution over the period.

#### 3.2 Pricing Calculation
Exact formula applied in `booking_routes.py`:
```python
Base_Slot_Price = Screen_Minute_Price * (Slot_Duration / 60)
Unit_Price      = Base_Slot_Price * Period_Multiplier
Total_Price_Ex_Tax = Unit_Price * Total_Plays_Count
Total_Price_Inc_Tax = Total_Price_Ex_Tax * (1 + VAT_Rate / 100)
```
*   **TimeSlots**: Predefined durations (10s, 15s, 20s, 30s).
*   **TimePeriods**: Time ranges with multiplier (e.g., 6PM-11PM = x1.5).

#### 3.3 Uploaded Media Validation
*   **Images**:
    *   Formats: JPG, PNG, GIF, WebP.
    *   Dimensions: Must match screen resolution **to the pixel**.
    *   Size: Max 100 MB (config `MAX_CONTENT_LENGTH`).
*   **Videos**:
    *   Formats: MP4, WebM, MOV.
    *   Duration: Must be **less than or equal** to the booked slot (0 tolerance).
    *   Analysis: Use of `ffprobe` to extract duration and dimensions.

### 4. The Player (Display Logic)

#### 4.1 Content Prioritization
The playlist generation algorithm (`mobile_api_routes.py`) ranks content by decreasing priority score:
1.  **Broadcasts (200)**: Emergency/System messages.
2.  **Paid Content (100)**: Active paid ads (Quota > 0).
3.  **Internal Content (80)**: Venue self-promotion.
4.  **AdContent (50)**: Network ads (Third-party).
5.  **Fillers (20)**: Default filler content (e.g., "Scan this QR Code").

#### 4.2 Playback & Tracking
*   **Polling**: JSON playlist retrieval every **60 seconds**.
*   **Preloading**: Browser caching of assets to smooth transitions.
*   **Logging**: At each end of playback, the player calls `/log-play`.
    *   Decrements `remaining_plays` counter of the Booking.
    *   Sets status to `completed` if quota reached.
    *   Records an entry in `stat_log` for reports.

#### 4.3 Overlays
*   **Tickers**: Scrolling texts configurable (Speed, Color, Position).
*   **Logic**: Can be associated with a specific period or permanent.
*   **Compatibility**: Works over Video mode AND IPTV mode.

### 5. Mobile API (Management)

The `/mobile/api/v1` API is dedicated to management apps (Flutter/React Native).

#### 5.1 Specific Error Codes
In addition to standard HTTP codes, the API returns business codes in JSON (`code`):
*   `MISSING_PASSWORD`: Password not provided.
*   `INVALID_CREDENTIALS`: Email/Code or password incorrect.
*   `ACCOUNT_DISABLED`: User disabled by admin.
*   `SCREEN_DISABLED`: Screen disabled.
*   `REFRESH_FAILED`: Refresh token invalid or expired.
*   `SCREEN_NOT_FOUND`: Screen ID non-existent or out of org scope.
*   `VALIDATION_ERROR`: Data validation failure (details in `field` field).

#### 5.2 JWT Authentication
*   **Access Token**: 24-hour expiration. Contains `user_id`, `role`, `organization_id`.
*   **Refresh Token**: 30-day expiration. Allows getting a new Access Token without relogin.

### 6. Billing & Finance

#### 6.1 Lifecycle
1.  **Generation**: Cron Job (`billing_routes.py`) executed **Sunday at 11:59 PM**.
2.  **Calculation**: Sum of paid `Booking`s from the past week.
3.  **Commission**: Application of platform percentage (defined by Organization).
4.  **State**: `pending` -> `paid` (Proof sent) -> `validated` (Money received).

#### 6.2 Currencies
*   Multi-currency support (EUR, USD, TND, etc.).
*   Currency symbol is injected globally via `inject_currency` Context Processor.

### 7. Internationalization (i18n)

*   **Mechanism**: Custom service `services/translation_service.py`.
*   **Storage**: Flat JSON files.
*   **Detection**:
    1.  URL `/set-language/<lang>`.
    2.  Session cookie.
    3.  Browser `Accept-Language` header.
    4.  Default language (`fr`).

---

## 🇫🇷 VERSION FRANÇAISE

Ce document est la référence absolue de toutes les fonctionnalités, règles métier, validations et comportements système de la plateforme Shabaka AdScreen. Il sert de vérité terrain pour les développeurs, testeurs et auditeurs.

### 1. Cœur du Système (Core)

#### 1.1 Authentification & Sécurité
*   **Hashage Mot de Passe** : Utilisation de `werkzeug.security` (Scrypt par défaut, ou PBKDF2-SHA256 selon configuration) pour le stockage sécurisé.
*   **Session Management** :
    *   Cookies `HttpOnly`, `SameSite=Lax`.
    *   `Secure` flag activé en production (via variable d'env `FLASK_ENV=production`).
    *   Protection contre le vol de session via régénération d'ID.
*   **Protection CSRF (Cross-Site Request Forgery)** :
    *   Implémentation manuelle via `app.before_request`.
    *   Token unique par session (`_csrf_token`).
    *   Vérification sur toutes les méthodes `POST`, `PUT`, `DELETE`, `PATCH`.
    *   **Exceptions** : Endpoints API (`api.*`, `mobile_api.*`) et Webhooks (`billing.cron_generate_invoices`).
*   **En-têtes de Sécurité (Security Headers)** :
    *   `X-Content-Type-Options: nosniff`
    *   `X-Frame-Options: SAMEORIGIN`
    *   `Referrer-Policy: strict-origin-when-cross-origin`
    *   `Strict-Transport-Security: max-age=31536000; includeSubDomains` (si HTTPS).
*   **Rate Limiting** :
    *   Librairie : `Flask-Limiter`.
    *   Stockage : Mémoire (Dev) ou Redis (Prod).
    *   Règles par défaut :
        *   Login : **5 requêtes / minute**.
        *   API Mobile (Lecture) : **60 requêtes / minute**.
        *   Player Heartbeat : **120 requêtes / minute**.

#### 1.2 Validation des Entrées (Input Validation)
Toutes les données entrantes sont assainies via `services/input_validator.py`.
*   **Chaînes de caractères** : Nettoyage HTML (suppression des balises `<script>`, etc.) et troncature à 255 caractères par défaut.
*   **E-mails** : Validation via `email-validator` (vérification syntaxique RFC).
*   **Téléphones** : Regex `^\+?[\d]{8,15}$` (Format international, 8 à 15 chiffres).
*   **Codes Écrans** : Regex `^[A-Za-z0-9\-_]+$` (Alphanumérique, tirets, underscores uniquement).
*   **URLs** :
    *   Doit commencer par `http://` ou `https://`.
    *   Protection **SSRF** (Server-Side Request Forgery) : Résolution DNS et vérification que l'IP cible n'est pas privée/locale (sauf exception).
*   **Dates** : Format strict `YYYY-MM-DD`.
*   **Entiers Positifs** : Vérification stricte des bornes (min/max).

### 2. Gestion des Écrans (Screen Management)

#### 2.1 Configuration
*   **Identifiant Unique** : Code généré aléatoirement ou défini manuellement (validé par Regex).
*   **Résolution** : Largeur et Hauteur en pixels (ex: 1920x1080). Utilisé pour valider les uploads.
*   **Orientation** : 'landscape' (Paysage) ou 'portrait' (Portrait).
*   **Modes de Fonctionnement** :
    1.  **Playlist** : Boucle de contenus médias.
    2.  **IPTV** : Diffusion de flux HLS/M3U8.
        *   Support du Proxying pour contourner CORS.
        *   Conversion MPEG-TS vers HLS à la volée via FFmpeg (si activé).

#### 2.2 Monitoring
*   **Heartbeat** : Le player envoie un ping toutes les **30 secondes**.
*   **Statuts** :
    *   `Online` : Heartbeat reçu < 2 minutes.
    *   `Playing` : En cours de lecture.
    *   `Offline` : Aucun signal > 2 minutes.
*   **Logs** : Historique conservé dans la table `heartbeat_log`.

### 3. Moteur de Réservation (Booking Engine)

#### 3.1 Modes de Réservation
Le système supporte deux logiques de réservation distinctes :
1.  **Par Nombre de Diffusions (Plays Mode)** :
    *   Le client achète un nombre fixe de passages (ex: 100 diffusions).
    *   Validité : Jusqu'à épuisement du quota.
2.  **Par Date (Dates Mode)** :
    *   Le client achète une période (ex: du 01/01 au 07/01).
    *   Objectif : X diffusions par jour.
    *   **Algorithme de Distribution Équitable** : Le système calcule la disponibilité journalière et lisse la diffusion sur la période.

#### 3.2 Calcul du Prix
Formule exacte appliquée dans `booking_routes.py` :
```python
Prix_Base_Slot = Prix_Minute_Ecran * (Duree_Slot / 60)
Prix_Unitaire  = Prix_Base_Slot * Multiplicateur_Periode
Prix_Total_HT  = Prix_Unitaire * Nombre_Total_Diffusions
Prix_TTC       = Prix_Total_HT * (1 + Taux_TVA / 100)
```
*   **TimeSlots** : Durées prédéfinies (10s, 15s, 20s, 30s).
*   **TimePeriods** : Plages horaires avec multiplicateur (ex: 18h-23h = x1.5).

#### 3.3 Validation des Médias Uploadés
*   **Images** :
    *   Formats : JPG, PNG, GIF, WebP.
    *   Dimensions : Doit correspondre **au pixel près** à la résolution de l'écran.
    *   Poids : Max 100 Mo (config `MAX_CONTENT_LENGTH`).
*   **Vidéos** :
    *   Formats : MP4, WebM, MOV.
    *   Durée : Doit être **inférieure ou égale** au slot réservé (tolérance 0).
    *   Analyse : Utilisation de `ffprobe` pour extraire durée et dimensions.

### 4. Le Player (Logique d'Affichage)

#### 4.1 Priorisation des Contenus
L'algorithme de génération de playlist (`mobile_api_routes.py`) classe les contenus par score de priorité décroissant :
1.  **Broadcasts (200)** : Messages d'urgence/système (ex: "Fermeture exceptionnelle").
2.  **Paid Content (100)** : Publicités payantes actives (Quota > 0).
3.  **Internal Content (80)** : Auto-promotion de l'établissement.
4.  **AdContent (50)** : Publicités régie (Réseau tiers).
5.  **Fillers (20)** : Contenu de remplissage par défaut (ex: "Scannez ce QR Code").

#### 4.2 Lecture & Tracking
*   **Polling** : Récupération de la playlist JSON toutes les **60 secondes**.
*   **Preloading** : Mise en cache navigateur des assets pour fluidifier les transitions.
*   **Logging** : À chaque fin de lecture, le player appelle `/log-play`.
    *   Décrémente le compteur `remaining_plays` du Booking.
    *   Passe le statut à `completed` si le quota est atteint.
    *   Enregistre une entrée dans `stat_log` pour les rapports.

#### 4.3 Overlays (Superposition)
*   **Tickers** : Textes défilants configurables (Vitesse, Couleur, Position).
*   **Logique** : Peuvent être associés à une période spécifique ou être permanents.
*   **Compatibilité** : Fonctionnent par-dessus le mode Vidéo ET le mode IPTV.

### 5. API Mobile (Management)

L'API `/mobile/api/v1` est dédiée aux applications de gestion (Flutter/React Native).

#### 5.1 Codes d'Erreur Spécifiques
En plus des codes HTTP standards, l'API retourne des codes métier dans le JSON (`code`):
*   `MISSING_PASSWORD` : Mot de passe non fourni.
*   `INVALID_CREDENTIALS` : Email/Code ou mot de passe incorrect.
*   `ACCOUNT_DISABLED` : L'utilisateur a été désactivé par un admin.
*   `SCREEN_DISABLED` : L'écran a été désactivé.
*   `REFRESH_FAILED` : Token de rafraîchissement invalide ou expiré.
*   `SCREEN_NOT_FOUND` : ID d'écran inexistant ou hors périmètre organisation.
*   `VALIDATION_ERROR` : Échec de validation des données (détails dans le champ `field`).

#### 5.2 Authentification JWT
*   **Access Token** : Expiration 24 heures. Contient `user_id`, `role`, `organization_id`.
*   **Refresh Token** : Expiration 30 jours. Permet d'obtenir un nouveau Access Token sans relogin.

### 6. Facturation & Finance

#### 6.1 Cycle de Vie
1.  **Génération** : Cron Job (`billing_routes.py`) exécuté le **Dimanche à 23h59**.
2.  **Calcul** : Somme des `Booking` payés de la semaine passée.
3.  **Commission** : Application du pourcentage plateforme (défini par Organisation).
4.  **État** : `pending` -> `paid` (Preuve envoyée) -> `validated` (Argent reçu).

#### 6.2 Devises
*   Support multi-devises (EUR, USD, TND, etc.).
*   Le symbole monétaire est injecté globalement via le Context Processor `inject_currency`.

### 7. Internationalisation (i18n)

*   **Mécanisme** : Service custom `services/translation_service.py`.
*   **Stockage** : Fichiers JSON plats.
*   **Détection** :
    1.  URL `/set-language/<lang>`.
    2.  Cookie de session.
    3.  Header `Accept-Language` du navigateur.
    4.  Langue par défaut (`fr`).
