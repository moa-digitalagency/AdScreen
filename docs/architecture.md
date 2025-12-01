# Architecture Technique - Shabaka AdScreen

## Vue d'ensemble

Shabaka AdScreen est une application web Flask suivant une architecture MVC (Model-View-Controller) avec une séparation claire des responsabilités. La plateforme supporte la gestion multi-établissements, les opérations multi-devises (EUR, MAD, XOF, TND), et un système de réservation QR code.

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Templates  │  │   Static    │  │   Player    │              │
│  │   Jinja2    │  │  CSS/JS/    │  │  Fullscreen │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ROUTES                                   │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐   │
│  │ Auth  │ │ Admin │ │  Org  │ │Screen │ │Booking│ │Player │   │
│  └───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        SERVICES                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Playlist   │  │   Pricing    │  │     QR       │           │
│  │   Service    │  │   Service    │  │   Service    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Receipt    │  │   Filler     │  │   Currency   │           │
│  │  Generator   │  │  Generator   │  │   Service    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MODELS                                   │
│  ┌──────┐ ┌────────────┐ ┌────────┐ ┌─────────┐ ┌─────────┐    │
│  │ User │ │Organization│ │ Screen │ │TimeSlot │ │TimePeriod│   │
│  └──────┘ └────────────┘ └────────┘ └─────────┘ └─────────┘    │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ ┌─────────────────────────┐ │
│  │ Content │ │ Booking │ │ Filler │ │ InternalContent/StatLog │ │
│  └─────────┘ └─────────┘ └────────┘ └─────────────────────────┘ │
│  ┌───────────────┐ ┌─────────────┐ ┌──────────────────────────┐ │
│  │ScreenOverlay  │ │ SiteSetting │ │ RegistrationRequest      │ │
│  └───────────────┘ └─────────────┘ └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATABASE                                   │
│                      PostgreSQL                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Stack technique

### Backend

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Framework | Flask | 3.x |
| ORM | SQLAlchemy | 2.x |
| Base de données | PostgreSQL | 14+ |
| Authentification | Flask-Login | 0.6.x |
| Serveur WSGI | Gunicorn | 23.x |
| Génération images | Pillow | 10.x |
| Génération PDF | ReportLab | 4.x |

### Frontend

| Composant | Technologie |
|-----------|-------------|
| Templates | Jinja2 |
| CSS | Tailwind CSS (CDN) |
| Icons | Font Awesome 6 |
| Fonts | Inter, JetBrains Mono |
| JavaScript | Vanilla JS |

### Utilitaires

| Composant | Technologie | Usage |
|-----------|-------------|-------|
| Pillow | PIL | Validation images, génération reçus |
| ReportLab | PDF | Génération reçus PDF |
| ffmpeg | Système | Validation vidéos |
| qrcode | Python | Génération QR codes |

## Structure des fichiers

