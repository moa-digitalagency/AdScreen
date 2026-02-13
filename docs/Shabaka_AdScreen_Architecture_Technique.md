# Shabaka AdScreen - Architecture Technique

Ce document détaille l'architecture logicielle, les choix technologiques et les flux de données de la plateforme Shabaka AdScreen. Il est destiné aux développeurs et aux architectes système.

## 1. Vue d'Ensemble

Shabaka AdScreen est une application monolithique modulaire construite sur le framework **Flask** (Python). Elle suit le modèle **MVC (Modèle-Vue-Contrôleur)**, où :
*   **Modèles** : Définis avec **SQLAlchemy** (ORM).
*   **Vues** : Templating **Jinja2** couplé à **Tailwind CSS**.
*   **Contrôleurs** : Routes organisées en **Blueprints**.

L'application expose également une **API RESTful** sécurisée pour les applications mobiles et les players.

## 2. Stack Technologique

### 2.1 Backend (Python 3.11+)
*   **Framework Web** : `Flask 3.0+`.
*   **Serveur WSGI** : `Gunicorn` (Production) / `Werkzeug` (Dev).
*   **Base de Données** : `PostgreSQL` (Production) / `SQLite` (Dev).
*   **ORM** : `SQLAlchemy 2.0+` avec `Flask-SQLAlchemy`.
*   **Authentification** :
    *   Web : `Flask-Login` (Sessions, Cookies sécurisés).
    *   API : `PyJWT` (JSON Web Tokens).
*   **Sécurité** : `Flask-Limiter` (Rate Limiting), `Bleach` (Sanitization), CSRF manuel (Tokens).
*   **Traitement Média** : `Pillow` (Images), `FFmpeg` (Vidéos/Streaming via `subprocess`).
*   **Tâches de fond** : `Gevent` (Async workers pour Gunicorn).

### 2.2 Frontend
*   **Templating** : Jinja2 (Rendu côté serveur).
*   **CSS Framework** : Tailwind CSS 3.4 (Compilation JIT via CLI).
*   **JavaScript** : Vanilla JS (ES6+) pour le player et les interactions dynamiques (pas de framework lourd type React/Vue pour le web public).
*   **Vidéo Web** : `hls.js` pour le support HLS universel.

## 3. Structure du Projet

L'application est structurée autour de **Blueprints** pour isoler les domaines fonctionnels :

```
/
├── app.py                 # Point d'entrée, config, init des extensions
├── models/                # Définitions des schémas de BDD
│   ├── user.py            # Gestion des utilisateurs et rôles
│   ├── screen.py          # Configuration des écrans
│   ├── booking.py         # Logique de réservation
│   └── ...
├── routes/                # Contrôleurs (Blueprints)
│   ├── auth_routes.py     # Login, Register, Logout
│   ├── admin_routes.py    # Back-office Superadmin
│   ├── org_routes.py      # Dashboard Organisation
│   ├── screen_routes.py   # Gestion technique des écrans
│   ├── booking_routes.py  # Tunnel de réservation public
│   ├── player_routes.py   # Logique d'affichage Player
│   ├── billing_routes.py  # Facturation et Paiements
│   └── mobile_api_routes.py # API JSON pour App Mobile
├── services/              # Logique métier complexe
│   ├── hls_converter.py   # Proxy et Conversion Vidéo (FFmpeg)
│   ├── playlist_service.py # Algorithme de sélection de contenu
│   └── billing_service.py # Génération de factures hebdo
├── static/                # Assets (CSS, JS, Uploads)
├── templates/             # Vues Jinja2
└── utils/                 # Helpers (Validateurs, Formatters)
```

## 4. Composants Clés

### 4.1 Le Player et le Streaming HLS
Le composant le plus complexe est le système de diffusion (`services/hls_converter.py`).
1.  **Proxying** : Le backend agit comme un proxy pour les flux `.m3u8` externes afin de contourner les restrictions CORS des fournisseurs IPTV.
2.  **Transcodage** : Si le flux source est en MPEG-TS pur (incompatible avec les navigateurs web standards), le backend lance un processus `ffmpeg` pour le convertir à la volée en segments HLS (`.ts` + `.m3u8`) stockés temporairement dans `static/hls/`.
3.  **Nettoyage** : Un mécanisme de rotation supprime les anciens segments pour éviter la saturation disque.

### 4.2 API Mobile (JWT)
L'API mobile (`/mobile/api/v1`) utilise une authentification distincte basée sur **JWT** :
*   **Access Token** : Durée de vie courte (24h).
*   **Refresh Token** : Durée de vie longue (30 jours), stocké en BDD (hashé) pour permettre la révocation.
*   **Middleware** : Un décorateur `@jwt_required` intercepte les requêtes, vérifie la signature et injecte l'utilisateur dans le contexte `g`.

### 4.3 Système de Facturation (Billing)
Le module de facturation est semi-automatisé :
*   **Trigger** : Cron job hebdomadaire (Dimanche 23h59).
*   **Logique** : Agrégation des `Booking` payés par `Organization`.
*   **Calcul** : `Total Revenu - (Total Revenu * % Commission) = Net à Reverser`.
*   **État** : Les factures passent par les états `PENDING` -> `PAID` (Preuve uploadée) -> `VALIDATED` (Confirmé par Admin).

## 5. Sécurité

### 5.1 Protection CSRF
Une implémentation manuelle de CSRF est présente dans `app.py` (`validate_csrf_token`). Elle vérifie la présence d'un token synchronisé en session pour toutes les méthodes `POST`, `PUT`, `DELETE`, sauf pour les endpoints API exclus explicitement (webhooks, API mobile).

### 5.2 Rate Limiting
`Flask-Limiter` protège les routes sensibles :
*   Login : 5 essais / minute.
*   API Mobile : Limites strictes par IP/Token.
*   Player Heartbeat : 120 requêtes / minute (pour éviter le DDoS interne).

### 5.3 Validation des Entrées
Tous les inputs utilisateurs (formulaires et JSON) sont validés via `services/input_validator.py` :
*   Sanitization des chaînes (suppression HTML/Script).
*   Validation stricte des types (int, float, uuid).
*   Vérification des fichiers uploadés (Magic numbers pour Images/Vidéos via `Pillow`/`ffprobe`).

## 6. Déploiement

L'application est conçue pour être déployée via Docker ou sur un VPS standard :
*   **Serveur Web** : Nginx (Reverse Proxy, SSL, Static Files).
*   **App Server** : Gunicorn avec Gevent (pour supporter les I/O longs du streaming).
*   **Process Manager** : Systemd ou Docker Compose.
*   **SSL** : Obligatoire pour la sécurité des cookies (Secure Flag).

## 7. Performances

*   **Caching** : Les playlists du player sont mises en cache (TTL court) pour réduire la charge BDD.
*   **Lazy Loading** : SQLAlchemy est configuré pour charger les relations à la demande, sauf pour les routes critiques (Dashboard) où `joinedload` est utilisé pour éviter le problème N+1.
*   **Async** : L'envoi de notifications (WhatsApp/Email) et le traitement vidéo sont gérés de manière asynchrone par rapport au thread de requête principal.
