![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue) ![Framework](https://img.shields.io/badge/Framework-Flask-green) ![Database](https://img.shields.io/badge/Database-PostgreSQL-orange) ![Status](https://img.shields.io/badge/Status-Proprietary-red) ![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red) ![Owner: MOA Digital Agency](https://img.shields.io/badge/Owner-MOA%20Digital%20Agency-purple)

# Shabaka AdScreen

**La solution de Digital Signage "Enterprise-Grade" pour la gestion de flottes d'écrans publicitaires et l'optimisation des revenus.**

---

### ⚠️ AVERTISSEMENT LÉGAL (LEGAL NOTICE)

**CE LOGICIEL EST LA PROPRIÉTÉ EXCLUSIVE DE MOA DIGITAL AGENCY (Aisance KALONJI).**

Tout usage, copie, modification, distribution ou vente de ce code source sans autorisation écrite explicite est **STRICTEMENT INTERDIT** et fera l'objet de poursuites judiciaires immédiates.
Ce dépôt est destiné uniquement à un usage interne pour la sauvegarde et le déploiement sur les infrastructures autorisées par MOA Digital Agency.

---

## 🏛️ Architecture du Système

```mermaid
graph TD
    User[Utilisateurs] -->|HTTPS| LB[Nginx / Load Balancer]
    Mobile[App Mobile] -->|API JWT| LB
    Screen[Écrans / Players] -->|HTTPS / Polling| LB

    LB -->|Reverse Proxy| Gunicorn[Gunicorn WSGI]

    subgraph "Shabaka AdScreen (Monolith)"
        Gunicorn --> Flask[Flask App]

        subgraph "Blueprints (Modules)"
            Flask --> Auth[Authentification]
            Flask --> Admin[Super Admin]
            Flask --> Org[Organisation Dashboard]
            Flask --> Booking[Booking Engine]
            Flask --> Player[Player Logic]
            Flask --> API[Mobile API]
        end

        subgraph "Services"
            Booking --> BillingService[Facturation]
            Player --> PlaylistAlgo[Algo Priorisation]
            API --> AuthJWT[JWT Service]
        end
    end

    Flask -->|SQLAlchemy| DB[(PostgreSQL / SQLite)]
    Flask -->|File System| Storage[Stockage Média]

    BillingService -.->|Cron Job| Invoices[Génération Factures]
```

## 📑 Table des Matières

1.  [Description](#description)
2.  [Stack Technique](#-stack-technique)
3.  [Installation & Démarrage](#-installation--démarrage)
4.  [Documentation](#-documentation)
5.  [Licence](#-licence)

## 📝 Description

Shabaka AdScreen est une plateforme centralisée permettant aux établissements (hôtels, restaurants, malls) de monétiser leurs écrans via la publicité. Elle offre une interface de gestion complète pour les propriétaires d'écrans, un tunnel de réservation pour les annonceurs, et un player web robuste capable de diffuser du contenu multimédia et des flux IPTV.

## 💻 Stack Technique

*   **Langage :** Python 3.11+
*   **Framework Web :** Flask 3.0+
*   **Serveur d'Application :** Gunicorn (avec Gevent Workers)
*   **Base de Données :** PostgreSQL (Prod) / SQLite (Dev)
*   **Frontend :** Jinja2, Tailwind CSS, Vanilla JS
*   **Vidéo/Streaming :** FFmpeg, HLS.js
*   **Sécurité :** Flask-Login, PyJWT, Werkzeug Security, Bleach

## 🚀 Installation & Démarrage

### Prérequis
*   Python 3.11 ou supérieur
*   `pip` et `virtualenv`

### Déploiement Local

1.  **Cloner le dépôt :**
    ```bash
    git clone <url_du_repo>
    cd shabaka-adscreen
    ```

2.  **Créer l'environnement virtuel :**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur Windows: venv\Scripts\activate
    ```

3.  **Installer les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration :**
    Créer un fichier `.env` ou définir les variables d'environnement :
    ```bash
    export FLASK_APP=app.py
    export FLASK_ENV=development
    export SESSION_SECRET="votre_secret_tres_long"
    export DATABASE_URL="sqlite:///shabaka.db"
    ```

5.  **Initialiser la Base de Données :**
    ```bash
    python init_db.py
    ```

6.  **Lancer le serveur :**
    ```bash
    python main.py
    # Ou via Gunicorn :
    # gunicorn -k gevent -w 4 -b 0.0.0.0:8080 app:app
    ```

## 📚 Documentation

La documentation complète est disponible dans le dossier `docs/` :

*   **La Bible des Fonctionnalités :** [docs/Shabaka_AdScreen_features_full_list.md](docs/Shabaka_AdScreen_features_full_list.md)
*   **Manuel Technique :** [docs/Shabaka_AdScreen_Technical_Manual.md](docs/Shabaka_AdScreen_Technical_Manual.md)
*   **Guide Utilisateur :** [docs/Shabaka_AdScreen_User_Guide.md](docs/Shabaka_AdScreen_User_Guide.md)

*(English versions available with suffix `_en.md`)*

## 🔒 Licence

Ce projet est sous licence **Propriétaire**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
Copyright © 2024 MOA Digital Agency.