```
shabaka-adscreen/
├── app.py                    # Configuration Flask
├── main.py                   # Point d'entrée
├── init_db.py                # Script init BDD
├── init_db_demo.py           # Script données démo
│
├── models/                   # Modèles SQLAlchemy
│   ├── __init__.py           # Exports
│   ├── user.py               # Utilisateurs
│   ├── organization.py       # Établissements (multi-devise)
│   ├── screen.py             # Écrans
│   ├── time_slot.py          # Créneaux
│   ├── time_period.py        # Périodes
│   ├── content.py            # Contenus clients
│   ├── booking.py            # Réservations
│   ├── filler.py             # Contenus filler
│   ├── internal_content.py   # Contenus internes
│   ├── stat_log.py           # Logs diffusion
│   ├── heartbeat_log.py      # Logs connexion
│   ├── screen_overlay.py     # Bandeaux/overlays
│   ├── site_setting.py       # Configuration globale
│   └── registration_request.py # Demandes inscription
│
├── routes/                   # Blueprints Flask
│   ├── auth_routes.py        # Authentification
│   ├── admin_routes.py       # Superadmin
│   ├── org_routes.py         # Établissement
│   ├── screen_routes.py      # Config écrans
│   ├── booking_routes.py     # Réservations
│   ├── player_routes.py      # Player API
│   └── api_routes.py         # API REST
│
├── services/                 # Logique métier
│   ├── playlist_service.py   # Génération playlists
│   ├── pricing_service.py    # Calcul prix
│   ├── qr_service.py         # Génération QR codes
│   ├── receipt_generator.py  # Reçus thermiques (image/PDF)
│   ├── filler_generator.py   # Génération fillers par défaut
│   └── currency_service.py   # Gestion multi-devises
│
├── utils/                    # Utilitaires
│   ├── image_utils.py        # Traitement images
│   ├── video_utils.py        # Traitement vidéos
│   ├── world_data.py         # Données pays/villes (208 pays, 4600+ villes)
│   └── currencies.py         # Gestion devises et taux de change
│
├── templates/                # Templates Jinja2
│   ├── base.html
│   ├── admin/
│   ├── org/
│   ├── booking/
│   └── player/
│
├── static/
│   └── uploads/              # Fichiers uploadés
│       ├── contents/         # Contenus clients
│       ├── fillers/          # Contenus filler
│       └── internal/         # Contenus internes
│
└── docs/                     # Documentation
    ├── architecture.md
    ├── demo_accounts.md
    ├── deployment.md
    └── features.md
```

## Modèle de données

### Diagramme entité-relation

```
┌──────────┐       ┌──────────────┐       ┌────────┐
│   User   │──────▶│ Organization │◀──────│ Screen │
└──────────┘ 1:N   └──────────────┘  1:N  └────────┘
     │               (multi-devise)           │
     │                                        │
     │    ┌───────────────────────────────────┼───────────────────────┐
     │    │              │           │        │          │            │
     ▼    ▼              ▼           ▼        ▼          ▼            ▼
┌─────────────┐   ┌──────────┐ ┌─────────┐ ┌────────┐ ┌────────┐ ┌─────────┐
│Registration │   │TimeSlot  │ │TimePeriod│ │Content │ │ Filler │ │ Overlay │
│  Request    │   └──────────┘ └──────────┘ └────────┘ └────────┘ └─────────┘
└─────────────┘                                │
                                               ▼
                                          ┌─────────┐
                                          │ Booking │
                                          └─────────┘
```

### Relations principales

| Relation | Type | Description |
|----------|------|-------------|
| User → Organization | N:1 | Un utilisateur appartient à une organisation |
| Organization → Screen | 1:N | Une organisation a plusieurs écrans |
| Screen → TimeSlot | 1:N | Un écran a plusieurs créneaux |
| Screen → TimePeriod | 1:N | Un écran a plusieurs périodes |
| Screen → Content | 1:N | Un écran a plusieurs contenus |
| Screen → ScreenOverlay | 1:N | Un écran peut avoir plusieurs overlays |
| Content → Booking | 1:1 | Un contenu a une réservation |
| Organization → currency | 1:1 | Chaque organisation a sa devise (EUR, MAD, XOF, TND) |

### Devises supportées

| Code | Symbole | Pays |
|------|---------|------|
| EUR | € | France, Europe |
| MAD | DH | Maroc |
| XOF | FCFA | Sénégal, Afrique de l'Ouest |
| TND | DT | Tunisie |

### Données géographiques (world_data.py)

Le module `utils/world_data.py` fournit une couverture mondiale exhaustive :

| Élément | Quantité | Description |
|---------|----------|-------------|
| Pays | 208 | Tous les pays avec code ISO, drapeau, continent, devise |
| Villes | 4 600+ | 1-30 villes par pays (moyenne 22) |
| Continents | 6 | Afrique, Amérique, Asie, Europe, Océanie |
| Territoires | 15+ | DOM-TOM, régions autonomes |

