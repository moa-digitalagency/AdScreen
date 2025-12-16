# Architecture technique

Ce document décrit la structure du code et les choix techniques de Shabaka AdScreen.

## Vue d'ensemble

Shabaka AdScreen est une application web monolithique construite avec Flask. Elle suit une architecture MVC (Modèle-Vue-Contrôleur) avec une séparation claire entre les couches de données, de logique métier et de présentation.

```
┌─────────────────────────────────────────────────────────────┐
│                     NAVIGATEUR                               │
│  Templates Jinja2 + Tailwind CSS + JavaScript               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     ROUTES (Blueprints Flask)               │
│  auth / admin / org / screen / booking / player / api       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     SERVICES                                 │
│  Playlist / Pricing / QR / Receipt / Filler / Currency      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     MODÈLES (SQLAlchemy)                    │
│  User / Organization / Screen / Content / Booking / ...    │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     BASE DE DONNÉES                         │
│                     PostgreSQL                              │
└─────────────────────────────────────────────────────────────┘
```

## Technologies utilisées

### Backend

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Framework | Flask 3.x | Gestion des requêtes HTTP, routing, sessions |
| ORM | SQLAlchemy 2.x | Mapping objet-relationnel, requêtes à la base |
| Base de données | PostgreSQL 14+ | Stockage persistant |
| Authentification | Flask-Login | Gestion des sessions utilisateur |
| Serveur WSGI | Gunicorn | Serveur de production |
| Images | Pillow | Validation, redimensionnement, génération de reçus |
| PDF | ReportLab | Génération de reçus PDF |
| QR Codes | qrcode | Génération des QR codes |
| JWT | PyJWT | Tokens d'authentification pour l'API mobile |
| Rate limiting | Flask-Limiter | Protection contre les abus d'API |

### Frontend

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Templates | Jinja2 | Génération HTML côté serveur |
| CSS | Tailwind CSS 3.4 (CDN) | Styles utilitaires |
| Icônes | Font Awesome 6 | Iconographie |
| Polices | Inter, JetBrains Mono | Typographie |
| Streaming | HLS.js | Lecture de flux HLS/M3U8 |
| Fallback streaming | mpegts.js | Lecture de flux MPEG-TS |

## Structure des fichiers

```
shabaka-adscreen/
├── app.py                    # Configuration Flask et initialisation
├── main.py                   # Point d'entrée de l'application
├── init_db.py                # Script de création/mise à jour de la base
├── init_db_demo.py           # Script de création des données de test
│
├── models/                   # Modèles SQLAlchemy
│   ├── __init__.py           # Exports des modèles
│   ├── user.py               # Utilisateurs (superadmin, admin, manager)
│   ├── organization.py       # Établissements
│   ├── screen.py             # Écrans
│   ├── time_slot.py          # Créneaux horaires
│   ├── time_period.py        # Périodes de la journée
│   ├── content.py            # Contenus uploadés
│   ├── booking.py            # Réservations
│   ├── filler.py             # Contenus de remplissage
│   ├── internal_content.py   # Contenus internes établissement
│   ├── broadcast.py          # Diffusions centralisées
│   ├── screen_overlay.py     # Bandeaux et overlays
│   ├── invoice.py            # Factures et preuves de paiement
│   ├── ad_content.py         # Contenus publicitaires opérateur
│   ├── stat_log.py           # Logs de diffusion
│   ├── heartbeat_log.py      # Logs de connexion des écrans
│   ├── site_setting.py       # Configuration globale
│   └── registration_request.py # Demandes d'inscription
│
├── routes/                   # Blueprints Flask (contrôleurs)
│   ├── __init__.py           # Enregistrement des blueprints
│   ├── auth_routes.py        # Authentification (login, logout)
│   ├── admin_routes.py       # Interface opérateur
│   ├── org_routes.py         # Interface établissement
│   ├── screen_routes.py      # Configuration des écrans
│   ├── booking_routes.py     # Réservation annonceur
│   ├── player_routes.py      # Player et API playlist
│   ├── billing_routes.py     # Facturation
│   ├── api_routes.py         # API REST générale
│   ├── ad_content_routes.py  # Gestion Ad Content
│   └── mobile_api_routes.py  # API mobile sécurisée
│
├── services/                 # Logique métier
│   ├── __init__.py
│   ├── playlist_service.py   # Génération des playlists
│   ├── pricing_service.py    # Calcul des prix
│   ├── qr_service.py         # Génération des QR codes
│   ├── receipt_generator.py  # Génération des reçus
│   ├── filler_generator.py   # Génération des fillers
│   ├── currency_service.py   # Gestion des devises
│   ├── availability_service.py # Calcul des disponibilités
│   ├── overlay_service.py    # Gestion des overlays
│   ├── iptv_service.py       # Parsing M3U et gestion OnlineTV
│   ├── hls_converter.py      # Conversion de flux
│   ├── jwt_service.py        # Génération/validation des tokens
│   ├── rate_limiter.py       # Configuration du rate limiting
│   └── input_validator.py    # Validation des entrées utilisateur
│
├── utils/                    # Utilitaires
│   ├── __init__.py
│   ├── image_utils.py        # Traitement des images
│   ├── video_utils.py        # Traitement des vidéos
│   ├── world_data.py         # Données pays/villes (208 pays, 4600+ villes)
│   ├── currencies.py         # Définition des devises
│   └── countries.py          # Noms des pays pour affichage
│
├── templates/                # Templates Jinja2
│   ├── base.html             # Template de base
│   ├── index.html            # Page d'accueil publique
│   ├── catalog.html          # Catalogue des écrans
│   ├── admin/                # Templates interface opérateur
│   ├── org/                  # Templates interface établissement
│   ├── booking/              # Templates réservation
│   ├── player/               # Templates player
│   └── auth/                 # Templates authentification
│
├── static/                   # Fichiers statiques
│   ├── css/                  # Feuilles de style
│   ├── js/                   # JavaScript (player, etc.)
│   └── uploads/              # Fichiers uploadés
│       ├── contents/         # Contenus clients
│       ├── fillers/          # Contenus filler par organisation
│       ├── internal/         # Contenus internes
│       └── broadcasts/       # Contenus diffusions
│
└── docs/                     # Documentation
```

