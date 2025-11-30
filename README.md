# 📺 AdScreen - SaaS Location Écrans Publicitaires

Plateforme SaaS permettant aux établissements (bars, restaurants, centres commerciaux) de monétiser leurs écrans publicitaires via un système de location self-service.

## ✨ Fonctionnalités principales

### 🏢 Gestion multi-établissements
- 👑 Superadmin gère les organisations et commissions
- 📋 Demandes d'inscription via WhatsApp
- 💰 Commission personnalisable par établissement

### 📺 Gestion des écrans
- 🖥️ Résolution, orientation, types de contenu acceptés
- 📛 Nommage personnalisé des écrans
- 👁️ Aperçu en direct de ce qui s'affiche
- 🔲 **Overlays superposés** (bandeaux défilants ou images fixes)

### 🎭 Système d'overlays
- 📜 Type bandeau: Texte défilant (ticker)
- 🖼️ Type image: Image fixe
- 📍 Positions: Header (haut), Body (centre), Footer (bas)
- 🎨 Personnalisation: Couleurs, taille de police, vitesse de défilement

### ⏰ Créneaux horaires
- 🕐 Slots configurables avec prix par diffusion
- 🌅 Multiplicateurs de prix (matin, midi, soir, nuit)

### 📱 QR Codes & Réservations
- 🔗 Génération automatique par écran
- 🛒 Réservation en libre-service

### ✅ Validation contenu
- 📤 File d'attente avec aperçu
- 🔍 Validation stricte (ratio, résolution, durée)

### 🎮 Player web
- 📺 Interface fullscreen pour diffusion sur écrans
- 🔲 Affichage des overlays en temps réel
- 💓 Heartbeat et statuts temps réel

### 📊 Statistiques
- 📈 Tracking des passages et revenus
- 📉 Analytics en temps réel

## 📋 Prérequis

- 🐍 Python 3.11+
- 🗄️ PostgreSQL
- 🎥 ffmpeg (pour validation vidéos)

## 🚀 Installation

### 1️⃣ Cloner le projet

```bash
git clone <repository-url>
cd adscreen
```

### 2️⃣ Installer les dépendances

```bash
# Avec pip
pip install -r requirements.txt

# Ou avec uv (recommandé)
uv sync
```

### 3️⃣ Configuration

Configurer les variables d'environnement :

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/adscreen
SESSION_SECRET=your-secret-key-here
```

### 4️⃣ Initialiser la base de données

```bash
# Créer les tables
python init_db.py

# Optionnel : Créer les données de démonstration
python init_db_demo.py
```

## 🎮 Démarrage

### 💻 Développement

```bash
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

### 🌐 Production

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

L'application sera accessible sur `http://localhost:5000`

## 👥 Comptes de démonstration

Après avoir exécuté `init_db_demo.py` :

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| 👑 Superadmin | admin@adscreen.com | admin123 |
| 🏪 Le Bistrot Parisien | manager@restaurant-paris.fr | demo123 |
| 🍺 Bar Le Central | manager@bar-lyon.fr | demo123 |
| 🏬 Centre Commercial Atlantis | manager@atlantis-mall.fr | demo123 |

🔑 Mot de passe player pour tous les écrans : `screen123`

## 📁 Structure du projet

```
├── 📄 app.py              # Configuration Flask
├── 📄 main.py             # Point d'entrée
├── 📄 requirements.txt    # Dépendances Python
├── 🗄️ init_db.py          # Initialisation base de données
├── 🎮 init_db_demo.py     # Données de démonstration
├── 📁 models/             # Modèles SQLAlchemy
├── 📁 routes/             # Routes Flask (blueprints)
├── 📁 services/           # Logique métier
├── 📁 utils/              # Utilitaires
├── 📁 templates/          # Templates Jinja2
├── 📁 static/             # Fichiers statiques
└── 📁 docs/               # Documentation
```

## 📚 Documentation

- 📖 [Déploiement](docs/deployment.md)
- 👥 [Comptes de démonstration](docs/demo_accounts.md)
- ✨ [Fonctionnalités](docs/features.md)
- 🏗️ [Architecture](docs/architecture.md)

## 🔌 API Player

Le player écran communique avec l'API pour récupérer la playlist :

```
GET /api/playlist/<screen_code>
POST /api/heartbeat/<screen_code>
POST /api/log-play/<screen_code>
```

## ⚙️ Paramètres Admin

Dans l'espace admin, vous pouvez configurer :
- 📱 Numéro WhatsApp pour recevoir les demandes d'inscription
- 💰 Commissions par défaut/min/max
- 🔍 Paramètres SEO
- 🔧 Mode maintenance

## 📄 Licence

Propriétaire - Tous droits réservés
