import json
import os
from flask import request, session, g

SUPPORTED_LANGUAGES = ['fr', 'en']
DEFAULT_LANGUAGE = 'fr'

_translations = {}

def load_translations():
    global _translations
    lang_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'lang')
    
    for lang in SUPPORTED_LANGUAGES:
        lang_file = os.path.join(lang_dir, f'{lang}.json')
        if os.path.exists(lang_file):
            with open(lang_file, 'r', encoding='utf-8') as f:
                _translations[lang] = json.load(f)

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
    
    if lang not in _translations:
        lang = DEFAULT_LANGUAGE
    
    translations = _translations.get(lang, {})
    
    keys = key.split('.')
    value = translations
    
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
            if value is None:
                if lang != DEFAULT_LANGUAGE:
                    return translate(key, DEFAULT_LANGUAGE)
                return key
        else:
            return key
    
    return value if value else key

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
