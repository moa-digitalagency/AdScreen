# Shabaka AdScreen - SaaS Location Écrans Publicitaires 📺

## 🎯 Overview
Shabaka AdScreen est une plateforme SaaS permettant aux établissements (bars, restaurants, centres commerciaux) de monétiser leurs écrans publicitaires via un système de location self-service. Les annonceurs accèdent via lien/QR code, choisissent des créneaux, uploadent du contenu adapté, payent et reçoivent des rapports.

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
- ✅ **Actions sur les publicités**: suspendre, activer, supprimer
- ✅ **Aperçu selon résolution écran** pour tous types de contenus
- ✅ **Vue playlist admin** avec miniature écran en temps réel

### 📋 Système de réservation
- ✅ **Numéro de réservation unique** (format RES-XXXXXXXX)
- ✅ **Reçu complet** avec QR code, détails booking, et impression
- ✅ Adaptation automatique du contenu (pas de restriction résolution stricte)
- ✅ Suivi de statut de réservation

### 📺 Player écran
- ✅ Player web fullscreen avec loop automatique
- ✅ Affichage des overlays en temps réel
- ✅ Heartbeat et statuts temps réel
- ✅ Statistiques et tracking passages
- ✅ **Timeout contrôles de 10 secondes** (curseur et contrôles visibles)
- ✅ Rafraîchissement automatique de la playlist toutes les 30s

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

### Bandeau défilant (Ticker)
- **Positions disponibles**: Header (haut), Body (centre), Footer (bas) uniquement
- **Aperçu temps réel**: Visualisation du défilement pendant la saisie
- **Vitesse de défilement**: Contrôle via slider (20-150)
- **Personnalisation**: Couleurs fond/texte, taille police (16-72px)
- **Durée d'affichage**: Configurable en secondes

### Image overlay
- **Toutes les positions**: Header, Body, Footer + coins (top-left, top-right, bottom-left, bottom-right) + position personnalisée
- **Aperçu en temps réel**: Visualisation du positionnement et de la taille
- **Taille ajustable**: Pourcentage de la largeur de l'écran (5-50%)
- **Position personnalisée**: Coordonnées X/Y en pourcentage
- **Opacité**: Contrôle de la transparence (10-100%)
- **Dimensions originales**: Affichage des dimensions de l'image uploadée

### Paramètres communs
- **Durée d'affichage**: Temps en secondes
- **Limite de passages**: Nombre maximum par période
- **Période de diffusion**: Date/heure de début et de fin
- **Fréquence**: Heure, jour, semaine, mois, ou périodes (matin, midi, après-midi, soir, nuit)

## 🌟 Écrans en vedette

- Les super-admins peuvent marquer des écrans comme "en vedette"
- Les écrans en vedette apparaissent sur la page d'accueil
- Bouton de mise en vedette dans l'administration des écrans

## 📱 QR Codes personnalisés

Deux types de QR codes disponibles pour chaque écran:
- **QR Code simple**: Code basique noir/blanc
- **QR Code complet**: Inclut nom de l'établissement, nom de l'écran, résolution, et plateforme

## ⚙️ Paramètres du site avancés

### SEO
- Titre et description du site
- Mots-clés meta
- Image OG et favicon personnalisables
- Google Analytics ID

### Réseaux sociaux
- Facebook, Instagram, Twitter, LinkedIn, YouTube
- WhatsApp pour contact direct

### Code personnalisé
- Injection de code dans le `<head>` (scripts, pixels tracking, etc.)

### Contact
- Téléphone, adresse
- Numéro WhatsApp admin

## 💱 Multi-Currency Support

The platform supports multiple currencies based on organization settings:

### Supported Currencies
- **EUR** (€) - France
- **MAD** (DH) - Morocco
- **XOF** (FCFA) - Senegal, West Africa
- **TND** (DT) - Tunisia

### Price Calculation
- **Base formula**: `(duration_seconds / 60) × price_per_minute`
- **Period multipliers**: Different rates for morning, lunch, afternoon, evening, night
- **Slot examples**: 10s → 0.33×, 15s → 0.50×, 30s → 1.00× (based on price_per_minute)

### Video Playback Algorithm
- **Images**: Displayed for the full slot duration
- **Videos**: Play in full; if shorter than slot duration, last frame holds until time is reached
- **Example**: 13s video in 15s slot → video plays, then last frame remains for 2 additional seconds

## 🔧 Recent Fixes (December 2025)

### Currency Display Bug Fix
- Fixed hardcoded symbols in screen detail, form, availability, and slots templates
- Currency symbol now dynamically passed from routes using organization's currency setting
- JavaScript components updated to use dynamic currency symbol

### Availability Page Error Fix
- Fixed Jinja2 `min` filter usage error in screen_availability.html
- Changed `usage_percent|min(100)` to proper conditional capping logic

### Booking Status Page Enhancement
- Added detailed explanation of diffusion mode based on content type
- Shows video last-frame hold behavior clearly
- Added equitable distribution explanation

### QR Code Design Enhancement
- Modern gradient backgrounds with professional styling
- Improved typography with JetBrains Mono fonts
- Screen info display (name, resolution, organization)
- Shabaka AdScreen branding with platform URL

### Filler Design Modernization
- New modern gradient backgrounds for default fillers
- Professional styling with shadows and rounded corners
- Clean typography with Inter/JetBrains Mono fonts
- Logo placeholder and call-to-action sections

### Automatic Currency Conversion (Admin Dashboard)
- Implemented European Central Bank (ECB) API integration for real-time exchange rates
- 24-hour caching mechanism to minimize API calls
- Superadmin dashboard displays all revenues converted to EUR
- Conversion breakdown table showing original amounts, rates, and converted values
- Supports 80+ world currencies including EUR, MAD, TND, XOF

### Booking Time Fields
- Added start_time and end_time fields to booking model
- Updated booking form with time selection (alongside dates)
- Visual improvement with green/red colored date-time sections
- Enables more precise availability calculations and scheduling

### Design Enhancements (December 2025)

#### QR Code Complet - Nouveau Design Premium
- Design glassmorphism avec gradients modernes (violet/indigo/bleu)
- Cercles décoratifs flottants dans le header
- Effet de vague entre les sections
- Coins colorés sur le conteneur QR
- Section info avec résolution, orientation, formats acceptés
- Bouton CTA avec gradient vert
- Footer moderne avec barre d'accent gradient

#### Filler Generator - Nouveau Style Professionnel
- Fond sombre avec gradient et effet de vague
- Cercles décoratifs dans le header
- Barre d'accent gradient dans le footer
- Coins colorés sur le conteneur QR
- Système de badges responsive pour les infos écran
- Bouton CTA avec gradient vert
- Typographie premium avec ombres

#### Dashboard Admin - Conversion Devises Améliorée
- Bouton de rafraîchissement des taux avec indicateur de chargement
- Bannière gradient pour le statut de conversion
- Token CSRF pour la sécurité des formulaires
- Timeout automatique de 15s pour réinitialiser le bouton
- Messages flash pour succès/erreur

#### Formulaire de Réservation - Responsivité Mobile/Tablette
- Design adaptatif pour écrans de 320px à 1920px
- Media queries spécifiques pour très petits écrans (320px, 360px, 480px)
- Grille de disponibilités compacte et responsive
- Tailles de police et espacement adaptés
- Contrôles de nombre de passages optimisés pour mobile
- Section dates/heures avec icônes et couleurs (vert/rouge)
