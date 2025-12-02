# Guide de Déploiement - Shabaka AdScreen

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
| `SUPERADMIN_EMAIL` | Email du super-administrateur | Oui |
| `SUPERADMIN_PASSWORD` | Mot de passe du super-administrateur | Oui |
| `UPLOAD_FOLDER` | Chemin du dossier uploads (défaut: static/uploads) | Non |
| `REPLIT_DEV_DOMAIN` | Domaine Replit (auto-configuré) | Non |

### Configuration du Super-Administrateur

Les identifiants du super-administrateur sont stockés de manière sécurisée via des variables d'environnement. **Ne jamais écrire ces identifiants en clair dans le code source.**

Au démarrage de l'application, le super-administrateur est automatiquement créé ou mis à jour avec les identifiants fournis.

### Exemple de configuration

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/shabaka_adscreen"
export SESSION_SECRET="votre-cle-secrete-tres-longue-et-aleatoire"
export SUPERADMIN_EMAIL="admin@votre-domaine.com"
export SUPERADMIN_PASSWORD="mot-de-passe-securise"
```

## Installation

### 1. Cloner le projet

```bash
git clone <repository-url>
cd shabaka-adscreen
```

### 2. Installer les dépendances Python

```bash
# Avec pip
pip install -r requirements.txt

# Ou avec uv (recommandé)
uv sync
```

### Dépendances principales

- flask
- flask-sqlalchemy
- flask-login
- gunicorn
- psycopg2-binary
- pillow (génération reçus thermiques)
- reportlab (génération PDF)
- qrcode
- pyjwt
- email-validator
- werkzeug

### 3. Configurer la base de données

```bash
# Créer la base de données PostgreSQL
createdb shabaka_adscreen

# Initialiser les tables (inclut Broadcast)
python init_db.py

# Optionnel : créer les données de démonstration
# (6 organisations, 9 écrans, 4 diffusions)
python init_db_demo.py
```

### 4. Créer les dossiers nécessaires

```bash
mkdir -p static/uploads/contents
mkdir -p static/uploads/fillers
mkdir -p static/uploads/internal
mkdir -p static/uploads/broadcasts
chmod -R 755 static/uploads
```

## Démarrage

### Mode développement

```bash
gunicorn --bind 0.0.0.0:5000 --reload main:app
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
  --reuse-port \
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

### Variables Replit auto-configurées

- `DATABASE_URL` - URL PostgreSQL
- `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`
- `REPLIT_DEV_DOMAIN` - Domaine de développement

## Nginx (Reverse Proxy)

Configuration recommandée pour Nginx :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    client_max_body_size 200M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /chemin/vers/shabaka-adscreen/static;
        expires 30d;
    }
}
```

## Maintenance

### Sauvegarde de la base de données

```bash
pg_dump -U user shabaka_adscreen > backup_$(date +%Y%m%d).sql
```

### Restauration

```bash
psql -U user shabaka_adscreen < backup_20231201.sql
```

### Mise à jour

```bash
git pull origin main
pip install -r requirements.txt
# Relancer l'application
```

### Réinitialisation des données de démo

```bash
# Supprimer et recréer les données de démonstration
python init_db_demo.py --force
```

## Monitoring

### Logs applicatifs

Les logs sont affichés sur la sortie standard. En production, redirigez-les vers un fichier :

```bash
gunicorn main:app 2>&1 | tee -a /var/log/shabaka-adscreen/app.log
```

### Points de vérification

- **Santé** : `GET /` doit retourner 200
- **Player** : `GET /player` doit afficher le formulaire de connexion
- **Admin** : `GET /admin` doit rediriger vers login
- **Base de données** : `python init_db.py --check`

### Métriques clés

- Uptime des écrans (heartbeat logs)
- Nombre de réservations par jour
- Revenus par devise (EUR, MAD, XOF, TND)
- Temps de validation des contenus
- Diffusions actives et écrans ciblés

## Troubleshooting

### Erreur de connexion à la base de données

Vérifiez que :
1. PostgreSQL est démarré
2. La variable `DATABASE_URL` est correcte
3. L'utilisateur a les droits sur la base

```bash
python init_db.py --check
```

### Erreur d'upload de fichiers

Vérifiez que :
1. Les dossiers `static/uploads/*` existent (contents, fillers, internal, broadcasts)
2. Les permissions sont correctes (755)
3. `MAX_CONTENT_LENGTH` est suffisant dans `app.py`

### Player écran ne se connecte pas

Vérifiez que :
1. Le code unique de l'écran est correct
2. Le mot de passe player est correct
3. L'écran est actif dans le dashboard

### Reçus ne s'affichent pas

Vérifiez que :
1. Pillow est installé (`pip install pillow`)
2. Les fonts sont disponibles (DejaVuSans)
3. La réservation existe en base

### Problèmes de devises

Vérifiez que :
1. L'organisation a une devise configurée (currency)
2. Le pays est défini (country)
3. Les symboles sont corrects dans `models/organization.py`

### Diffusions non affichées sur le player

Vérifiez que :
1. La diffusion est active (`is_active = True`)
2. Les dates de début/fin sont valides (ou nulles)
3. Le ciblage correspond à l'écran (pays, ville, établissement, écran)
4. Le player a rafraîchi sa playlist (toutes les 30 secondes)
5. Pour les diffusions programmées :
   - Le mode est 'scheduled' et la date/heure est passée
   - La récurrence est correctement configurée (type, intervalle, jours)
   - La priorité est suffisante pour apparaître dans la playlist

## Support

- **Documentation** : `/docs`
- **Email support** : support@shabaka-adscreen.com
- **WhatsApp admin** : Configurable dans les paramètres