## Modèle de données

### Relations principales

```
User ──────────────────┐
  │                    │
  │ appartient à       │ gère
  ▼                    ▼
Organization ──────► Screen
  │                    │
  │ a plusieurs        │ a plusieurs
  │                    │
  ├── TimeSlot         ├── Content ──► Booking
  ├── TimePeriod       ├── Filler
  ├── InternalContent  ├── ScreenOverlay
  ├── Invoice          └── HeartbeatLog
  └── RegistrationRequest

Broadcast (ciblage: pays/ville/org/écran)
  │
  └──► Affiché sur les écrans ciblés

AdContent (ciblage: pays/ville/org/écran)
  │
  └──► Diffusé selon le paramètre allow_ad_content
```

### Entités clés

**User** : Représente tout utilisateur de la plateforme. Le champ `role` distingue les superadmins des admins et des managers d'établissement. Les admins ont des permissions granulaires stockées en JSON.

**Organization** : Un établissement (restaurant, bar, centre commercial). Contient la devise, le pays, la ville, le taux de commission et les paramètres OnlineTV.

**Screen** : Un écran physique. Définit la résolution, l'orientation, le prix par minute, les types de contenu acceptés, le mode actuel (playlist ou IPTV).

**TimeSlot** : Un créneau horaire (ex: image 15 secondes). Le prix est calculé automatiquement à partir du prix par minute de l'écran.

**TimePeriod** : Une période de la journée (ex: soir 18h-22h). Contient un multiplicateur de prix.

**Content** : Un contenu uploadé par un client. Référence le fichier, la résolution, la durée, le statut de validation.

**Booking** : Une réservation liant un contenu à un écran. Contient les dates, le nombre de diffusions, le prix, le statut.

**Filler** : Contenu de remplissage généré automatiquement. Affiché quand il n'y a pas d'autre contenu.

**InternalContent** : Contenu créé par l'établissement pour sa propre promotion.

**Broadcast** : Diffusion centralisée créée par l'opérateur. Contient le ciblage, le type (overlay ou contenu), la programmation, la priorité.

**ScreenOverlay** : Bandeau défilant créé par l'établissement. Contient le texte, le style, la position, la fréquence.

**Invoice** : Facture hebdomadaire. Contient le montant, la commission, le statut, la preuve de paiement.

**StatLog** : Log de diffusion. Enregistre chaque passage d'un contenu sur un écran.

**HeartbeatLog** : Log de connexion. Enregistre les signaux envoyés par les écrans.

### Devises supportées

| Code | Symbole | Format | Pays |
|------|---------|--------|------|
| EUR | € | 2,50 € | France, Europe |
| MAD | DH | 25,00 DH | Maroc |
| XOF | FCFA | 1 500 FCFA | Afrique de l'Ouest |
| TND | DT | 8,00 DT | Tunisie |

## Flux de données

### Réservation d'un annonceur

```
1. Annonceur scanne le QR code
   GET /book/<code>

2. Le serveur récupère l'écran et ses créneaux
   SELECT screen, time_slots, time_periods FROM ...

3. Annonceur remplit le formulaire et uploade son contenu
   POST /book/<code>/submit (multipart/form-data)

4. Validation automatique du fichier (résolution, durée, taille)

5. Création du contenu et de la réservation en base
   INSERT INTO content, booking

6. Génération du reçu thermique et redirection vers la confirmation
```

### Récupération de la playlist par le player

```
1. Player demande la playlist
   GET /player/api/playlist

2. Le serveur identifie l'écran via la session

3. Récupération des contenus actifs
   - Contenus payants validés (priorité 100)
   - Contenus internes (priorité 80)
   - Contenus publicitaires opérateur si autorisés (priorité 60)
   - Fillers (priorité 20)

4. Récupération des diffusions centralisées actives
   - Vérification du ciblage (pays, ville, org, écran)
   - Vérification de la programmation et des récurrences
   - Ajout avec priorité jusqu'à 200

5. Récupération des overlays
   - Overlays de l'établissement
   - Overlays des diffusions

6. Réponse JSON avec playlist + overlays triés par priorité
```

