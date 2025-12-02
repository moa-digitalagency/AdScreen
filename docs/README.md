# Documentation Shabaka AdScreen

Bienvenue dans la documentation technique de Shabaka AdScreen, la plateforme SaaS de location d'écrans publicitaires.

## Table des matières

1. [Architecture](architecture.md) - Structure technique du projet (17 modèles de base de données)
2. [Déploiement](deployment.md) - Guide de mise en production
3. [Comptes de démonstration](demo_accounts.md) - Données de test (6 organisations, 9 écrans, 4 devises)
4. [Fonctionnalités](features.md) - Liste des fonctionnalités
5. [Algorithme de Playlist](Algo.md) - Calcul des playlists et priorités

## Démarrage rapide

### Installation

```bash
# Installer les dépendances
uv sync

# Initialiser la base de données
python init_db.py

# Créer les données de démonstration
python init_db_demo.py

# Démarrer l'application
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

### Accès

- **Application** : http://localhost:5000
- **Login Superadmin** : admin@shabaka-adscreen.com / admin123

## Fonctionnalités principales

- Multi-devises : EUR, MAD, XOF, TND (208 pays supportés)
- Gestion multi-établissements avec commissions personnalisables
- Système de diffusion (Broadcast) pour ciblage géographique
- Facturation hebdomadaire automatique avec preuves de paiement
- Player web fullscreen avec overlays temps réel
- Génération de reçus thermiques (style ticket de caisse) et PDF

## Support

Pour toute question technique, consultez les guides de cette documentation.
