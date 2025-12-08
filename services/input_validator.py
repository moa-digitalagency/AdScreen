import re
from email_validator import validate_email, EmailNotValidError
from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def sanitize_string(value: str, max_length: int = 255, allow_html: bool = False) -> str:
    if value is None:
        return None
    
    value = str(value).strip()
    
    if not allow_html:
        value = re.sub(r'<[^>]+>', '', value)
    
    value = value.replace('\x00', '')
    
    if len(value) > max_length:
        value = value[:max_length]
    
    return value


def validate_email_address(email: str) -> str:
    if not email:
        raise ValidationError("email", "Email is required")
    
    try:
        valid = validate_email(email, check_deliverability=False)
        return valid.normalized
    except EmailNotValidError as e:
        raise ValidationError("email", str(e))


def validate_phone(phone: str) -> str:
    if not phone:
        return None
    
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    if not re.match(r'^\+?[\d]{8,15}$', cleaned):
        raise ValidationError("phone", "Invalid phone number format")
    
    return cleaned


def validate_positive_integer(value, field_name: str, min_val: int = 0, max_val: int = None) -> int:
    try:
        num = int(value)
        if num < min_val:
            raise ValidationError(field_name, f"Must be at least {min_val}")
        if max_val is not None and num > max_val:
            raise ValidationError(field_name, f"Must not exceed {max_val}")
        return num
    except (ValueError, TypeError):
        raise ValidationError(field_name, "Must be a valid integer")


def validate_date_string(date_str: str, field_name: str = "date") -> str:
    if not date_str:
        return None
    
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        raise ValidationError(field_name, "Date must be in YYYY-MM-DD format")
    
    parts = date_str.split('-')
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    
    if not (1 <= month <= 12):
        raise ValidationError(field_name, "Invalid month")
    if not (1 <= day <= 31):
        raise ValidationError(field_name, "Invalid day")
    if year < 2000 or year > 2100:
        raise ValidationError(field_name, "Year out of valid range")
    
    return date_str


def validate_content_type(content_type: str) -> str:
    valid_types = ['image', 'video']
    if content_type not in valid_types:
        raise ValidationError("content_type", f"Must be one of: {', '.join(valid_types)}")
    return content_type


def validate_screen_code(code: str) -> str:
    if not code:
        raise ValidationError("screen_code", "Screen code is required")
    
    code = sanitize_string(code, max_length=50)
    
    if not re.match(r'^[A-Za-z0-9\-_]+$', code):
        raise ValidationError("screen_code", "Invalid screen code format")
    
    return code


def validate_url(url: str, field_name: str = "url") -> str:
    if not url:
        return None
    
    if not url.startswith(('http://', 'https://')):
        raise ValidationError(field_name, "URL must start with http:// or https://")
    
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        raise ValidationError(field_name, "Invalid URL format")
    
    return url


def validate_json_request(*required_fields):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    "error": "Request must be JSON",
                    "code": "INVALID_CONTENT_TYPE"
                }), 400
            
            data = request.get_json()
            
            if data is None:
                return jsonify({
                    "error": "Invalid JSON body",
                    "code": "INVALID_JSON"
                }), 400
            
            missing = [field for field in required_fields if field not in data or data[field] is None]
            
            if missing:
                return jsonify({
                    "error": f"Missing required fields: {', '.join(missing)}",
                    "code": "MISSING_FIELDS",
                    "fields": missing
                }), 400
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def handle_validation_errors(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.field} - {e.message}")
            return jsonify({
                "error": e.message,
                "code": "VALIDATION_ERROR",
                "field": e.field
            }), 400
    return decorated
