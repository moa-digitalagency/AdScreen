"""
 * Nom de l'application : Shabaka AdScreen
 * Description : Main application entry point and configuration (Security Audited)
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""
import os
import logging
import secrets

from flask import Flask, request, session, abort, redirect, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    # In production, this should ideally raise an error or be strictly enforced.
    # For dev/audit, we generate a random key if missing to prevent crash/insecurity.
    if os.environ.get('FLASK_ENV') == 'production':
        logging.warning("SESSION_SECRET is missing in production! Using random key (sessions will invalidate on restart).")
    app.secret_key = secrets.token_hex(32)

# Secure Session Configuration
app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production', # Only true if behind https/prod usually, but let's be safe
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = "static/uploads"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

INIT_DB_MODE = os.environ.get('INIT_DB_MODE', 'false').lower() == 'true'

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    if app.config.get('SESSION_COOKIE_SECURE'):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

with app.app_context():
    import models
    db.create_all()
    
    if not INIT_DB_MODE:
        superadmin_email = os.environ.get("SUPERADMIN_EMAIL")
        superadmin_password = os.environ.get("SUPERADMIN_PASSWORD")
        
        if superadmin_email and superadmin_password:
            existing_superadmin = models.User.query.filter_by(email=superadmin_email).first()
            if not existing_superadmin:
                superadmin = models.User(
                    username='superadmin',
                    email=superadmin_email,
                    role='superadmin',
                    is_active=True
                )
                superadmin.set_password(superadmin_password)
                db.session.add(superadmin)
                db.session.commit()
                logging.info(f"Superadmin user created with email: {superadmin_email}")
            else:
                updated = False
                if existing_superadmin.role != 'superadmin':
                    existing_superadmin.role = 'superadmin'
                    updated = True
                    logging.info(f"Updated user {superadmin_email} to superadmin role")
                
                if not existing_superadmin.check_password(superadmin_password):
                    existing_superadmin.set_password(superadmin_password)
                    updated = True
                    logging.info(f"Updated superadmin password for {superadmin_email}")
                
                if updated:
                    db.session.commit()
        
        from routes.auth_routes import auth_bp
        from routes.admin_routes import admin_bp
        from routes.org_routes import org_bp
        from routes.screen_routes import screen_bp
        from routes.booking_routes import booking_bp
        from routes.player_routes import player_bp
        from routes.api_routes import api_bp
        from routes.billing_routes import billing_bp
        from routes.ad_content_routes import ad_content_bp
        from routes.mobile_api_routes import mobile_api_bp
        
        from services.rate_limiter import init_limiter
        init_limiter(app)
        
        from services.translation_service import init_translations, set_locale, SUPPORTED_LANGUAGES
        init_translations(app)
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp, url_prefix="/admin")
        app.register_blueprint(org_bp, url_prefix="/org")
        app.register_blueprint(screen_bp, url_prefix="/screen")
        app.register_blueprint(booking_bp, url_prefix="/book")
        app.register_blueprint(player_bp, url_prefix="/player")
        app.register_blueprint(api_bp, url_prefix="/api")
        app.register_blueprint(billing_bp, url_prefix="/org/billing")
        app.register_blueprint(ad_content_bp, url_prefix="/admin")
        app.register_blueprint(mobile_api_bp, url_prefix="/mobile/api/v1")

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))


@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.now}


@app.context_processor
def inject_csrf_token():
    def csrf_token():
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(32)
        return session['_csrf_token']
    
    return {'csrf_token': csrf_token}


CSRF_EXEMPT_ENDPOINTS = [
    'player.heartbeat',
    'player.log_play',
    'player.stream_proxy',
    'player.stop_tv_stream',
    'player.change_channel',
    'api.screen_heartbeat',
    'api.screen_status',
    'api.screen_playlist',
    'api.screen_analytics',
    'billing.cron_generate_invoices',
]

CSRF_EXEMPT_PREFIXES = [
    'api.',
    'mobile_api.',
]

@app.before_request
def validate_csrf_token():
    if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        if request.endpoint and request.endpoint in CSRF_EXEMPT_ENDPOINTS:
            return
        
        if request.endpoint:
            for prefix in CSRF_EXEMPT_PREFIXES:
                if request.endpoint.startswith(prefix):
                    return
        
        token_from_form = request.form.get('csrf_token')
        token_from_header = request.headers.get('X-CSRF-Token')
        submitted_token = token_from_form or token_from_header
        
        session_token = session.get('_csrf_token')
        
        if not submitted_token or not session_token:
            logging.warning(f"CSRF token missing for {request.endpoint}")
            abort(400, description="CSRF token missing. Please refresh the page and try again.")
        
        if not secrets.compare_digest(submitted_token, session_token):
            logging.warning(f"CSRF token mismatch for {request.endpoint}")
            abort(400, description="CSRF token invalid. Please refresh the page and try again.")


@app.context_processor
def inject_currency():
    from flask_login import current_user
    from utils.currencies import get_currency_by_code
    
    currency_symbol = '€'
    try:
        if current_user and current_user.is_authenticated:
            org = getattr(current_user, 'organization', None)
            if org:
                org_currency = getattr(org, 'currency', None) or 'EUR'
                currency_info = get_currency_by_code(org_currency)
                currency_symbol = currency_info.get('symbol', org_currency)
    except Exception:
        pass
    
    return {'currency_symbol': currency_symbol}


@app.context_processor
def inject_site_settings():
    from models import SiteSetting
    # Preload all settings to avoid N+1 queries
    SiteSetting.preload_cache()
    return {
        'site_settings': {
            'platform_name': SiteSetting.get('platform_name', 'Shabaka AdScreen'),
            'site_description': SiteSetting.get('site_description', ''),
            'support_email': SiteSetting.get('support_email', ''),
            'admin_whatsapp_number': SiteSetting.get('admin_whatsapp_number', ''),
            'facebook_url': SiteSetting.get('facebook_url', ''),
            'instagram_url': SiteSetting.get('instagram_url', ''),
            'twitter_url': SiteSetting.get('twitter_url', ''),
            'linkedin_url': SiteSetting.get('linkedin_url', ''),
            'youtube_url': SiteSetting.get('youtube_url', ''),
            'contact_phone': SiteSetting.get('contact_phone', ''),
            'contact_address': SiteSetting.get('contact_address', ''),
            'head_code': SiteSetting.get('head_code', ''),
            'og_image': SiteSetting.get('og_image', ''),
            'favicon': SiteSetting.get('favicon', ''),
            'default_currency': SiteSetting.get('default_currency', 'EUR'),
            'copyright_text': SiteSetting.get('copyright_text', '© Shabaka AdScreen. Tous droits réservés.'),
            'made_with_text': SiteSetting.get('made_with_text', 'Fait avec ❤️ en France'),
        }
    }


@app.route('/set-language/<lang>')
def set_language(lang):
    from services.translation_service import set_locale, SUPPORTED_LANGUAGES
    if lang in SUPPORTED_LANGUAGES:
        set_locale(lang)
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect('/')