### Heartbeat et monitoring

```
1. Player envoie un signal toutes les 30 secondes
   POST /player/api/heartbeat { status: "playing" }

2. Mise à jour de l'écran en base
   UPDATE screen SET last_heartbeat = NOW(), status = 'online'

3. Les interfaces admin et org affichent le statut en temps réel
   Un écran est "online" si son dernier heartbeat date de moins de 2 minutes
```

### Diffusion centralisée

```
1. Opérateur crée une diffusion depuis /admin
   POST /admin/broadcasts/new

2. Définition du ciblage et de la programmation
   INSERT INTO broadcast

3. Au prochain rafraîchissement de playlist
   - Le player demande sa playlist
   - Le serveur vérifie les diffusions actives correspondant à l'écran
   - Les diffusions sont ajoutées à la playlist avec leur priorité

4. Si mode "overlay", le bandeau s'affiche par-dessus le contenu
   Si mode "contenu", il s'insère dans la rotation de la playlist
```

## Sécurité

### Authentification

**Sessions Flask** : Les utilisateurs (admin, manager) sont authentifiés via des cookies de session signés. La clé secrète est définie par la variable d'environnement `SESSION_SECRET`.

**Flask-Login** : Gère le cycle de vie des sessions utilisateur (login, logout, protection des routes).

**Mots de passe** : Hashés avec Werkzeug (PBKDF2-SHA256). Ne jamais stocker de mots de passe en clair.

**JWT pour l'API mobile** : Les applications mobiles utilisent des tokens JWT avec expiration. Access token (24h) et refresh token (30 jours).

### Autorisation

**Décorateurs** : Les routes protégées utilisent `@login_required`. Les routes admin vérifient le rôle de l'utilisateur.

**Permissions granulaires** : Les admins peuvent avoir des permissions limitées stockées en JSON dans le champ `permissions` du modèle User.

**Isolation des données** : Chaque établissement ne voit que ses propres écrans, contenus et statistiques.

### Protection des fichiers

**Validation** : Les fichiers uploadés sont validés (format, résolution, durée, taille) avant d'être acceptés.

**Stockage** : Les fichiers sont stockés dans `static/uploads/` avec des noms générés (hash) pour éviter les collisions et les attaques par traversée de chemin.

### Rate limiting

L'API mobile est protégée par Flask-Limiter :
- Login : 5 requêtes/minute
- Refresh token : 10 requêtes/minute
- Playlist : 60 requêtes/minute
- Heartbeat : 120 requêtes/minute

## Performance

### Optimisations actuelles

**Lazy loading** : Les relations SQLAlchemy sont chargées à la demande.

**Pool de connexions** : SQLAlchemy maintient un pool de connexions PostgreSQL avec recyclage automatique.

**Cache statique** : Les fichiers statiques sont servis avec des headers de cache appropriés.

### Points d'attention

**Taille des fichiers** : Les vidéos peuvent atteindre 200 Mo. Prévoir un stockage suffisant et une limite de taille dans Nginx si utilisé en reverse proxy.

**Heartbeat** : Avec de nombreux écrans, les heartbeats génèrent beaucoup de requêtes. Le système actuel tient bien jusqu'à quelques centaines d'écrans.

**Streaming IPTV** : Les flux MPEG-TS passent par un proxy serveur, ce qui consomme de la bande passante. Les flux HLS natifs sont préférables.

## Tests et débogage

### Données de démonstration

```bash
python init_db_demo.py
```

Crée 7 établissements dans 4 pays, 10 écrans, des overlays et des diffusions de test.

### Logs

Flask est configuré en mode debug avec logging au niveau DEBUG. Les erreurs sont affichées dans la console.

### Points de vérification

- `GET /` : Page d'accueil publique
- `GET /player` : Formulaire de connexion player
- `GET /admin` : Redirection vers login admin
- `GET /api/health` : Statut de l'API

## Extension et personnalisation

### Ajouter une nouvelle devise

1. Ajouter la devise dans `utils/currencies.py`
2. Ajouter le pays dans `utils/world_data.py` avec la devise par défaut
3. Mettre à jour le service de devises si nécessaire

### Ajouter un nouveau type d'overlay

1. Définir le type dans le modèle `ScreenOverlay`
2. Ajouter le rendu dans le template du player
3. Ajouter l'interface de configuration dans les templates org

### Ajouter une nouvelle permission admin

1. Ajouter la permission dans la liste du template `user_form.html`
2. Ajouter la vérification dans les routes concernées
3. Mettre à jour la documentation

## Déploiement

L'application est conçue pour tourner sur :

**Replit** : Configuration automatique, base PostgreSQL provisionnée, déploiement en un clic.

**VPS classique** : Gunicorn + Nginx + systemd, avec script `init_db.py` pour les mises à jour de schéma.

Voir les guides [deployment.md](deployment.md) et [VPS_DEPLOYMENT.md](VPS_DEPLOYMENT.md) pour les instructions détaillées.
