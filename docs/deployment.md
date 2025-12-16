# Guide de déploiement

Ce guide explique comment installer et configurer Shabaka AdScreen en production.

## Prérequis

- **Python 3.11** ou supérieur
- **PostgreSQL 14** ou supérieur
- **ffmpeg** pour la validation des vidéos (optionnel mais recommandé)
- Espace disque suffisant pour stocker les fichiers uploadés

## Variables d'environnement

Quatre variables sont indispensables :

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DATABASE_URL` | URL de connexion PostgreSQL | `postgresql://user:password@localhost:5432/shabaka` |
| `SESSION_SECRET` | Clé secrète pour signer les cookies | Chaîne aléatoire longue |
| `SUPERADMIN_EMAIL` | Email du super-administrateur | `admin@votre-domaine.com` |
| `SUPERADMIN_PASSWORD` | Mot de passe du super-administrateur | Un mot de passe solide |

Le super-administrateur est créé ou mis à jour automatiquement au démarrage de l'application. Ne mettez jamais ces identifiants en clair dans le code.

### Variables optionnelles

| Variable | Description | Défaut |
|----------|-------------|--------|
| `UPLOAD_FOLDER` | Dossier des fichiers uploadés | `static/uploads` |
| `CRON_SECRET` | Clé pour sécuriser les endpoints cron | Aucun |

## Installation pas à pas

### 1. Récupérer le code

```bash
git clone <url-du-dépôt>
cd shabaka-adscreen
```

### 2. Installer les dépendances Python

```bash
# Avec pip
pip install -r requirements.txt

# Ou avec uv (plus rapide)
uv sync
```

### Dépendances principales

Le fichier `requirements.txt` inclut notamment :
- flask et flask-sqlalchemy pour le backend
- flask-login pour l'authentification
- gunicorn pour le serveur de production
- pillow pour les images et les reçus
- reportlab pour les PDF
- qrcode pour les QR codes
- psycopg2-binary pour PostgreSQL

### 3. Configurer la base de données

Créez la base de données PostgreSQL :

```bash
createdb shabaka_adscreen
```

Initialisez les tables :

```bash
python init_db.py
```

Ce script crée toutes les tables et ajoute automatiquement les colonnes manquantes si vous mettez à jour une installation existante.

### 4. Créer les dossiers de stockage

```bash
mkdir -p static/uploads/contents
mkdir -p static/uploads/fillers
mkdir -p static/uploads/internal
mkdir -p static/uploads/broadcasts
chmod -R 755 static/uploads
```

### 5. Démarrer l'application

**En développement** (avec rechargement automatique) :

```bash
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

**En production** :

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 main:app
```

L'application est accessible sur `http://localhost:5000`

## Configuration Gunicorn recommandée

Pour un déploiement robuste :

```bash
gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 4 \
  --threads 2 \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --reuse-port \
  --access-logfile - \
  --error-logfile - \
  main:app
```

## Déploiement sur Replit

Sur Replit, presque tout est automatique :

1. La base de données PostgreSQL est provisionnée automatiquement
2. Les variables d'environnement se configurent dans les Secrets
3. Le workflow "Start application" lance Gunicorn

Pour publier :
1. Cliquez sur "Deploy" dans l'interface Replit
2. L'application sera accessible via une URL `.replit.app`

Les variables Replit auto-configurées :
- `DATABASE_URL`, `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`
- `REPLIT_DEV_DOMAIN`

## Configuration Nginx (reverse proxy)

Si vous placez Nginx devant l'application :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    # Taille max des uploads (ajustez selon vos besoins)
    client_max_body_size 200M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cache des fichiers statiques
    location /static {
        alias /chemin/vers/shabaka-adscreen/static;
        expires 30d;
    }

    # Pour le streaming IPTV
    location /player/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    # Pour le Service Worker (mode hors ligne)
    location /static/js/player-sw.js {
        add_header Cache-Control "no-cache";
        add_header Service-Worker-Allowed "/player/";
        proxy_pass http://127.0.0.1:5000;
    }
}
```

## Données de démonstration

Pour tester l'installation avec des données réalistes :

```bash
python init_db_demo.py
```

Cela crée :
- 7 établissements dans 4 pays (France, Maroc, Sénégal, Tunisie)
- 10 écrans avec différentes résolutions
- Des overlays et des diffusions de test
- 1 établissement en mode gratuit

Pour recommencer à zéro :

```bash
python init_db_demo.py --force
```

Pour tout supprimer :

```bash
python init_db_demo.py --clear
```

## Maintenance

### Sauvegarde de la base de données

```bash
pg_dump -U utilisateur shabaka_adscreen > backup_$(date +%Y%m%d).sql
```

### Restauration

```bash
psql -U utilisateur shabaka_adscreen < backup_20231201.sql
```

### Mise à jour de l'application

```bash
git pull origin main
pip install -r requirements.txt
python init_db.py  # Met à jour le schéma si nécessaire
# Redémarrer l'application
```

## Vérifications

### Points de contrôle

| URL | Attendu |
|-----|---------|
| `/` | Page d'accueil publique |
| `/player` | Formulaire de connexion player |
| `/admin` | Redirection vers login |
| `/catalog` | Liste des écrans publics |

### Métriques à surveiller

- Uptime des écrans (via les logs de heartbeat)
- Nombre de réservations par jour
- Temps de validation des contenus
- Revenus par devise

## Dépannage

### Erreur de connexion à la base de données

1. Vérifiez que PostgreSQL est démarré
2. Vérifiez que `DATABASE_URL` est correcte
3. Vérifiez que l'utilisateur a les droits sur la base

```bash
python init_db.py --check
```

### Erreur d'upload de fichiers

1. Vérifiez que les dossiers `static/uploads/*` existent
2. Vérifiez les permissions (755)
3. Vérifiez la limite de taille dans Nginx si utilisé

### Player qui ne se connecte pas

1. Vérifiez le code unique de l'écran
2. Vérifiez le mot de passe player
3. Vérifiez que l'écran est actif dans le dashboard

### Reçus qui ne s'affichent pas

1. Vérifiez que Pillow est installé
2. Vérifiez que les polices système sont disponibles
3. Vérifiez que la réservation existe

### Diffusions non affichées

1. Vérifiez que la diffusion est active
2. Vérifiez les dates de début/fin
3. Vérifiez le ciblage (pays, ville, établissement, écran)
4. Attendez le prochain rafraîchissement de la playlist (30 secondes)

### Mode hors ligne qui ne fonctionne pas

1. Vérifiez le support Service Worker du navigateur
2. En production, le site doit être en HTTPS
3. Vérifiez que `/static/js/player-sw.js` est accessible
4. Vérifiez l'espace de stockage disponible

## Support

Pour toute question ou problème :
- Consultez les logs de l'application
- Vérifiez la section Dépannage ci-dessus
- Les données de démonstration permettent de tester chaque fonctionnalité isolément
