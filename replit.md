# Shabaka AdScreen

## A propos du projet

Shabaka AdScreen est une plateforme SaaS qui permet aux etablissements (restaurants, bars, centres commerciaux, hotels) de monetiser leurs ecrans d'affichage. Les annonceurs locaux reservent des creneaux publicitaires directement via un QR code, sans intermediaire.

## Stack technique

- **Backend** : Flask 3.x avec Python 3.11
- **Base de donnees** : PostgreSQL avec SQLAlchemy 2.x
- **Frontend** : Templates Jinja2, Tailwind CSS 3.4
- **Authentification** : Flask-Login (sessions), PyJWT (API mobile)
- **Serveur** : Gunicorn avec gevent
- **Streaming** : HLS.js, mpegts.js (fallback)

## Architecture des fichiers

```
shabaka-adscreen/
├── app.py                  # Configuration Flask et initialisation
├── main.py                 # Point d'entree de l'application
├── init_db.py              # Script de creation/mise a jour du schema
├── init_db_demo.py         # Donnees de demonstration (808 lignes)
│
├── models/                 # Modeles SQLAlchemy
│   ├── __init__.py
│   ├── ad_content.py       # Contenu publicitaire (435 lignes)
│   ├── booking.py          # Reservations
│   ├── broadcast.py        # Diffusions (435 lignes)
│   ├── content.py          # Contenus
│   ├── filler.py           # Contenus de remplissage
│   ├── heartbeat_log.py    # Logs heartbeat player
│   ├── internal_content.py # Contenus internes
│   ├── invoice.py          # Factures
│   ├── organization.py     # Organisations/Etablissements
│   ├── registration_request.py # Demandes d'inscription
│   ├── screen.py           # Ecrans
│   ├── screen_overlay.py   # Overlays ecran
│   ├── site_setting.py     # Parametres du site
│   ├── stat_log.py         # Logs statistiques
│   ├── time_period.py      # Periodes horaires
│   ├── time_slot.py        # Creneaux horaires
│   └── user.py             # Utilisateurs
│
├── routes/                 # Blueprints Flask
│   ├── __init__.py
│   ├── admin_routes.py     # Console admin (1790 lignes)
│   ├── ad_content_routes.py # Gestion contenus pub (901 lignes)
│   ├── api_routes.py       # API generale
│   ├── auth_routes.py      # Authentification (324 lignes)
│   ├── billing_routes.py   # Facturation (466 lignes)
│   ├── booking_routes.py   # Reservations (456 lignes)
│   ├── mobile_api_routes.py # API mobile (570 lignes)
│   ├── org_routes.py       # Dashboard organisation (1610 lignes)
│   ├── player_routes.py    # Player ecran (637 lignes)
│   └── screen_routes.py    # Gestion ecrans
│
├── services/               # Logique metier
│   ├── __init__.py
│   ├── availability_service.py # Calcul disponibilites (251 lignes)
│   ├── currency_service.py     # Gestion devises (307 lignes)
│   ├── filler_generator.py     # Generation fillers (401 lignes)
│   ├── hls_converter.py        # Conversion HLS
│   ├── input_validator.py      # Validation entrees
│   ├── iptv_service.py         # Service IPTV
│   ├── jwt_service.py          # Gestion JWT (268 lignes)
│   ├── overlay_service.py      # Gestion overlays
│   ├── playlist_service.py     # Generation playlists (390 lignes)
│   ├── pricing_service.py      # Calcul prix
│   ├── qr_service.py           # Generation QR codes (270 lignes)
│   ├── rate_limiter.py         # Limitation requetes
│   └── receipt_generator.py    # Generation recus (515 lignes)
│
├── utils/                  # Utilitaires
│   ├── __init__.py
│   ├── countries.py        # Liste des pays
│   ├── currencies.py       # Devises (398 lignes)
│   ├── image_utils.py      # Manipulation images
│   ├── video_utils.py      # Manipulation videos
│   └── world_data.py       # Donnees mondiales (208 pays, 4600+ villes)
│
├── templates/              # Templates Jinja2
│   ├── admin/              # Interface admin
│   │   ├── ad_contents/    # Gestion contenus pub
│   │   ├── billing/        # Facturation
│   │   ├── broadcasts/     # Diffusions
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── organizations.html
│   │   ├── screens.html
│   │   ├── settings.html
│   │   ├── stats.html
│   │   └── users.html
│   ├── auth/               # Authentification
│   │   ├── login.html
│   │   └── register.html
│   ├── booking/            # Reservation annonceur
│   │   ├── screen.html
│   │   ├── status.html
│   │   ├── success.html
│   │   └── unavailable.html
│   ├── org/                # Dashboard organisation
│   │   ├── billing/        # Facturation org
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── screens.html
│   │   ├── settings.html
│   │   └── stats.html
│   ├── player/             # Player ecran
│   │   ├── display.html
│   │   └── login.html
│   ├── base.html           # Template de base
│   ├── catalog.html        # Catalogue ecrans
│   └── index.html          # Page d'accueil
│
├── static/                 # Fichiers statiques
│   ├── css/
│   │   ├── input.css       # Source Tailwind
│   │   ├── styles.css      # Styles compiles
│   │   ├── tailwind.css    # Tailwind compile
│   │   └── theme-template.css
│   ├── js/
│   │   ├── hls.min.js      # Librairie HLS.js
│   │   ├── main.js         # JS principal (306 lignes)
│   │   ├── mpegts.min.js   # Librairie MPEG-TS (externe)
│   │   └── player-sw.js    # Service Worker player
│   └── uploads/            # Contenus uploades
│       └── fillers/        # Images de remplissage (7 dossiers)
│
├── docs/                   # Documentation
│   ├── README.md           # Vue d'ensemble
│   ├── Algo.md             # Algorithmes metier
│   ├── API_MOBILE_DOCUMENTATION.md
│   ├── API_MOBILE_V1_SECURE.md
│   ├── architecture.md
│   ├── COMMERCIAL_PRESENTATION.md
│   ├── demo_accounts.md
│   ├── deployment.md
│   ├── features.md
│   ├── PLAYER_MOBILE_SDK.md
│   └── VPS_DEPLOYMENT.md
│
├── package.json            # Config Node.js (Tailwind)
├── tailwind.config.js      # Config Tailwind CSS
├── pyproject.toml          # Config Python
├── requirements.txt        # Dependances Python
└── README.md               # Documentation principale
```

