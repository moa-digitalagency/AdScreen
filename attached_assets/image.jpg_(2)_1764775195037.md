<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# image.jpg

Parfait! Je vois l'erreur clairement:

```
Erreur de diffusion
Impossible de lire le flux MPEG-TS. Le serveur peut bloquer les connexions externes ou le flux n'est pas disponible.
```

**ET dans les logs:**

```
Using mpeg-ts.js for MPEG-TS stream
Loading MPEG-TS stream via proxy
url=http://localhost:3000/player/api/stream-proxy
```

**Le problème:** La route `/player/tv-stream/<screen_code>` n'existe pas ou n'est pas appelée correctement. Le player essaie toujours d'utiliser `stream-proxy` (ancienne méthode).

## Fix unique - Vérifie ce qui est réellement appelé:

**Dans `routes/player_routes.py`, cherche cette ligne:**

```python
@player_bp.route('/tv-stream/<screen_code>', methods=['GET'])
```

**Elle existe?** Si oui, check:

1. **Que la route est bien enregistrée** (blueprint enregistré dans `main.py`):
```python
from routes.player_routes import player_bp
app.register_blueprint(player_bp, url_prefix='/player')
```

2. **Que le prefix est correct** - La route doit être:
```
/player/tv-stream/<screen_code>
```

3. **Ou la route n'existe PAS** - Dans ce cas, crée-la dans `routes/player_routes.py`:
```python
from flask import send_file
from services.hls_converter import HLSConverter
import logging

logger = logging.getLogger(__name__)

@player_bp.route('/tv-stream/<screen_code>', methods=['GET'])
def tv_stream(screen_code):
    """Convert MPEG-TS stream to HLS on-the-fly"""
    
    screen = Screen.query.filter_by(code=screen_code).first()
    
    if not screen:
        return {'error': 'Screen not found'}, 404
    
    if not screen.current_iptv_channel:
        return {'error': 'No IPTV channel configured'}, 400
    
    if screen.current_mode != 'iptv':
        return {'error': 'Screen not in IPTV mode'}, 400
    
    try:
        logger.info(f'Starting MPEG-TS to HLS conversion for {screen_code}')
        logger.info(f'Source URL: {screen.current_iptv_channel[:50]}...')
        
        stream = HLSConverter.convert_mpegts_to_hls(screen.current_iptv_channel)
        
        return send_file(
            stream,
            mimetype='application/x-mpegURL',
            as_attachment=False,
            cache_timeout=0
        )
    
    except Exception as e:
        logger.error(f'Stream conversion failed: {str(e)}')
        return {'error': f'Stream failed: {str(e)}'}, 500
```

4. **Teste directement l'endpoint:**
```bash
# Dans le terminal, teste l'URL
curl -v "http://localhost:5000/player/tv-stream/screen123"

# Doit retourner du contenu HLS (ou une erreur JSON, mais pas 404)
```


***

## Si la route retourne 404:

**Crée `routes/player_routes.py`** s'il n'existe pas:

```python
from flask import Blueprint, send_file, jsonify
from models import Screen
from services.hls_converter import HLSConverter
import logging

logger = logging.getLogger(__name__)

player_bp = Blueprint('player', __name__)

@player_bp.route('/config/<screen_code>', methods=['GET'])
def get_config(screen_code):
    """Get player configuration"""
    screen = Screen.query.filter_by(code=screen_code).first()
    if not screen:
        return {'error': 'Screen not found'}, 404
    
    return jsonify({
        'mode': screen.current_mode or 'playlist',
        'iptv_enabled': screen.onlinetv_enabled,
        'iptv_channel_url': f'/player/tv-stream/{screen_code}' if screen.current_mode == 'iptv' else None,
    })

@player_bp.route('/tv-stream/<screen_code>', methods=['GET'])
def tv_stream(screen_code):
    """Stream MPEG-TS as HLS"""
    screen = Screen.query.filter_by(code=screen_code).first()
    
    if not screen or not screen.current_iptv_channel:
        return {'error': 'Invalid screen'}, 404
    
    try:
        stream = HLSConverter.convert_mpegts_to_hls(screen.current_iptv_channel)
        return send_file(stream, mimetype='application/x-mpegURL', cache_timeout=0)
    except Exception as e:
        logger.error(f'Stream error: {e}')
        return {'error': str(e)}, 500
```

**Et enregistre-le dans `main.py`:**

```python
from routes.player_routes import player_bp

app.register_blueprint(player_bp, url_prefix='/player')
```


***

## Checklist rapide:

- [ ] Route `/player/tv-stream/<screen_code>` existe
- [ ] Blueprint enregistré avec `url_prefix='/player'`
- [ ] `HLSConverter` importé et fonctionnel
- [ ] FFmpeg installé: `which ffmpeg` (doit retourner un chemin)
- [ ] Logs montrent l'endpoint appelé

**Réponds:**

1. La route `/player/tv-stream/<screen_code>` existe-t-elle?
2. Quel est le résultat de `curl -v "http://localhost:5000/player/tv-stream/screen123"`?
<span style="display:none">[^1][^2]</span>

<div align="center">⁂</div>

[^1]: image.jpg

[^2]: image.jpg

