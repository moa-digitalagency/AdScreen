# Documentation Shabaka AdScreen

Bienvenue dans la documentation technique de Shabaka AdScreen, la plateforme SaaS de location d'écrans publicitaires.

## Table des matières

1. [Architecture](architecture.md) - Structure technique du projet
2. [Déploiement](deployment.md) - Guide de mise en production
3. [Comptes de démonstration](demo_accounts.md) - Données de test et configuration
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
- **Authentification** : Utilisez les identifiants configurés dans les variables d'environnement

**Important** : Configurez les identifiants du superadmin via les variables d'environnement `SUPERADMIN_EMAIL` et `SUPERADMIN_PASSWORD` pour la sécurité.

## Fonctionnalités principales

- Multi-devises : Support de 200+ devises à travers 208 pays
- Gestion multi-établissements avec commissions configurables
- Système de diffusion (Broadcast) pour ciblage géographique
- Contenus publicitaires superadmin avec ciblage avancé
- Contrôle par établissement des publicités superadmin (opt-in/opt-out)
- Facturation hebdomadaire automatique
- Player web fullscreen avec overlays temps réel
- Génération de reçus (image thermique et PDF)

## Support

Pour toute question technique, consultez les guides de cette documentation.