## Interfaces

La plateforme expose 4 interfaces distinctes :

1. **Admin** (`/admin`) - Console operateur : gestion des etablissements, commissions, diffusions, facturation
2. **Organisation** (`/org`) - Tableau de bord etablissement : ecrans, contenus, overlays, statistiques
3. **Booking** (`/book/<code>`) - Interface annonceur : reservation via QR code, upload, paiement
4. **Player** (`/player`) - Diffusion sur ecran : playlist, overlays, mode OnlineTV

## Fonctionnalites cles

- **Multi-pays** : 208 pays, 4600+ villes, 4 devises (EUR, MAD, XOF, TND)
- **Systeme de broadcast** : Ciblage geographique, programmation avec recurrence
- **OnlineTV** : Streaming adaptatif HLS avec overlays
- **Mode hors ligne** : Service Worker + IndexedDB pour le player
- **API mobile** : REST avec JWT et rate limiting

## Comptes de test

Apres `python init_db_demo.py` :

- **Admin** : admin@shabaka-adscreen.com / admin123
- **Etablissements** : manager@restaurant-paris.fr / demo123 (et autres)
- **Player** : code unique de l'ecran + screen123

## Variables d'environnement requises

```
DATABASE_URL           # URL de connexion PostgreSQL
SESSION_SECRET         # Cle secrete pour les cookies de session
SUPERADMIN_EMAIL       # Email du super-administrateur
SUPERADMIN_PASSWORD    # Mot de passe du super-administrateur
```

## Commandes utiles

```bash
# Demarrer l'application
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Initialiser la base de donnees
python init_db.py

# Creer les donnees de demonstration
python init_db_demo.py

# Reinitialiser les donnees de demo
python init_db_demo.py --force
```

## Notes de developpement

- Le port 5000 est obligatoire pour l'interface web
- Les contenus sont stockes dans `static/uploads/`
- Les overlays BROADCAST ont priorite sur les overlays LOCAL
- Le heartbeat player est envoye toutes les 30 secondes
- La facturation est hebdomadaire (lundi a dimanche)

## Notes qualite code

**Fichiers volumineux a refactoriser si necessaire :**
- `routes/admin_routes.py` (1790 lignes)
- `routes/org_routes.py` (1610 lignes)
- `routes/ad_content_routes.py` (901 lignes)

**Librairies externes (non modifiables) :**
- `static/js/mpegts.min.js` - Librairie tierce minifiee, warnings normaux

## Securite

**Corrections XSS appliquees (16/12/2024) :**
- `static/js/main.js` : Remplacement innerHTML par creation d'elements DOM
- `templates/admin/ad_contents/form.html` : Ajout fonction escapeHtml() pour donnees dynamiques
- `templates/player/display.html` : Ajout escapeHtml() + encodeURI() pour chemins et messages

**Bonnes pratiques :**
- Toujours echapper les donnees utilisateur avec escapeHtml() avant insertion HTML
- Utiliser textContent au lieu de innerHTML quand possible
- Valider/sanitizer les chemins de fichiers cote serveur

## Internationalisation (i18n)

**Langues supportees :** Francais (fr), Anglais (en)

**Architecture :**
- `services/translation_service.py` : Service de traduction avec detection du navigateur
- `static/lang/fr.json` et `static/lang/en.json` : Fichiers de traduction
- Widget flottant en bas a gauche pour changer de langue
- Detection automatique de la langue du navigateur

**Convention :**
- Tous les textes utilisateur utilisent la syntaxe `{{ t('cle.souscle') }}`
- Les noms de marque ("Shabaka AdScreen") restent en dur (pratique i18n standard)
- Ajouter les nouvelles cles dans les deux fichiers JSON simultanement

## Dernieres modifications

- 16/12/2024 : Internationalisation complete des routes backend (toutes les flash messages utilisent t())
- 16/12/2024 : Implementation complete du systeme bilingue (FR/EN)
- 16/12/2024 : Corrections vulnerabilites XSS (main.js, ad_contents/form.html, player/display.html)
- 16/12/2024 : Mise a jour documentation structure fichiers
- 12/2024 : Reecriture complete de la documentation
