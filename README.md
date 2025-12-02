# Shabaka AdScreen - SaaS Location Écrans Publicitaires

Plateforme SaaS permettant aux établissements (bars, restaurants, centres commerciaux) de monétiser leurs écrans publicitaires via un système de location self-service. Support multi-pays et multi-devises (EUR, MAD, XOF, TND).

**Un produit de Shabaka InnovLab**

## Fonctionnalités principales

### Multi-pays & Multi-devises (208 pays, 4600+ villes)
- France (EUR)
- Maroc (MAD)
- Sénégal (XOF)
- Tunisie (TND)
- Et 200+ autres pays avec sélection dynamique de ville

### Gestion multi-établissements
- Superadmin gère les organisations et commissions
- Demandes d'inscription via WhatsApp
- Commission personnalisable par établissement
- Statistiques par devise

### Gestion des écrans
- Résolution, orientation, types de contenu acceptés
- Nommage personnalisé des écrans
- Aperçu en direct de ce qui s'affiche
- **Overlays superposés** (bandeaux défilants)
- Fillers générés automatiquement avec QR code

### Système d'overlays
- Type bandeau: Texte défilant (ticker)
- Positions: Header (haut), Body (centre), Footer (bas)
- Personnalisation: Couleurs, taille de police, vitesse de défilement
- Fréquence configurable par durée ou nombre de passages

### Système de diffusion (Broadcast) - NOUVEAU
- Diffusion centralisée par le superadmin
- Ciblage par pays, ville, établissement ou écran spécifique
- Types: Overlay (bandeau) ou contenu playlist
- **Modes de programmation**: Immédiat ou Programmé avec date/heure exacte
- **Système de récurrence**: Unique, quotidien, hebdomadaire (jours sélectionnables), mensuel
- **Priorité configurable** (20-200) avec option override pour décaler la playlist
- Programmation avec dates de début/fin

### Créneaux horaires
- Slots configurables avec prix calculés automatiquement
- Multiplicateurs de prix (matin, midi, soir, nuit)
- Prix affichés en devise locale

### QR Codes & Réservations
- Génération automatique par écran
- Réservation en libre-service
- **Reçu thermique** (image style ticket de caisse)
- **Reçu PDF** imprimable

### Validation contenu
- File d'attente avec aperçu
- Validation stricte (ratio, résolution, durée)
- Validation/refus manuel avec motif

### Player web
- Interface fullscreen pour diffusion sur écrans
- Affichage des overlays en temps réel
- Réception des diffusions (broadcasts) centralisées
- Heartbeat et statuts temps réel

### Statistiques
- Tracking des passages et revenus
- Analytics par écran, période, devise
- Monitoring uptime des écrans

## Prérequis

- Python 3.11+
- PostgreSQL 14+
- ffmpeg (pour validation vidéos)

## Installation

### 1. Cloner le projet

```bash
git clone <repository-url>
cd shabaka-adscreen
```

### 2. Installer les dépendances

```bash
# Avec pip
pip install -r requirements.txt

# Ou avec uv (recommandé)
uv sync
```

### 3. Configuration

Configurer les variables d'environnement :

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/shabaka_adscreen
SESSION_SECRET=your-secret-key-here
SUPERADMIN_EMAIL=admin@votre-domaine.com
SUPERADMIN_PASSWORD=mot-de-passe-securise
```

**Important** : Les identifiants du super-administrateur doivent être stockés dans des variables d'environnement, jamais en clair dans le code.

### 4. Initialiser la base de données

```bash
# Créer les tables
python init_db.py

# Créer les données de démonstration (6 organisations, 9 écrans, 4 pays, 4 diffusions)
python init_db_demo.py
```

## Démarrage

### Développement

```bash
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

### Production

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --reuse-port main:app
```

L'application sera accessible sur `http://localhost:5000`

## Comptes de démonstration

Après avoir exécuté `init_db_demo.py` (pour test uniquement) :

### Superadmin (démo)

| Email | Mot de passe |
|-------|--------------|
| admin@shabaka-adscreen.com | admin123 |

> **Note** : En production, utilisez les variables d'environnement `SUPERADMIN_EMAIL` et `SUPERADMIN_PASSWORD`.

### Établissements (mot de passe: demo123)

