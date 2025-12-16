# Shabaka AdScreen

## À propos du projet

Shabaka AdScreen est une plateforme SaaS qui permet aux établissements (restaurants, bars, centres commerciaux, hôtels) de monétiser leurs écrans d'affichage. Les annonceurs locaux réservent des créneaux publicitaires directement via un QR code, sans intermédiaire.

## Stack technique

- **Backend** : Flask 3.x avec Python 3.11
- **Base de données** : PostgreSQL avec SQLAlchemy 2.x
- **Frontend** : Templates Jinja2, Tailwind CSS 3.4 (CDN)
- **Authentification** : Flask-Login (sessions), PyJWT (API mobile)
- **Serveur** : Gunicorn avec gevent
- **Streaming** : HLS.js, mpegts.js (fallback)

## Architecture

```
shabaka-adscreen/
├── app.py              # Configuration Flask et initialisation
├── main.py             # Point d'entrée de l'application
├── init_db.py          # Script de création/mise à jour du schéma
├── init_db_demo.py     # Données de démonstration
├── models/             # 15+ modèles SQLAlchemy (User, Screen, Booking...)
├── routes/             # 8 blueprints Flask (admin, org, player, booking...)
├── services/           # Logique métier (playlist, pricing, QR, receipts...)
├── utils/              # Utilitaires (world_data avec 208 pays, currencies...)
├── templates/          # Templates Jinja2 organisés par module
├── static/             # CSS, JS, uploads
└── docs/               # Documentation complète
```

## Interfaces

La plateforme expose 4 interfaces distinctes :

1. **Admin** (`/admin`) - Console opérateur : gestion des établissements, commissions, diffusions, facturation
2. **Organisation** (`/org`) - Tableau de bord établissement : écrans, contenus, overlays, statistiques
3. **Booking** (`/book/<code>`) - Interface annonceur : réservation via QR code, upload, paiement
4. **Player** (`/player`) - Diffusion sur écran : playlist, overlays, mode OnlineTV

## Fonctionnalités clés

- **Multi-pays** : 208 pays, 4600+ villes, 4 devises (EUR, MAD, XOF, TND)
- **Système de broadcast** : Ciblage géographique, programmation avec récurrence
- **OnlineTV** : Streaming adaptatif HLS avec overlays
- **Mode hors ligne** : Service Worker + IndexedDB pour le player
- **API mobile** : REST avec JWT et rate limiting

## Comptes de test

Après `python init_db_demo.py` :

- **Admin** : admin@shabaka-adscreen.com / admin123
- **Établissements** : manager@restaurant-paris.fr / demo123 (et autres)
- **Player** : code unique de l'écran + screen123

## Documentation

Toute la documentation est dans le dossier `docs/` :

- `README.md` - Vue d'ensemble de la documentation
- `features.md` - Guide complet des fonctionnalités
- `architecture.md` - Structure technique détaillée
- `Algo.md` - Algorithmes métier (prix, disponibilités, playlist)
- `deployment.md` - Guide de déploiement
- `VPS_DEPLOYMENT.md` - Déploiement sur serveur privé
- `demo_accounts.md` - Comptes de test et scénarios
- `COMMERCIAL_PRESENTATION.md` - Pitch commercial
- `API_MOBILE_DOCUMENTATION.md` - API REST avec sessions
- `API_MOBILE_V1_SECURE.md` - API REST avec JWT
- `PLAYER_MOBILE_SDK.md` - Guide développement player natif

## Variables d'environnement requises

```
DATABASE_URL           # URL de connexion PostgreSQL
SESSION_SECRET         # Clé secrète pour les cookies de session
SUPERADMIN_EMAIL       # Email du super-administrateur
SUPERADMIN_PASSWORD    # Mot de passe du super-administrateur
```

## Commandes utiles

```bash
# Démarrer l'application
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Initialiser la base de données
python init_db.py

# Créer les données de démonstration
python init_db_demo.py

# Réinitialiser les données de démo
python init_db_demo.py --force
```

## Notes de développement

- Le port 5000 est obligatoire pour l'interface web
- Les contenus sont stockés dans `static/uploads/`
- Les overlays BROADCAST ont priorité sur les overlays LOCAL
- Le heartbeat player est envoyé toutes les 30 secondes
- La facturation est hebdomadaire (lundi à dimanche)

## Dernières modifications

- Réécriture complète de la documentation (12/2024)
  - Style plus naturel et humain
  - Contenu plus détaillé et complet
  - Exemples de code mis à jour
  - Structure améliorée pour faciliter la navigation
