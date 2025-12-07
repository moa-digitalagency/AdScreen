# VPS Deployment Guide for Shabaka AdScreen

## Quick Start

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd shabaka-adscreen
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
export DATABASE_URL="postgresql://user:password@host:5432/database_name"
export SESSION_SECRET="$(openssl rand -hex 32)"
export SUPERADMIN_EMAIL="admin@yourdomain.com"
export SUPERADMIN_PASSWORD="your-secure-password"

# 3. Initialize database (run this FIRST, before starting the app)
python init_db.py

# 4. Start application
gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class gevent main:app
```

## Required Environment Variables

Set these environment variables on your VPS before running the application:

```bash
# Required
export DATABASE_URL="postgresql://user:password@host:5432/database_name"
export SESSION_SECRET="your-secure-random-secret-key-here"

# Recommended (for superadmin access)
export SUPERADMIN_EMAIL="admin@yourdomain.com"
export SUPERADMIN_PASSWORD="your-secure-password"

# Optional (for cron jobs)
export CRON_SECRET="your-cron-secret"
```

## Installation Steps

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd shabaka-adscreen
```

### 2. Create virtual environment
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize the database (IMPORTANT: Run before starting the app)
```bash
python init_db.py
```

This command will:
- Create all database tables
- Automatically add any missing columns to existing tables
- Display a summary of all tables
- Skip superadmin creation and blueprint registration (handled by app on startup)

**Options:**
```bash
python init_db.py --check  # Verify database connection only
python init_db.py --drop   # Reset database (WARNING: all data will be lost)
```

### 5. Run the application

**Development:**
```bash
python main.py
```

**Production (recommended):**
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class gevent main:app
```

## Using with systemd (Production)

Create a service file `/etc/systemd/system/shabaka.service`:

```ini
[Unit]
Description=Shabaka AdScreen
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/shabaka-adscreen
EnvironmentFile=/path/to/shabaka-adscreen/.env
ExecStartPre=/path/to/venv/bin/python init_db.py
ExecStart=/path/to/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class gevent main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Create the environment file `/path/to/shabaka-adscreen/.env`:
```bash
DATABASE_URL=postgresql://user:password@host:5432/database
SESSION_SECRET=your-secret-key
SUPERADMIN_EMAIL=admin@yourdomain.com
SUPERADMIN_PASSWORD=your-password
```

Then enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable shabaka
sudo systemctl start shabaka
```

**Notes:**
- The `ExecStartPre` directive runs `init_db.py` before each start to ensure database schema is up-to-date.
- `init_db.py` sets `INIT_DB_MODE=true` internally to skip superadmin creation and blueprint registration (these run when the main app starts).
- Do NOT add `INIT_DB_MODE=true` to your environment file, as this would prevent the app from starting properly.

## Using with Nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/shabaka-adscreen/static;
        expires 30d;
    }

    client_max_body_size 100M;
}
```

## Database Schema Updates

When you update the code and there are new database columns, simply run:

```bash
python init_db.py
```

This will automatically detect and add any missing columns without losing existing data.

## Troubleshooting

### "column does not exist" errors
Run `python init_db.py` to sync the database schema.

### Static files not loading
Ensure the `static/uploads` folder exists and has write permissions:
```bash
mkdir -p static/uploads
chmod 755 static/uploads
```

### Permission errors
Make sure the application user has write access to:
- `static/uploads/`
- Any log directories

### Database connection issues
Verify your DATABASE_URL is correct and the PostgreSQL server is accessible.

## IPTV/OnlineTV Streaming Notes

The platform includes adaptive bitrate streaming for IPTV/OnlineTV functionality:

### Features
- **Adaptive Quality**: Video quality automatically adjusts based on connection speed
- **Buffer Management**: Smart buffering prevents stalls during bandwidth fluctuations
- **Quality Recovery**: After network issues, quality gradually improves over time

### VPS Considerations
1. **CDN Assets**: HLS.js is loaded from CDN (`jsdelivr.net`). Ensure your VPS has internet access.
2. **Proxy Streaming**: MPEG-TS streams are converted to HLS via server proxy. This uses server bandwidth.
3. **Logging**: Debug logging is enabled by default. For production, consider reducing log verbosity.

### Nginx Configuration for Streaming
Add these settings for better streaming performance:

```nginx
# Inside the server block
proxy_buffering off;
proxy_read_timeout 300s;
proxy_connect_timeout 75s;
proxy_send_timeout 300s;

# For websocket support (if needed)
location /player/ {
    proxy_pass http://127.0.0.1:5000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# Service Worker for offline caching (player)
location /static/js/player-sw.js {
    add_header Cache-Control "no-cache";
    add_header Service-Worker-Allowed "/player/";
    proxy_pass http://127.0.0.1:5000;
}
```

### Reducing Log Verbosity
In `app.py`, change the logging level for production:
```python
# Change this line:
logging.basicConfig(level=logging.DEBUG)
# To:
logging.basicConfig(level=logging.WARNING)
```