| Pays | Établissement | Email | Devise |
|------|--------------|-------|--------|
| FR | Le Bistrot Parisien | manager@restaurant-paris.fr | EUR |
| FR | Bar Le Central | manager@bar-lyon.fr | EUR |
| FR | Centre Commercial Atlantis | manager@atlantis-mall.fr | EUR |
| MA | Café Marrakech | manager@cafe-marrakech.ma | MAD |
| SN | Restaurant Dakar Beach | manager@dakar-beach.sn | XOF |
| TN | Tunisian Café | manager@tunis-cafe.tn | TND |

Mot de passe player pour tous les écrans : `screen123`

### Diffusions de démonstration

| Nom | Ciblage | Mode | Récurrence |
|-----|---------|------|------------|
| Promotion Été France | Pays: FR | Immédiat | - |
| Message Marrakech | Ville: Marrakech | Immédiat | - |
| Promo Centre Atlantis | Établissement | Programmé | Quotidien 12h |
| Info Écran Beach | Écran spécifique | Programmé | Hebdo ven/sam |
| Promo Mensuelle Tunisie | Pays: TN | Programmé | Mensuel |

## Structure du projet

```
├── app.py              # Configuration Flask
├── main.py             # Point d'entrée
├── requirements.txt    # Dépendances Python
├── init_db.py          # Initialisation base de données
├── init_db_demo.py     # Données de démonstration
├── models/             # Modèles SQLAlchemy
│   └── broadcast.py    # Modèle diffusions
├── routes/             # Routes Flask (blueprints)
├── services/           # Logique métier
│   ├── playlist_service.py
│   ├── pricing_service.py
│   ├── qr_service.py
│   ├── receipt_generator.py  # Reçus thermiques
│   └── filler_generator.py   # Génération fillers
├── utils/              # Utilitaires
│   └── countries.py    # Noms des pays
├── templates/          # Templates Jinja2
│   └── admin/
│       └── broadcasts/ # Gestion diffusions
├── static/             # Fichiers statiques
│   └── uploads/        # Contenus uploadés
└── docs/               # Documentation
```

## Documentation

- [Déploiement](docs/deployment.md)
- [Comptes de démonstration](docs/demo_accounts.md)
- [Fonctionnalités](docs/features.md)
- [Architecture](docs/architecture.md)

## API Player

Le player écran communique avec l'API pour récupérer la playlist :

```
GET /api/playlist/<screen_code>     # Récupère la playlist + overlays + broadcasts
POST /api/heartbeat/<screen_code>   # Signal de vie
POST /api/log-play/<screen_code>    # Log de diffusion
```

## Espace Admin

Dans l'espace admin (`/admin`), vous pouvez configurer :
- Établissements (payants ou gratuits) et écrans
- **Gestion des administrateurs** avec permissions granulaires
- Numéro WhatsApp pour recevoir les demandes d'inscription
- Commissions par défaut/min/max
- Paramètres SEO
- Mode maintenance
- **Diffusions (Broadcasts)** : Pousser du contenu vers les écrans ciblés

### Types d'établissements

- **Payant** : Accès complet (réservations, facturation, créneaux, périodes, contenus internes, overlays)
- **Gratuit** : Fonctionnalités limitées (contenus internes et overlays uniquement)

### Gestion des administrateurs

Le superadmin peut créer d'autres administrateurs avec des permissions spécifiques pour chaque menu (tableau de bord, établissements, écrans, diffusions, statistiques, facturation, demandes, paramètres, utilisateurs).

## Système de diffusion (Broadcast)

Les superadmins peuvent diffuser du contenu vers plusieurs écrans :

1. Accédez à `/admin` et connectez-vous
2. Cliquez sur "Diffusion" dans le menu
3. Créez une nouvelle diffusion
4. Choisissez le ciblage (pays, ville, établissement, écran)
5. Configurez le type (overlay ou contenu)
6. **Choisissez le mode de programmation**:
   - **Immédiat**: Diffusion active dès activation
   - **Programmé**: Définir date/heure + récurrence optionnelle
7. **Définissez la priorité** (20-200) et l'option override
8. Activez la diffusion

Les diffusions apparaissent automatiquement sur les players ciblés selon leur programmation.

## Système de reçus

Après une réservation, le client peut télécharger :
- **Image thermique** : Style ticket de caisse avec en-tête établissement + écran
- **PDF** : Document imprimable

Les reçus incluent :
- Numéro de réservation
- Détails du créneau et des diffusions
- Prix dans la devise de l'établissement
- QR code de vérification
- Statut de validation

## Licence

Propriétaire - Tous droits réservés - Shabaka InnovLab
