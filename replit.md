# AdScreen - SaaS Location Écrans Publicitaires

## Overview
AdScreen est une plateforme SaaS permettant aux établissements (bars, restaurants, centres commerciaux) de monétiser leurs écrans publicitaires via un système de location self-service. Les annonceurs accèdent via lien/QR code, choisissent des créneaux, uploadent du contenu adapté, payent et reçoivent des rapports.

## Architecture

### Backend
- **Framework**: Flask (Python 3.11)
- **Base de données**: PostgreSQL avec SQLAlchemy ORM
- **Authentification**: Flask-Login avec sessions
- **Validation médias**: Pillow (images), ffmpeg (vidéos)
- **QR Codes**: qrcode[pil]

### Frontend
- **Templates**: Jinja2
- **CSS**: Tailwind CSS (CDN)
- **Icons**: Font Awesome
- **Fonts**: Inter, JetBrains Mono (Google Fonts)
- **JavaScript**: Vanilla JS

## Structure du projet

```
├── app.py              # Configuration Flask et extensions
├── models.py           # Modèles SQLAlchemy
├── main.py             # Point d'entrée
├── create_superadmin.py # Script création admin
├── routes/
│   ├── auth_routes.py      # Login/Register/Logout
│   ├── admin_routes.py     # Dashboard superadmin
│   ├── org_routes.py       # Dashboard établissement
│   ├── screen_routes.py    # Gestion écrans
│   ├── booking_routes.py   # Réservations publiques
│   ├── player_routes.py    # API et page player
│   └── api_routes.py       # API REST
├── services/
│   ├── playlist_service.py # Gestion playlist
│   ├── pricing_service.py  # Calcul prix
│   └── qr_service.py       # Génération QR
├── utils/
│   ├── image_utils.py      # Validation images
│   └── video_utils.py      # Validation vidéos
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── auth/               # Login, Register
│   ├── admin/              # Dashboard superadmin
│   ├── org/                # Dashboard établissement
│   ├── booking/            # Interface client
│   └── player/             # Mode player écran
└── static/
    └── uploads/            # Contenus uploadés
```

## Rôles utilisateurs

1. **Superadmin**: Gère les établissements, commissions, stats globales
2. **Établissement (org)**: Configure écrans, valide contenus, stats
3. **Client/Annonceur**: Réserve via QR code, uploade contenu
4. **Écran (player)**: Page web fullscreen pour diffusion

## Fonctionnalités principales

- CRUD établissements et écrans
- Configuration slots (durées/prix) et périodes journée (multiplicateurs)
- Génération QR codes par écran
- Upload contenu avec validation stricte (ratio, résolution, durée)
- File de validation avec aperçu
- Player web fullscreen avec loop automatique
- Heartbeat et statuts temps réel
- Statistiques et tracking passages

## Comptes de test

- **Superadmin**: admin@adscreen.com / admin123
- Pour créer un superadmin: `python create_superadmin.py email password`

## Démarrage

L'application démarre automatiquement sur le port 5000 via Gunicorn.

## Base de données

PostgreSQL est configuré via la variable d'environnement DATABASE_URL.
Les tables sont créées automatiquement au démarrage.

## Priorités playlist

1. Contenus payants (priorité 100)
2. Contenus internes établissement (priorité 80)
3. Fillers/démos (priorité 20)
