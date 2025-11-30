# AdScreen - SaaS Location Écrans Publicitaires

Plateforme SaaS permettant aux établissements (bars, restaurants, centres commerciaux) de monétiser leurs écrans publicitaires via un système de location self-service.

## Fonctionnalités principales

- **Gestion multi-établissements** : Superadmin gère les organisations et commissions
- **Configuration écrans** : Résolution, orientation, types de contenu acceptés
- **Créneaux horaires** : Slots configurables avec prix par diffusion
- **Périodes journée** : Multiplicateurs de prix (matin, midi, soir, nuit)
- **QR Codes** : Génération automatique par écran pour accès client
- **Validation contenu** : File d'attente avec aperçu et validation stricte
- **Player web** : Interface fullscreen pour diffusion sur écrans
- **Statistiques** : Tracking des passages et revenus

## Prérequis

- Python 3.11+
- PostgreSQL
- ffmpeg (pour validation vidéos)

## Installation

### 1. Cloner le projet

```bash
git clone <repository-url>
cd adscreen
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
# ou avec uv
uv sync
```

### 3. Configuration

Créer un fichier `.env` ou configurer les variables d'environnement :

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/adscreen
SESSION_SECRET=your-secret-key-here
```

### 4. Initialiser la base de données

```bash
# Créer les tables
python init_db.py

# Optionnel : Créer les données de démonstration
python init_db_demo.py
```

## Démarrage

### Développement

```bash
python main.py
```

### Production

```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

L'application sera accessible sur `http://localhost:5000`

## Comptes de démonstration

Après avoir exécuté `init_db_demo.py` :

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Superadmin | admin@adscreen.com | admin123 |
| Établissement | demo@restaurant-paris.fr | demo123 |
| Établissement | contact@bar-lyon.fr | demo123 |

## Structure du projet

```
├── app.py              # Configuration Flask
├── main.py             # Point d'entrée
├── init_db.py          # Initialisation base de données
├── init_db_demo.py     # Données de démonstration
├── models/             # Modèles SQLAlchemy
├── routes/             # Routes Flask (blueprints)
├── services/           # Logique métier
├── utils/              # Utilitaires
├── templates/          # Templates Jinja2
├── static/             # Fichiers statiques
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
GET /api/playlist/<screen_code>
POST /api/heartbeat/<screen_code>
POST /api/log-play/<screen_code>
```

## Licence

Propriétaire - Tous droits réservés
