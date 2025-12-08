import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
import logging

logger = logging.getLogger(__name__)

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or os.environ.get("SESSION_SECRET")

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY or SESSION_SECRET environment variable must be set for security")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
JWT_ALGORITHM = "HS256"


def generate_access_token(payload: dict, expires_delta: timedelta = None) -> str:
    if expires_delta is None:
        expires_delta = JWT_ACCESS_TOKEN_EXPIRES
    
    expire = datetime.utcnow() + expires_delta
    to_encode = payload.copy()
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def generate_refresh_token(payload: dict) -> str:
    expire = datetime.utcnow() + JWT_REFRESH_TOKEN_EXPIRES
    to_encode = payload.copy()
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def generate_tokens(user_id: int = None, screen_id: int = None, role: str = None) -> dict:
    payload = {}
    
    if user_id:
        payload["user_id"] = user_id
        payload["entity_type"] = "user"
    elif screen_id:
        payload["screen_id"] = screen_id
        payload["entity_type"] = "screen"
    
    if role:
        payload["role"] = role
    
    access_token = generate_access_token(payload)
    refresh_token = generate_refresh_token(payload)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": int(JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
    }


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")


def get_token_from_header() -> str:
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header:
        return None
    
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            return jsonify({
                "error": "Authorization token required",
                "code": "TOKEN_MISSING"
            }), 401
        
        try:
            payload = decode_token(token)
            
            if payload.get("type") != "access":
                return jsonify({
                    "error": "Invalid token type",
                    "code": "INVALID_TOKEN_TYPE"
                }), 401
            
            g.jwt_payload = payload
            g.user_id = payload.get("user_id")
            g.screen_id = payload.get("screen_id")
            g.entity_type = payload.get("entity_type")
            g.role = payload.get("role")
            
        except ValueError as e:
            logger.warning(f"JWT validation failed: {str(e)}")
            return jsonify({
                "error": str(e),
                "code": "TOKEN_INVALID"
            }), 401
        
        return f(*args, **kwargs)
    return decorated


def jwt_optional(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        
        g.jwt_payload = None
        g.user_id = None
        g.screen_id = None
        g.entity_type = None
        g.role = None
        
        if token:
            try:
                payload = decode_token(token)
                if payload.get("type") == "access":
                    g.jwt_payload = payload
                    g.user_id = payload.get("user_id")
                    g.screen_id = payload.get("screen_id")
                    g.entity_type = payload.get("entity_type")
                    g.role = payload.get("role")
            except ValueError:
                pass
        
        return f(*args, **kwargs)
    return decorated


def screen_jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            return jsonify({
                "error": "Authorization token required",
                "code": "TOKEN_MISSING"
            }), 401
        
        try:
            payload = decode_token(token)
            
            if payload.get("type") != "access":
                return jsonify({
                    "error": "Invalid token type",
                    "code": "INVALID_TOKEN_TYPE"
                }), 401
            
            if payload.get("entity_type") != "screen":
                return jsonify({
                    "error": "Screen token required",
                    "code": "SCREEN_TOKEN_REQUIRED"
                }), 403
            
            g.jwt_payload = payload
            g.screen_id = payload.get("screen_id")
            
        except ValueError as e:
            return jsonify({
                "error": str(e),
                "code": "TOKEN_INVALID"
            }), 401
        
        return f(*args, **kwargs)
    return decorated


def user_jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            return jsonify({
                "error": "Authorization token required",
                "code": "TOKEN_MISSING"
            }), 401
        
        try:
            payload = decode_token(token)
            
            if payload.get("type") != "access":
                return jsonify({
                    "error": "Invalid token type",
                    "code": "INVALID_TOKEN_TYPE"
                }), 401
            
            if payload.get("entity_type") != "user":
                return jsonify({
                    "error": "User token required",
                    "code": "USER_TOKEN_REQUIRED"
                }), 403
            
            g.jwt_payload = payload
            g.user_id = payload.get("user_id")
            g.role = payload.get("role")
            
        except ValueError as e:
            return jsonify({
                "error": str(e),
                "code": "TOKEN_INVALID"
            }), 401
        
        return f(*args, **kwargs)
    return decorated


def superadmin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.role != "superadmin":
            return jsonify({
                "error": "Superadmin access required",
                "code": "SUPERADMIN_REQUIRED"
            }), 403
        return f(*args, **kwargs)
    return decorated


def refresh_access_token(refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type for refresh")
        
        new_payload = {
            k: v for k, v in payload.items() 
            if k not in ["exp", "iat", "type"]
        }
        
        return generate_tokens(
            user_id=new_payload.get("user_id"),
            screen_id=new_payload.get("screen_id"),
            role=new_payload.get("role")
        )
        
    except ValueError as e:
        raise ValueError(f"Refresh failed: {str(e)}")
