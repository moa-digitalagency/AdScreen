import json
import os
import logging
from flask import request, session, g

SUPPORTED_LANGUAGES = ['fr', 'en']
DEFAULT_LANGUAGE = 'fr'

_translations = {}

def load_translations():
    global _translations
    base_dir = os.path.dirname(os.path.dirname(__file__))
    lang_dir = os.path.join(base_dir, 'static', 'lang')
    
    # Ensure directory exists
    if not os.path.exists(lang_dir):
        try:
            os.makedirs(lang_dir)
            logging.info(f"Created language directory: {lang_dir}")
        except OSError as e:
            logging.error(f"Failed to create language directory {lang_dir}: {e}")
            return

    new_translations = {}
    for lang in SUPPORTED_LANGUAGES:
        lang_file = os.path.join(lang_dir, f'{lang}.json')
        if os.path.exists(lang_file):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    new_translations[lang] = json.load(f)
                logging.info(f"Loaded translations for {lang}")
            except Exception as e:
                logging.error(f"Error loading translations for {lang}: {e}")
                new_translations[lang] = {}
        else:
            logging.warning(f"Translation file not found: {lang_file}")
            new_translations[lang] = {}

    _translations = new_translations

def reload_translations():
    """Reloads translations from disk."""
    load_translations()

def get_locale():
    if 'lang' in session:
        return session['lang']
    
    browser_lang = request.accept_languages.best_match(SUPPORTED_LANGUAGES)
    return browser_lang if browser_lang else DEFAULT_LANGUAGE

def set_locale(lang):
    if lang in SUPPORTED_LANGUAGES:
        session['lang'] = lang
        return True
    return False

def translate(key, lang=None):
    if lang is None:
        lang = getattr(g, 'lang', DEFAULT_LANGUAGE)
    
    # Fallback to default language if requested language is not loaded/supported
    if lang not in _translations or not _translations[lang]:
        if lang != DEFAULT_LANGUAGE:
            return translate(key, DEFAULT_LANGUAGE)
    
    translations = _translations.get(lang, {})
    
    keys = key.split('.')
    value = translations
    
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
            if value is None:
                # Key not found in current lang, try default
                if lang != DEFAULT_LANGUAGE:
                    return translate(key, DEFAULT_LANGUAGE)
                return key
        else:
            # Structure mismatch
            return key
    
    return value if value is not None else key

def t(key, lang=None):
    return translate(key, lang)

def init_translations(app):
    load_translations()
    
    @app.before_request
    def before_request_set_lang():
        g.lang = get_locale()
    
    @app.context_processor
    def inject_translation_helpers():
        return {
            't': t,
            'current_lang': lambda: getattr(g, 'lang', DEFAULT_LANGUAGE),
            'supported_languages': SUPPORTED_LANGUAGES,
        }
