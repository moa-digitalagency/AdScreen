# Documentation AdScreen

Bienvenue dans la documentation technique d'AdScreen, la plateforme SaaS de location d'écrans publicitaires.

## Table des matières

1. [Architecture](architecture.md) - Structure technique du projet
2. [Déploiement](deployment.md) - Guide de mise en production
3. [Comptes de démonstration](demo_accounts.md) - Données de test
4. [Fonctionnalités](features.md) - Liste des fonctionnalités

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
- **Login Superadmin** : admin@adscreen.com / admin123

## Support

Pour toute question technique, consultez les guides de cette documentation.
