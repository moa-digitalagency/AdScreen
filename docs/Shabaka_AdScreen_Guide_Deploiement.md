# Shabaka AdScreen - Guide de Déploiement

Ce guide détaille les procédures pour installer, configurer et déployer la plateforme Shabaka AdScreen, que ce soit pour un environnement de développement local ou une production sur VPS.

## 1. Prérequis Système

*   **OS** : Linux (Ubuntu 22.04 LTS recommandé) ou macOS.
*   **Langage** : Python 3.11+.
*   **Base de Données** : PostgreSQL 14+ (SQLite supporté pour le dev).
*   **Outils** : `git`, `ffmpeg` (obligatoire pour le traitement vidéo/HLS), `pip`.
*   **Frontend** : Node.js & npm (uniquement pour recompiler le CSS Tailwind si modification).

## 2. Installation Locale (Développement)

Idéal pour tester ou contribuer au code.

### 2.1 Récupération du code
```bash
git clone <url-du-repo>
cd shabaka-adscreen
```

### 2.2 Environnement Virtuel
```bash
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2.3 Configuration
Créez un fichier `.env` à la racine (ou définissez les variables dans votre shell) :
```bash
# Utilisation de SQLite par défaut si DATABASE_URL n'est pas défini
export FLASK_ENV=development
export SESSION_SECRET="dev-secret-key"
export SUPERADMIN_EMAIL="admin@local.test"
export SUPERADMIN_PASSWORD="admin"
```

### 2.4 Initialisation BDD
```bash
# Crée les tables
python init_db.py

# (Optionnel) Peupler avec des fausses données de test
python init_db_demo.py
```

### 2.5 Lancement
```bash
python main.py
# Accès via http://localhost:5000
```

## 3. Installation Serveur (Production VPS)

Procédure pour un serveur Ubuntu/Debian vierge.

### 3.1 Préparation Système
Créez un utilisateur dédié pour la sécurité :
```bash
sudo adduser --system --group shabaka
sudo mkdir -p /opt/shabaka/adscreen
sudo chown shabaka:shabaka /opt/shabaka/adscreen
sudo apt update && sudo apt install -y python3-venv python3-dev libpq-dev ffmpeg nginx git
```

### 3.2 Installation de l'Application
```bash
# En tant que root ou sudo
cd /opt/shabaka/adscreen
# Cloner le code (remplacez par votre URL)
git clone <url-du-repo> .
chown -R shabaka:shabaka .

# Installation des dépendances
sudo -u shabaka python3 -m venv venv
sudo -u shabaka venv/bin/pip install -r requirements.txt
```

### 3.3 Variables d'Environnement
Créez le fichier `/opt/shabaka/adscreen/.env` :
```ini
DATABASE_URL=postgresql://user:password@localhost:5432/shabaka_prod
SESSION_SECRET=GENERATE_A_LONG_RANDOM_STRING
SUPERADMIN_EMAIL=admin@votredomaine.com
SUPERADMIN_PASSWORD=STRONG_PASSWORD
FLASK_ENV=production
```
Sécurisez le fichier :
```bash
chmod 600 /opt/shabaka/adscreen/.env
chown shabaka:shabaka /opt/shabaka/adscreen/.env
```

### 3.4 Service Systemd
Créez `/etc/systemd/system/shabaka.service` pour lancer Gunicorn automatiquement :

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
# Init DB avant lancement pour gérer les migrations
ExecStartPre=/opt/shabaka/adscreen/venv/bin/python init_db.py
# Lancement avec Gevent pour supporter les I/O longs (streaming)
ExecStart=/opt/shabaka/adscreen/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --worker-class gevent main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Activez le service :
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now shabaka
```

### 3.5 Configuration Nginx (Reverse Proxy)
Créez `/etc/nginx/sites-available/shabaka` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    # Taille max upload (Vidéos HD)
    client_max_body_size 200M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cache long pour les assets statiques
    location /static {
        alias /opt/shabaka/adscreen/static;
        expires 30d;
    }

    # Configuration spécifique pour le streaming HLS (buffer désactivé)
    location /player/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }
}
```

Activez le site et installez SSL avec Certbot :
```bash
sudo ln -s /etc/nginx/sites-available/shabaka /etc/nginx/sites-enabled/
sudo apt install python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
sudo systemctl reload nginx
```

## 4. Maintenance

### Mise à jour
```bash
cd /opt/shabaka/adscreen
sudo -u shabaka git pull
sudo -u shabaka venv/bin/pip install -r requirements.txt
sudo systemctl restart shabaka
```
*Note : Le script `init_db.py` exécuté au démarrage gère automatiquement l'ajout de nouvelles colonnes si le schéma change.*

### Logs
*   **Application** : `journalctl -u shabaka -f`
*   **Nginx Access** : `tail -f /var/log/nginx/access.log`
*   **Nginx Error** : `tail -f /var/log/nginx/error.log`

## 5. Dépannage Courant

*   **Erreur 502 Bad Gateway** : Gunicorn n'est pas lancé. Vérifiez `sudo systemctl status shabaka`.
*   **Erreur Upload** : Vérifiez que `client_max_body_size` est assez grand dans Nginx et que les dossiers `static/uploads` appartiennent bien à l'utilisateur `shabaka`.
*   **Pas de vidéo / streaming** : Vérifiez que `ffmpeg` est installé (`which ffmpeg`).
