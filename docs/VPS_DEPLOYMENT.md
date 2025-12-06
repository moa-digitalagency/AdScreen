# VPS Deployment Guide for Shabaka AdScreen

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

### 4. Initialize the database
```bash
python init_db.py
```

This command will:
- Create all database tables
- Automatically add any missing columns to existing tables
- Display a summary of all tables

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
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/shabaka-adscreen
Environment="DATABASE_URL=postgresql://user:password@host:5432/database"
Environment="SESSION_SECRET=your-secret-key"
Environment="SUPERADMIN_EMAIL=admin@yourdomain.com"
Environment="SUPERADMIN_PASSWORD=your-password"
ExecStart=/path/to/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class gevent main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```bash
sudo systemctl enable shabaka
sudo systemctl start shabaka
```

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
