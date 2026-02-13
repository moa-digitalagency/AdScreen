# Shabaka AdScreen - Audit de Sécurité

Ce document détaille les mesures de sécurité implémentées dans l'application pour protéger les données, l'infrastructure et les utilisateurs.

## 1. Authentification et Sessions

### 1.1 Gestion des Mots de Passe
*   **Hachage** : Utilisation de `werkzeug.security.generate_password_hash` avec l'algorithme **PBKDF2-SHA256** (standard NIST).
*   **Stockage** : Aucun mot de passe n'est stocké en clair.
*   **Politique** : Les mots de passe ne sont jamais retournés par l'API.

### 1.2 Sessions Web
*   **Cookies** : Configuré avec `HttpOnly=True` (protection XSS) et `SameSite='Lax'` (protection CSRF).
*   **Secure Flag** : Activé automatiquement en production (`SESSION_COOKIE_SECURE=True`).
*   **Clé de signature** : Définie par la variable d'environnement `SESSION_SECRET`.

### 1.3 Tokens API (JWT)
*   **Access Token** : Expiration courte (24h).
*   **Refresh Token** : Expiration longue (30j), hashé en base de données. Permet la révocation en cas de compromission.
*   **Décorateurs** : `@jwt_required` assure la validation de la signature à chaque requête protégée.

## 2. Protection des Requêtes

### 2.1 CSRF (Cross-Site Request Forgery)
Une protection CSRF personnalisée est implémentée dans `app.py` :
*   Un token unique est généré par session.
*   Il est injecté dans tous les formulaires HTML via `inject_csrf_token`.
*   Le middleware `validate_csrf_token` vérifie sa présence pour toutes les méthodes mutantes (`POST`, `PUT`, `DELETE`).
*   Les endpoints API stateless sont exclus explicitement.

### 2.2 Rate Limiting (Anti-Brute Force)
La librairie `Flask-Limiter` protège les endpoints critiques :
*   **Login Web** : 5 tentatives / minute.
*   **Login API** : 5 tentatives / minute.
*   **Player Heartbeat** : 120 requêtes / minute (pour prévenir le déni de service interne).
*   **API Publique** : Limites configurables par IP.

### 2.3 En-têtes de Sécurité
L'application injecte systématiquement les en-têtes suivants :
*   `X-Content-Type-Options: nosniff`
*   `X-Frame-Options: SAMEORIGIN` (Protection Clickjacking)
*   `Referrer-Policy: strict-origin-when-cross-origin`
*   `Strict-Transport-Security` (HSTS) en production.

## 3. Validation des Données

### 3.1 Uploads de Fichiers
Le module d'upload (`booking_routes.py`, `utils/image_utils.py`) applique une politique stricte :
*   **Renommage** : Tous les fichiers sont renommés avec un UUID aléatoire pour éviter les collisions et l'exécution de code (`shell.php.jpg`).
*   **Extensions** : Liste blanche stricte (`.jpg`, `.png`, `.mp4`, ...).
*   **Contenu** : Vérification réelle du type MIME via `Pillow` (Images) et `ffprobe` (Vidéos).

### 3.2 SSRF (Server-Side Request Forgery)
Le proxy de streaming (`player_routes.py`) est un vecteur potentiel d'attaque SSRF. Mesures prises :
*   Validation des protocoles autorisés (`http`, `https`, `udp`, `rtmp`, `rtsp`).
*   Interdiction des accès aux IPs locales/privées (via `ipaddress`).
*   Limitation du nombre de redirections suivies par le client HTTP.

## 4. Infrastructure

### 4.1 Isolation
*   L'application tourne sous un utilisateur système dédié (`shabaka`) sans privilèges root.
*   La base de données utilise un utilisateur PostgreSQL dédié.

### 4.2 Secrets
*   Toutes les clés sensibles (`DATABASE_URL`, `SESSION_SECRET`) sont chargées depuis des variables d'environnement, jamais hardcodées.
