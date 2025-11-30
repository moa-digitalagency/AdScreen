# Architecture Technique

## Vue d'ensemble

AdScreen est une application web Flask suivant une architecture MVC (Model-View-Controller) avec une séparation claire des responsabilités.

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

### Frontend

| Composant | Technologie |
|-----------|-------------|
| Templates | Jinja2 |
| CSS | Tailwind CSS (CDN) |
| Icons | Font Awesome |
| Fonts | Inter, JetBrains Mono |
| JavaScript | Vanilla JS |

### Utilitaires

| Composant | Technologie | Usage |
|-----------|-------------|-------|
| Pillow | PIL | Validation images |
| ffmpeg | Système | Validation vidéos |
| qrcode | Python | Génération QR codes |

## Structure des fichiers

```
adscreen/
├── app.py                 # Configuration Flask
├── main.py                # Point d'entrée
├── init_db.py             # Script init BDD
├── init_db_demo.py        # Script données démo
│
├── models/                # Modèles SQLAlchemy
│   ├── __init__.py        # Exports
│   ├── user.py            # Utilisateurs
│   ├── organization.py    # Établissements
│   ├── screen.py          # Écrans
│   ├── time_slot.py       # Créneaux
│   ├── time_period.py     # Périodes
│   ├── content.py         # Contenus clients
│   ├── booking.py         # Réservations
│   ├── filler.py          # Contenus filler
│   ├── internal_content.py # Contenus internes
│   ├── stat_log.py        # Logs diffusion
│   └── heartbeat_log.py   # Logs connexion
│
├── routes/                # Blueprints Flask
│   ├── auth_routes.py     # Authentification
│   ├── admin_routes.py    # Superadmin
│   ├── org_routes.py      # Établissement
│   ├── screen_routes.py   # Config écrans
│   ├── booking_routes.py  # Réservations
│   ├── player_routes.py   # Player API
│   └── api_routes.py      # API REST
│
├── services/              # Logique métier
│   ├── playlist_service.py
│   ├── pricing_service.py
│   └── qr_service.py
│
├── utils/                 # Utilitaires
│   ├── image_utils.py
│   └── video_utils.py
│
├── templates/             # Templates Jinja2
│   ├── base.html
│   ├── admin/
│   ├── org/
│   ├── booking/
│   └── player/
│
└── static/
    └── uploads/           # Fichiers uploadés
```

## Modèle de données

### Diagramme entité-relation

```
┌──────────┐       ┌──────────────┐       ┌────────┐
│   User   │──────▶│ Organization │◀──────│ Screen │
└──────────┘ 1:N   └──────────────┘  1:N  └────────┘
                                              │
                   ┌──────────────────────────┼──────────────────────────┐
                   │              │           │           │              │
                   ▼              ▼           ▼           ▼              ▼
              ┌─────────┐   ┌──────────┐ ┌─────────┐ ┌────────┐   ┌──────────┐
              │TimeSlot │   │TimePeriod│ │ Content │ │ Filler │   │ Internal │
              └─────────┘   └──────────┘ └─────────┘ └────────┘   │ Content  │
                                              │                   └──────────┘
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
| Content → Booking | 1:1 | Un contenu a une réservation |

## Flux de données

### 1. Réservation client

```
Client                    Serveur                   Base de données
   │                         │                            │
   │  GET /book/<code>       │                            │
   │────────────────────────▶│                            │
   │                         │  SELECT screen             │
   │                         │───────────────────────────▶│
   │                         │◀───────────────────────────│
   │   Page écran            │                            │
   │◀────────────────────────│                            │
   │                         │                            │
   │  POST /book/<code>      │                            │
   │  (form + fichier)       │                            │
   │────────────────────────▶│                            │
   │                         │  Validation fichier        │
   │                         │  INSERT content            │
   │                         │  INSERT booking            │
   │                         │───────────────────────────▶│
   │   Confirmation          │◀───────────────────────────│
   │◀────────────────────────│                            │
```

### 2. Player écran

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
   │                         │───────────────────────────▶│
   │   JSON playlist         │◀───────────────────────────│
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

## Sécurité

### Authentification

- **Sessions Flask** avec cookie sécurisé
- **Flask-Login** pour la gestion des utilisateurs connectés
- **Mots de passe** hashés avec Werkzeug (PBKDF2-SHA256)

### Autorisation

- **Décorateurs** `@login_required` sur les routes protégées
- **Vérification de rôle** dans les routes admin/org
- **Isolation des données** par organisation

### Upload de fichiers

- **Validation MIME type**
- **Limite de taille** configurable
- **Nom de fichier** sécurisé (uuid)
- **Stockage** hors de la racine web

## Performance

### Optimisations actuelles

- **Pool de connexions** PostgreSQL avec recyclage
- **Pre-ping** pour détecter les connexions mortes
- **Indexes** sur les colonnes fréquemment requêtées

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

### Métriques à surveiller

- Temps de réponse des routes
- Nombre de connexions actives
- Utilisation mémoire/CPU
- Uptime des écrans
