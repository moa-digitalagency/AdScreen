# AdScreen - SaaS Location Écrans Publicitaires 📺

## 🎯 Overview
AdScreen est une plateforme SaaS permettant aux établissements (bars, restaurants, centres commerciaux) de monétiser leurs écrans publicitaires via un système de location self-service. Les annonceurs accèdent via lien/QR code, choisissent des créneaux, uploadent du contenu adapté, payent et reçoivent des rapports.

## 🏗️ Architecture

### Backend
- **Framework**: Flask (Python 3.11) 🐍
- **Base de données**: PostgreSQL avec SQLAlchemy ORM 🗄️
- **Authentification**: Flask-Login avec sessions 🔐
- **Validation médias**: Pillow (images), ffmpeg (vidéos) 🖼️
- **QR Codes**: qrcode[pil] 📱

### Frontend
- **Templates**: Jinja2 📝
- **CSS**: Tailwind CSS (CDN) 🎨
- **Icons**: Font Awesome ⭐
- **Fonts**: Inter, JetBrains Mono (Google Fonts) ✏️
- **JavaScript**: Vanilla JS ⚡

## 📁 Structure du projet

```
├── app.py              # Configuration Flask et extensions
├── main.py             # Point d'entrée
├── create_superadmin.py # Script création admin
├── init_db.py          # Initialisation base de données
├── init_db_demo.py     # Données de démonstration
├── models/             # Modèles SQLAlchemy
│   ├── __init__.py         # Export tous les modèles
│   ├── user.py             # 👤 Utilisateurs (superadmin, org)
│   ├── organization.py     # 🏢 Établissements
│   ├── screen.py           # 📺 Écrans publicitaires
│   ├── screen_overlay.py   # 🎭 Overlays (bandeaux, images)
│   ├── time_slot.py        # ⏰ Créneaux horaires
│   ├── time_period.py      # 🌅 Périodes de la journée
│   ├── content.py          # 📦 Contenus uploadés
│   ├── booking.py          # 📋 Réservations
│   ├── filler.py           # 🎬 Contenus de remplissage
│   ├── internal_content.py # 📢 Contenus internes
│   ├── stat_log.py         # 📊 Statistiques de lecture
│   ├── heartbeat_log.py    # 💓 Logs de connexion écrans
│   ├── site_setting.py     # ⚙️ Paramètres du site
│   └── registration_request.py # 📝 Demandes d'inscription
├── routes/
│   ├── auth_routes.py      # 🔑 Login/Register/Logout
│   ├── admin_routes.py     # 👑 Dashboard superadmin
│   ├── org_routes.py       # 🏪 Dashboard établissement
│   ├── screen_routes.py    # 📺 Gestion écrans
│   ├── booking_routes.py   # 🛒 Réservations publiques
│   ├── player_routes.py    # 🎮 API et page player
│   └── api_routes.py       # 🔌 API REST
├── services/
│   ├── playlist_service.py # 📻 Gestion playlist
│   ├── pricing_service.py  # 💰 Calcul prix
│   └── qr_service.py       # 📱 Génération QR
├── utils/
│   ├── image_utils.py      # 🖼️ Validation images
│   └── video_utils.py      # 🎥 Validation vidéos
├── templates/              # 📄 Templates Jinja2
└── static/                 # 📦 Fichiers statiques
    └── uploads/            # 📤 Contenus uploadés
```

## 👥 Rôles utilisateurs

1. **👑 Superadmin**: Gère les établissements, commissions, stats globales, demandes d'inscription
2. **🏪 Établissement (org)**: Configure écrans, valide contenus, ajoute overlays, visualise en direct
3. **📱 Client/Annonceur**: Réserve via QR code, uploade contenu
4. **📺 Écran (player)**: Page web fullscreen pour diffusion avec overlays

## ✨ Fonctionnalités principales

### 🏢 Gestion des établissements
- ✅ CRUD établissements et écrans
- ✅ Configuration slots (durées/prix) et périodes journée (multiplicateurs)
- ✅ Génération QR codes par écran
- ✅ Commissions personnalisables par établissement

### 📝 Système d'inscription
- ✅ Demandes d'inscription via formulaire
- ✅ Notification WhatsApp à l'admin (numéro configurable)
- ✅ Validation/rejet des demandes par l'admin
- ✅ Création de compte avec commission personnalisée

### 📺 Gestion des écrans
- ✅ Nommage personnalisé des écrans
- ✅ Aperçu en direct de ce qui s'affiche
- ✅ **Overlays superposés** (bandeaux défilants ou images fixes)
- ✅ Position des overlays: header, body ou footer
- ✅ Configuration couleurs, taille de police, vitesse de défilement

### 🎬 Gestion du contenu
- ✅ Upload contenu avec validation stricte (ratio, résolution, durée)
- ✅ File de validation avec aperçu
- ✅ Contenus internes établissement
- ✅ Fillers/démos

### 📺 Player écran
- ✅ Player web fullscreen avec loop automatique
- ✅ Affichage des overlays en temps réel
- ✅ Heartbeat et statuts temps réel
- ✅ Statistiques et tracking passages

### ⚙️ Administration
- ✅ Paramètres du site (SEO, commissions)
- ✅ Numéro WhatsApp admin configurable
- ✅ Mode maintenance
- ✅ Statistiques globales

## 🔐 Comptes de test

- **👑 Superadmin**: admin@adscreen.com / admin123
- Pour créer un superadmin: `python create_superadmin.py email password`

## 🚀 Démarrage

L'application démarre automatiquement sur le port 5000 via Gunicorn.

```bash
# Initialiser la base de données
python init_db.py

# Créer les données de démonstration
python init_db_demo.py
```

## 🗄️ Base de données

PostgreSQL est configuré via la variable d'environnement DATABASE_URL.
Les tables sont créées automatiquement au démarrage.

## 📻 Priorités playlist

1. 💰 Contenus payants (priorité 100)
2. 📢 Contenus internes établissement (priorité 80)
3. 🎬 Fillers/démos (priorité 20)

## 🎭 Système d'overlays

Les overlays permettent aux établissements d'afficher des messages superposés sur leurs écrans:

- **Type bandeau**: Texte défilant (ticker)
- **Type image**: Image fixe
- **Positions**: Header (haut), Body (centre), Footer (bas)
- **Personnalisation**: Couleurs, taille de police, vitesse de défilement
