from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import request
import logging

logger = logging.getLogger(__name__)


def get_client_ip():
    """Get real client IP, handling proxy headers safely."""
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
        return client_ip
    return get_remote_address()


limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)


RATE_LIMITS = {
    "auth": {
        "login": "5 per minute",
        "register": "3 per minute",
        "refresh": "10 per minute"
    },
    "api": {
        "default": "100 per minute",
        "read": "200 per minute",
        "write": "30 per minute"
    },
    "player": {
        "heartbeat": "120 per minute",
        "playlist": "60 per minute",
        "log_play": "120 per minute"
    },
    "public": {
        "default": "30 per minute"
    }
}


def get_rate_limit(category: str, action: str = "default") -> str:
    if category in RATE_LIMITS:
        if action in RATE_LIMITS[category]:
            return RATE_LIMITS[category][action]
        if "default" in RATE_LIMITS[category]:
            return RATE_LIMITS[category]["default"]
    return "100 per minute"


def init_limiter(app):
    limiter.init_app(app)
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {
            "error": "Too many requests. Please slow down.",
            "code": "RATE_LIMIT_EXCEEDED",
            "retry_after": e.description
        }, 429
    
    logger.info("Rate limiter initialized")
    return limiter
