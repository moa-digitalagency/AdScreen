# 📺 Shabaka AdScreen - SaaS Location Écrans Publicitaires

Plateforme SaaS permettant aux établissements (bars, restaurants, centres commerciaux) de monétiser leurs écrans publicitaires via un système de location self-service. Support multi-pays et multi-devises (EUR, MAD, XOF, TND).

**Un produit de Shabaka InnovLab**

## ✨ Fonctionnalités principales

### 🌍 Multi-pays & Multi-devises
- 🇫🇷 France (EUR - €)
- 🇲🇦 Maroc (MAD - DH)
- 🇸🇳 Sénégal (XOF - FCFA)
- 🇹🇳 Tunisie (TND - DT)

### 🏢 Gestion multi-établissements
- 👑 Superadmin gère les organisations et commissions
- 📋 Demandes d'inscription via WhatsApp
- 💰 Commission personnalisable par établissement
- 📊 Statistiques par devise

### 📺 Gestion des écrans
- 🖥️ Résolution, orientation, types de contenu acceptés
- 📛 Nommage personnalisé des écrans
- 👁️ Aperçu en direct de ce qui s'affiche
- 🔲 **Overlays superposés** (bandeaux défilants)
- 🎨 Fillers générés automatiquement avec QR code

### 🎭 Système d'overlays
- 📜 Type bandeau: Texte défilant (ticker)
- 📍 Positions: Header (haut), Body (centre), Footer (bas)
- 🎨 Personnalisation: Couleurs, taille de police, vitesse de défilement
- ⏱️ Fréquence configurable par durée ou nombre de passages

### ⏰ Créneaux horaires
- 🕐 Slots configurables avec prix calculés automatiquement
- 🌅 Multiplicateurs de prix (matin, midi, soir, nuit)
- 💵 Prix affichés en devise locale

### 📱 QR Codes & Réservations
- 🔗 Génération automatique par écran
- 🛒 Réservation en libre-service
- 🧾 **Reçu thermique** (image style ticket de caisse)
- 📄 **Reçu PDF** imprimable

### ✅ Validation contenu
- 📤 File d'attente avec aperçu
- 🔍 Validation stricte (ratio, résolution, durée)
- ✔️ Validation/refus manuel avec motif

### 🎮 Player web
- 📺 Interface fullscreen pour diffusion sur écrans
- 🔲 Affichage des overlays en temps réel
- 💓 Heartbeat et statuts temps réel

### 📊 Statistiques
- 📈 Tracking des passages et revenus
- 📉 Analytics par écran, période, devise
- 🕐 Monitoring uptime des écrans

## 📋 Prérequis

- 🐍 Python 3.11+
- 🗄️ PostgreSQL 14+
- 🎥 ffmpeg (pour validation vidéos)

## 🚀 Installation

### 1️⃣ Cloner le projet

```bash
git clone <repository-url>
cd shabaka-adscreen
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
DATABASE_URL=postgresql://user:password@localhost:5432/shabaka_adscreen
SESSION_SECRET=your-secret-key-here
```

### 4️⃣ Initialiser la base de données

```bash
# Créer les tables
python init_db.py

# Créer les données de démonstration (6 organisations, 9 écrans, 4 pays)
python init_db_demo.py
```

## 🎮 Démarrage

### 💻 Développement

```bash
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

### 🌐 Production

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --reuse-port main:app
```

L'application sera accessible sur `http://localhost:5000`

## 👥 Comptes de démonstration

Après avoir exécuté `init_db_demo.py` :

### 👑 Superadmin

| Email | Mot de passe |
|-------|--------------|
| admin@shabaka-adscreen.com | admin123 |

### 🏪 Établissements (mot de passe: demo123)

| Pays | Établissement | Email | Devise |
|------|--------------|-------|--------|
| 🇫🇷 | Le Bistrot Parisien | manager@restaurant-paris.fr | EUR |
| 🇫🇷 | Bar Le Central | manager@bar-lyon.fr | EUR |
| 🇫🇷 | Centre Commercial Atlantis | manager@atlantis-mall.fr | EUR |
| 🇲🇦 | Café Marrakech | manager@cafe-marrakech.ma | MAD |
| 🇸🇳 | Restaurant Dakar Beach | manager@dakar-beach.sn | XOF |
| 🇹🇳 | Tunisian Café | manager@tunis-cafe.tn | TND |

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
│   ├── playlist_service.py
│   ├── pricing_service.py
│   ├── qr_service.py
│   ├── receipt_generator.py  # Reçus thermiques
│   └── filler_generator.py   # Génération fillers
├── 📁 utils/              # Utilitaires
├── 📁 templates/          # Templates Jinja2
├── 📁 static/             # Fichiers statiques
│   └── uploads/           # Contenus uploadés
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
GET /api/playlist/<screen_code>     # Récupère la playlist + overlays
POST /api/heartbeat/<screen_code>   # Signal de vie
POST /api/log-play/<screen_code>    # Log de diffusion
```

## ⚙️ Paramètres Admin

Dans l'espace admin (`/admin`), vous pouvez configurer :
- 📱 Numéro WhatsApp pour recevoir les demandes d'inscription
- 💰 Commissions par défaut/min/max
- 🔍 Paramètres SEO
- 🔧 Mode maintenance

## 🧾 Système de reçus

Après une réservation, le client peut télécharger :
- **Image thermique** : Style ticket de caisse avec en-tête établissement + écran
- **PDF** : Document imprimable

Les reçus incluent :
- Numéro de réservation
- Détails du créneau et des diffusions
- Prix dans la devise de l'établissement
- QR code de vérification
- Statut de validation

## 📄 Licence

Propriétaire - Tous droits réservés - Shabaka InnovLab
