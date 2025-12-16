# Déploiement sur VPS

Ce guide détaille l'installation de Shabaka AdScreen sur un serveur privé virtuel (VPS) avec Linux.

## Démarrage rapide

```bash
# 1. Récupérer et préparer
git clone <url-du-dépôt>
cd shabaka-adscreen
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configurer l'environnement
export DATABASE_URL="postgresql://user:password@localhost:5432/shabaka"
export SESSION_SECRET="$(openssl rand -hex 32)"
export SUPERADMIN_EMAIL="admin@votre-domaine.com"
export SUPERADMIN_PASSWORD="mot-de-passe-securise"

# 3. Initialiser la base (avant le premier démarrage)
python init_db.py

# 4. Démarrer
gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class gevent main:app
```

## Installation détaillée

### Préparer l'environnement

Créez un utilisateur dédié :

```bash
sudo adduser --system --group shabaka
sudo mkdir -p /opt/shabaka
sudo chown shabaka:shabaka /opt/shabaka
```

Clonez le projet :

```bash
sudo -u shabaka git clone <url-du-dépôt> /opt/shabaka/adscreen
cd /opt/shabaka/adscreen
```

Créez l'environnement virtuel Python :

```bash
sudo -u shabaka python3.11 -m venv venv
sudo -u shabaka venv/bin/pip install -r requirements.txt
```

### Configurer les variables d'environnement

Créez un fichier `/opt/shabaka/adscreen/.env` :

```bash
DATABASE_URL=postgresql://shabaka:motdepasse@localhost:5432/shabaka_adscreen
SESSION_SECRET=votre-cle-secrete-longue-et-aleatoire
SUPERADMIN_EMAIL=admin@votre-domaine.com
SUPERADMIN_PASSWORD=mot-de-passe-securise
```

Protégez ce fichier :

```bash
chmod 600 /opt/shabaka/adscreen/.env
chown shabaka:shabaka /opt/shabaka/adscreen/.env
```

### Initialiser la base de données

```bash
sudo -u shabaka /opt/shabaka/adscreen/venv/bin/python init_db.py
```

Ce script :
- Crée toutes les tables
- Ajoute automatiquement les colonnes manquantes si vous mettez à jour
- Affiche un résumé des tables créées

Options utiles :
```bash
python init_db.py --check  # Vérifie la connexion uniquement
python init_db.py --drop   # Réinitialise la base (perte de données)
```

## Configuration systemd

Créez `/etc/systemd/system/shabaka.service` :

```ini
[Unit]
Description=Shabaka AdScreen
After=network.target postgresql.service

[Service]
Type=simple
User=shabaka
Group=shabaka
WorkingDirectory=/opt/shabaka/adscreen
EnvironmentFile=/opt/shabaka/adscreen/.env
ExecStartPre=/opt/shabaka/adscreen/venv/bin/python init_db.py
ExecStart=/opt/shabaka/adscreen/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class gevent main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Activez et démarrez le service :

```bash
sudo systemctl daemon-reload
sudo systemctl enable shabaka
sudo systemctl start shabaka
```

La ligne `ExecStartPre` exécute `init_db.py` avant chaque démarrage pour maintenir le schéma à jour.

## Configuration Nginx

Créez `/etc/nginx/sites-available/shabaka` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    # Redirection HTTPS (recommandé)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com;

    # Certificats SSL (Let's Encrypt recommandé)
    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;

    # Taille max des uploads
    client_max_body_size 200M;

    # Application principale
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Fichiers statiques (cache long)
    location /static {
        alias /opt/shabaka/adscreen/static;
        expires 30d;
    }

    # Configuration streaming
    location /player/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }

    # Service Worker pour le mode hors ligne
    location /static/js/player-sw.js {
        add_header Cache-Control "no-cache";
        add_header Service-Worker-Allowed "/player/";
        proxy_pass http://127.0.0.1:5000;
    }
}
```

Activez la configuration :

```bash
sudo ln -s /etc/nginx/sites-available/shabaka /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Certificat SSL avec Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
```

Certbot configure automatiquement Nginx et renouvelle le certificat.

## Mise à jour du schéma

Quand vous mettez à jour le code et qu'il y a de nouvelles colonnes en base :

```bash
sudo -u shabaka /opt/shabaka/adscreen/venv/bin/python init_db.py
sudo systemctl restart shabaka
```

Le script `init_db.py` détecte et ajoute les colonnes manquantes sans perdre les données existantes.

## Notes sur le streaming IPTV

La plateforme inclut le streaming adaptatif pour la fonctionnalité OnlineTV.

### Fonctionnement

- La qualité vidéo s'adapte automatiquement à la bande passante
- Les buffers sont optimisés pour éviter les coupures
- La qualité remonte progressivement après une dégradation réseau

### Points d'attention

**CDN externe** : HLS.js est chargé depuis jsDelivr. Votre VPS doit avoir accès à Internet.

**Bande passante** : Les flux MPEG-TS passent par un proxy serveur. Préférez les flux HLS natifs quand c'est possible.

**Logs** : Par défaut, le logging est en mode DEBUG. En production, changez dans `app.py` :

```python
# Avant
logging.basicConfig(level=logging.DEBUG)

# Après
logging.basicConfig(level=logging.WARNING)
```

## Dépannage

### Erreurs "column does not exist"

Le schéma n'est pas à jour. Exécutez :

```bash
sudo -u shabaka /opt/shabaka/adscreen/venv/bin/python init_db.py
```

### Fichiers statiques non chargés

Vérifiez les permissions :

```bash
sudo chown -R shabaka:shabaka /opt/shabaka/adscreen/static
sudo chmod -R 755 /opt/shabaka/adscreen/static
```

### Erreurs de permission

Vérifiez que l'utilisateur `shabaka` a accès aux dossiers :

```bash
sudo -u shabaka ls -la /opt/shabaka/adscreen/static/uploads/
```

### Connexion base de données refusée

Vérifiez PostgreSQL :

```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT 1;"
```

Vérifiez les droits :

```bash
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE shabaka_adscreen TO shabaka;"
```

## Sécurité

### Pare-feu

Ouvrez uniquement les ports nécessaires :

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Mises à jour système

```bash
sudo apt update && sudo apt upgrade -y
```

### Sauvegardes

Automatisez les sauvegardes de la base :

```bash
# Dans /etc/cron.daily/shabaka-backup
#!/bin/bash
pg_dump -U shabaka shabaka_adscreen | gzip > /backup/shabaka_$(date +%Y%m%d).sql.gz
find /backup -name "shabaka_*.sql.gz" -mtime +30 -delete
```

## Ressources recommandées

| VPS type | vCPU | RAM | Usage |
|----------|------|-----|-------|
| Petit réseau (<10 écrans) | 1 | 1 Go | Tests, démo |
| Réseau moyen (10-50 écrans) | 2 | 2 Go | Production standard |
| Grand réseau (50+ écrans) | 4 | 4 Go | Production intensive |

Le stockage dépend du volume de contenus uploadés. Comptez 1 Go de base + volume des fichiers média.
