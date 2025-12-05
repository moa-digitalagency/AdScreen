# Shabaka AdScreen

Plateforme SaaS de gestion d'écrans publicitaires numériques (DOOH - Digital Out-Of-Home).

## Vue d'ensemble

Shabaka AdScreen permet aux établissements (cafés, restaurants, centres commerciaux) de monétiser leurs écrans en offrant des créneaux publicitaires à des annonceurs locaux. La plateforme prend en charge plusieurs devises (EUR, MAD, TND, XOF) et propose un système complet de réservation, validation et diffusion de contenus.

## Caractéristiques principales

### Gestion Multi-devises
- **EUR** (Euro) - France, Belgique, Allemagne, etc.
- **MAD** (Dirham Marocain) - Maroc
- **TND** (Dinar Tunisien) - Tunisie
- **XOF** (Franc CFA) - Sénégal, Côte d'Ivoire, Mali, etc.

### Types d'écrans
- Écrans paysage (16:9) : 1920x1080, 3840x2160
- Écrans portrait (9:16) : 1080x1920
- Résolutions personnalisées

### Créneaux horaires
- Images : 10s, 15s, 30s
- Vidéos : 15s, 30s, 60s
- Tarification dynamique par période (matin, midi, après-midi, soir, nuit)

### Système de diffusion (Broadcasts)
- Ciblage multi-niveaux : pays, ville, établissement, écran
- Types d'overlay : bandeau texte, image fixe, coin logo
- Modes : immédiat ou programmé avec récurrence
- Priorités configurables (20-200)
- Fuseaux horaires internationaux (25+ zones)

### Mode OnlineTV (IPTV)
- Support M3U/M3U8 et flux HLS via HLS.js
- Fallback MPEG-TS avec mpegts.js
- Bascule instantanée playlist/TV
- Overlays actifs pendant la diffusion TV
- Contrôle audio complet (mute/unmute)

### Système de Player
- Authentification par code unique et mot de passe
- Playlist dynamique avec rafraîchissement automatique
- Overlay système : bandeaux défilants, images, logos en coin
- Heartbeat automatique pour monitoring
- Mode plein écran (F11)
- Contrôle audio avec raccourci clavier (M)
- Support vidéo et streaming IPTV avec son

### Établissements gratuits
- Mode gratuit disponible pour établissements partenaires
- Accès limité : contenus internes et overlays uniquement
- Pas de réservations clients ni de facturation

### Validation des contenus
- Vérification automatique des résolutions
- Support formats : JPEG, PNG, GIF, WebP, MP4, WebM, MOV
- Validation durée des vidéos
- Workflow d'approbation/rejet

### Facturation automatisée
- Cycle hebdomadaire (lundi à dimanche)
- Commission configurable par établissement
- Workflow de preuve de paiement
- Export PDF des factures

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | Structure technique et diagrammes |
| [Fonctionnalités](features.md) | Liste détaillée des fonctionnalités |
| [Algorithme](Algo.md) | Logique métier détaillée |
| [Comptes démo](demo_accounts.md) | Données de test et scénarios |
| [Déploiement](deployment.md) | Guide d'installation et configuration |
| [Présentation commerciale](COMMERCIAL_PRESENTATION.md) | Pitch et argumentaire commercial |

## Structure du projet

```
shabaka-adscreen/
├── main.py                 # Point d'entrée
├── app.py                  # Configuration Flask
├── init_db.py              # Initialisation base de données
├── init_db_demo.py         # Données de démonstration
├── models/                 # Modèles SQLAlchemy
│   ├── user.py             # Utilisateurs (super-admin, admin, managers)
│   ├── organization.py     # Établissements
│   ├── screen.py           # Écrans
│   ├── reservation.py      # Réservations clients
│   ├── broadcast.py        # Diffusions centralisées
│   ├── overlay.py          # Overlays locaux
│   ├── online_tv.py        # Chaînes TV et streaming
│   ├── invoice.py          # Factures
│   └── ...
├── routes/                 # Routes Flask
│   ├── admin/              # Interface super-admin
│   ├── org/                # Interface établissement
│   ├── client/             # Interface annonceur
│   ├── player/             # API et interface player
│   └── billing/            # Facturation
├── services/               # Services métier
│   ├── playlist_service.py # Génération playlists
│   └── broadcast_service.py # Logique broadcasts
├── templates/              # Templates Jinja2
│   ├── admin/              # Templates admin
│   ├── org/                # Templates établissement
│   ├── client/             # Templates client
│   └── player/             # Templates player
├── static/                 # Fichiers statiques
│   ├── css/                # Styles
│   ├── js/                 # JavaScript
│   ├── uploads/            # Fichiers uploadés
│   │   ├── contents/       # Contenus publicitaires
│   │   ├── fillers/        # Contenus de remplissage
│   │   ├── internal/       # Contenus internes
│   │   └── broadcasts/     # Contenus diffusions
│   └── favicon*.svg        # Favicons par interface
└── docs/                   # Documentation
```

## Technologies

| Composant | Technologie |
|-----------|-------------|
| Backend | Python 3.11, Flask 3.x |
| Base de données | PostgreSQL 16 (Neon) |
| ORM | SQLAlchemy 2.x |
| Authentification | Flask-Login |
| Frontend | Tailwind CSS, Font Awesome |
| Player vidéo | HLS.js, mpegts.js |
| QR Codes | qrcode, Pillow |
| PDF | ReportLab |
| Serveur WSGI | Gunicorn |

## Accès rapides

| Interface | URL | Utilisateur |
|-----------|-----|-------------|
| Super-admin | `/admin` | Administrateur plateforme |
| Établissement | `/org` | Manager d'établissement |
| Client | `/book/<code>` | Annonceur (via QR code) |
| Player | `/player` | Écran de diffusion |

## Démarrage rapide

```bash
# Installation des dépendances
pip install -r requirements.txt

# Initialisation de la base de données
python init_db.py

# (Optionnel) Création des données de démo
python init_db_demo.py

# Démarrage du serveur
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

## Comptes de démonstration

Pour tester la plateforme, utilisez les comptes créés par `init_db_demo.py` :

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Super-admin | admin@shabaka-adscreen.com | admin123 |
| Manager | manager@restaurant-paris.fr | demo123 |
| Player | Code écran + mot de passe | screen123 |

Voir [demo_accounts.md](demo_accounts.md) pour la liste complète.

## Licence

Propriétaire - Shabaka AdScreen
