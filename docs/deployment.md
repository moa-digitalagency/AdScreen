# Guide de Déploiement

## Prérequis

- Python 3.11+
- PostgreSQL 14+
- ffmpeg (pour la validation des vidéos)
- Espace disque suffisant pour les uploads

## Variables d'environnement

| Variable | Description | Obligatoire |
|----------|-------------|-------------|
| `DATABASE_URL` | URL de connexion PostgreSQL | Oui |
| `SESSION_SECRET` | Clé secrète pour les sessions Flask | Oui |
| `UPLOAD_FOLDER` | Chemin du dossier uploads (défaut: static/uploads) | Non |

### Exemple de configuration

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/adscreen"
export SESSION_SECRET="votre-cle-secrete-tres-longue-et-aleatoire"
```

## Installation

### 1. Cloner le projet

```bash
git clone <repository-url>
cd adscreen
```

### 2. Installer les dépendances Python

```bash
# Avec pip
pip install -r requirements.txt

# Ou avec uv (recommandé)
uv sync
```

### 3. Configurer la base de données

```bash
# Créer la base de données PostgreSQL
createdb adscreen

# Initialiser les tables
python init_db.py

# Optionnel : créer les données de démonstration
python init_db_demo.py
```

### 4. Créer les dossiers nécessaires

```bash
mkdir -p static/uploads
chmod 755 static/uploads
```

## Démarrage

### Mode développement

```bash
python main.py
```

L'application sera accessible sur http://localhost:5000 avec le rechargement automatique activé.

### Mode production

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 main:app
```

### Configuration Gunicorn recommandée

```bash
gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 4 \
  --threads 2 \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --access-logfile - \
  --error-logfile - \
  main:app
```

## Déploiement sur Replit

Sur Replit, l'application est déjà configurée pour se lancer automatiquement :

1. La base de données PostgreSQL est provisionnée automatiquement
2. Les variables d'environnement sont configurées dans les Secrets
3. Gunicorn démarre via le workflow "Start application"

Pour publier :
1. Cliquez sur "Deploy" dans l'interface Replit
2. L'application sera accessible via une URL `.replit.app`

## Nginx (Reverse Proxy)

Configuration recommandée pour Nginx :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /chemin/vers/adscreen/static;
        expires 30d;
    }
}
```

## Maintenance

### Sauvegarde de la base de données

```bash
pg_dump -U user adscreen > backup_$(date +%Y%m%d).sql
```

### Restauration

```bash
psql -U user adscreen < backup_20231201.sql
```

### Mise à jour

```bash
git pull origin main
pip install -r requirements.txt
# Relancer l'application
```

## Monitoring

### Logs applicatifs

Les logs sont affichés sur la sortie standard. En production, redirigez-les vers un fichier :

```bash
gunicorn main:app 2>&1 | tee -a /var/log/adscreen/app.log
```

### Points de vérification

- **Santé** : `GET /` doit retourner 200
- **API** : `GET /api/health` (à implémenter)
- **Base de données** : `python init_db.py --check`

## Troubleshooting

### Erreur de connexion à la base de données

Vérifiez que :
1. PostgreSQL est démarré
2. La variable `DATABASE_URL` est correcte
3. L'utilisateur a les droits sur la base

### Erreur d'upload de fichiers

Vérifiez que :
1. Le dossier `static/uploads` existe
2. Les permissions sont correctes (755)
3. `MAX_CONTENT_LENGTH` est suffisant dans `app.py`

### Player écran ne se connecte pas

Vérifiez que :
1. Le code unique de l'écran est correct
2. Le mot de passe player est correct
3. L'écran est actif dans le dashboard