**API Endpoint** : `GET /api/cities/<country_code>` retourne la liste des villes pour un pays donné.

## Flux de données

### 1. Réservation client

```
Client                    Serveur                   Base de données
   │                         │                            │
   │  GET /book/<code>       │                            │
   │────────────────────────▶│                            │
   │                         │  SELECT screen, org        │
   │                         │───────────────────────────▶│
   │                         │◀───────────────────────────│
   │   Page écran (devise)   │                            │
   │◀────────────────────────│                            │
   │                         │                            │
   │  POST /book/<code>      │                            │
   │  (form + fichier)       │                            │
   │────────────────────────▶│                            │
   │                         │  Validation fichier        │
   │                         │  INSERT content            │
   │                         │  INSERT booking            │
   │                         │───────────────────────────▶│
   │   Confirmation + Reçu   │◀───────────────────────────│
   │◀────────────────────────│                            │
```

### 2. Player écran avec overlays

```
Player                    Serveur                   Base de données
   │                         │                            │
   │  POST /player/login     │                            │
   │────────────────────────▶│                            │
   │                         │  Vérif credentials        │
   │                         │───────────────────────────▶│
   │   Session               │◀───────────────────────────│
   │◀────────────────────────│                            │
   │                         │                            │
   │  GET /api/playlist      │                            │
   │────────────────────────▶│                            │
   │                         │  Génération playlist       │
   │                         │  + overlays actifs         │
   │                         │───────────────────────────▶│
   │   JSON playlist+overlay │◀───────────────────────────│
   │◀────────────────────────│                            │
   │                         │                            │
   │  POST /api/heartbeat    │                            │
   │  (toutes les 30s)       │                            │
   │────────────────────────▶│                            │
   │                         │  UPDATE screen.status      │
   │                         │───────────────────────────▶│
   │   OK                    │◀───────────────────────────│
   │◀────────────────────────│                            │
```

### 3. Génération reçu thermal

```
Client                    Serveur                   Services
   │                         │                         │
   │  GET /receipt/<id>      │                         │
   │────────────────────────▶│                         │
   │                         │  receipt_generator      │
   │                         │─────────────────────────▶│
   │                         │  Génère image PIL        │
   │                         │  (style ticket thermal)  │
   │                         │  En-tête: Org + Écran    │
   │   Image PNG (stream)    │◀────────────────────────│
   │◀────────────────────────│                         │
```

## Sécurité

### Authentification

- **Sessions Flask** avec cookie sécurisé
- **Flask-Login** pour la gestion des utilisateurs connectés
- **Mots de passe** hashés avec Werkzeug (PBKDF2-SHA256)
- **JWT** pour authentification player (optionnel)

### Autorisation

- **Décorateurs** `@login_required` sur les routes protégées
- **Vérification de rôle** dans les routes admin/org
- **Isolation des données** par organisation
- **Validation CSRF** sur les formulaires

### Upload de fichiers

- **Validation MIME type**
- **Limite de taille** configurable par écran
- **Nom de fichier** sécurisé (uuid)
- **Stockage** dans `static/uploads/` avec organisation

## Performance

### Optimisations actuelles

- **Pool de connexions** PostgreSQL avec recyclage (300s)
- **Pre-ping** pour détecter les connexions mortes
- **Indexes** sur les colonnes fréquemment requêtées
- **Streaming** des images reçu (pas de stockage temporaire)
- **Cache-Control** headers anti-cache pour les reçus

### Améliorations futures

- Cache Redis pour les playlists
- CDN pour les fichiers statiques
- Pagination sur les listes longues
- Compression des réponses

## Monitoring

### Logs

- Logs applicatifs sur stdout/stderr
- Niveau DEBUG en développement
- Format structuré en production
- Heartbeat logs pour uptime écrans

### Métriques à surveiller

- Temps de réponse des routes
- Nombre de connexions actives
- Utilisation mémoire/CPU
- Uptime des écrans
- Revenus par devise
