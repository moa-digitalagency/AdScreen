<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Lien bien le code compet de mon repo [https://github.com/moa-digitalagency/AdScreen](https://github.com/moa-digitalagency/AdScreen) et aussi voici le type de lien que je fourni [http://rahali44.xyz/get.php?username=056C940\&password=KV41346\&type=m3u_plus\&output=mpegts](http://rahali44.xyz/get.php?username=056C940&password=KV41346&type=m3u_plus&output=mpegts) et adape une reponse et suggestion a donné a mon outils videcoding pour corriger ce probleme

Parfait, je comprends le problème maintenant. **L'URL que tu fournis retourne du MPEG-TS (`output=mpegts`)** et hls.js ne supporte **pas directement** le MPEG-TS pur. C'est pour ça que tu as l'erreur:

```
MPEG-TS error: NetworkError
```


## Diagnostic du problème

| Problème | Raison |
| :-- | :-- |
| URL retourne `mpegts` | Format conteneur transport stream, pas HLS (.m3u8) |
| hls.js ne peut pas parser ça | hls.js attend du HLS/M3U8 avec segments `.ts` |
| Le player essaie de play() trop tôt | Timing race condition + format incompatible = crash |
| L'erreur `pause()` | Le lecteur démarre → erreur → tente de pause → erreur en cascade |

## Solution pour AdScreen

Tu as **2 options**:

### Option 1: Demander le format HLS au serveur (Recommandé ⭐)

Modifie ton URL pour demander du HLS au lieu de MPEG-TS:

```python
# Dans AdScreen, routes/player.py ou services/playlist_service.py

def get_iptv_playlist_url(username, password, screen):
    """
    Récupère une playlist M3U/HLS depuis un serveur IPTV externe
    """
    # ❌ MAUVAIS - retourne du MPEG-TS brut
    # url = f"http://rahali44.xyz/get.php?username={username}&password={password}&type=m3u_plus&output=mpegts"
    
    # ✅ BON - demande du HLS/M3U8
    url = f"http://rahali44.xyz/get.php?username={username}&password={password}&type=m3u_plus&output=m3u8"
    
    # Ou essayer d'autres formats:
    # &output=hls
    # &output=m3u
    
    return url
```

**Teste dans le terminal:**

```bash
# ❌ MPEGTS (ton erreur actuelle)
curl "http://rahali44.xyz/get.php?username=056C940&password=KV41346&type=m3u_plus&output=mpegts" -I
# Retourne du video/mp2t

# ✅ HLS (ce qu'il faut)
curl "http://rahali44.xyz/get.php?username=056C940&password=KV41346&type=m3u_plus&output=m3u8" -I
# Doit retourner du application/x-mpegURL ou text/plain avec #EXTM3U
```


***

### Option 2: Convertir MPEG-TS → HLS côté serveur (Si serveur ne supporte pas option 1)

Si le serveur IPTV ne propose que `mpegts`, tu dois **transmuxer** le flux côté backend Flask + servir du HLS au player.

#### A) Avec FFmpeg (simple, streaming direct)

```python
# routes/player.py ou services/streaming_service.py

from flask import send_file
import subprocess
import threading

@app.route('/api/player/<screen_code>/tv-stream', methods=['GET'])
def get_tv_stream(screen_code):
    """
    Récupère un flux MPEG-TS et le convertit en HLS à la volée
    """
    screen = Screen.query.filter_by(code=screen_code).first()
    if not screen or not screen.onlinetv_enabled:
        return {'error': 'TV disabled'}, 403
    
    # URL source (MPEG-TS)
    source_url = f"http://rahali44.xyz/get.php?username={screen.iptv_user}&password={screen.iptv_pass}&type=m3u_plus&output=mpegts"
    
    # Convertir MPEG-TS → HLS avec FFmpeg
    cmd = [
        'ffmpeg',
        '-i', source_url,
        '-c:v', 'copy',  # Pas de réencodage vidéo (fast)
        '-c:a', 'aac',   # Audio AAC (HLS compatible)
        '-f', 'hls',     # Output format = HLS
        '-hls_time', '6',  # Durée segment = 6s
        '-hls_list_size', '5',  # Garde 5 segments en mémoire
        '-hls_flags', 'delete_segments+live_start',
        'pipe:1'  # Output vers stdout (réponse HTTP)
    ]
    
    def stream_generator():
        """Stream HLS au navigateur"""
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1024*1024  # 1MB buffer
        )
        
        try:
            while True:
                chunk = process.stdout.read(1024)
                if not chunk:
                    break
                yield chunk
        finally:
            process.terminate()
            process.wait()
    
    return send_file(
        stream_generator(),
        mimetype='application/x-mpegURL',
        as_attachment=False,
        download_name='stream.m3u8'
    )
```

**Utilisation dans le player HTML:**

```javascript
const video = document.getElementById('tv-player');
const hls = new Hls();

// ✅ Maintenant pointe vers ton endpoint HLS converti
hls.loadSource('/api/player/screen123/tv-stream');
hls.attachMedia(video);

hls.on(Hls.Events.MANIFEST_PARSED, () => {
  video.play().catch(err => console.error('Play failed:', err));
});
```


***

#### B) Avec ffmpeg + HLS segment files (plus robuste)

Si tu veux vraiment du streaming HLS fiable:

```python
import os
import tempfile
from pathlib import Path

class HLSStreamServer:
    def __init__(self, source_url, output_dir='/tmp/hls_streams'):
        self.source_url = source_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.process = None
        
    def start(self, segment_id='screen123'):
        """Démarre la conversion MPEG-TS → HLS"""
        output_path = self.output_dir / f'{segment_id}.m3u8'
        
        cmd = [
            'ffmpeg',
            '-i', self.source_url,
            '-c:v', 'copy',  # Copy codec (pas de réencodage)
            '-c:a', 'aac',
            '-b:a', '128k',
            '-f', 'hls',
            '-hls_time', '10',
            '-hls_list_size', '10',
            '-hls_flags', 'delete_segments',
            str(output_path)
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            start_new_session=True  # Processus indépendant
        )
        
        # Attendre que le manifeste soit créé
        import time
        for _ in range(30):  # 30 tentatives
            if output_path.exists():
                return str(output_path)
            time.sleep(0.1)
        
        raise Exception(f'HLS manifest not created after 3s')
    
    def stop(self):
        """Arrête la conversion"""
        if self.process:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

# Dans routes/player.py
@app.route('/api/player/<screen_code>/tv-stream', methods=['GET'])
def get_tv_stream(screen_code):
    screen = Screen.query.filter_by(code=screen_code).first()
    if not screen or not screen.onlinetv_enabled:
        return {'error': 'TV disabled'}, 403
    
    source_url = f"http://rahali44.xyz/get.php?username={screen.iptv_user}&password={screen.iptv_pass}&type=m3u_plus&output=mpegts"
    
    # Créer ou récupérer stream HLS
    stream_key = f'{screen_code}_{int(time.time())}'
    server = HLSStreamServer(source_url)
    m3u8_path = server.start(stream_key)
    
    # Servir le fichier M3U8
    return send_file(m3u8_path, mimetype='application/x-mpegURL')
```


***

## Code complet pour AdScreen (Recommandé)

Voici le fix complet à ajouter à ton projet:

**`services/hls_converter.py`** (nouveau fichier):

```python
import subprocess
import tempfile
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MPEGTStoHLSConverter:
    """Convertit un flux MPEG-TS en HLS streamable"""
    
    @staticmethod
    def convert_stream(source_url, output_format='hls'):
        """
        Convertit un flux MPEG-TS à la volée en HLS
        
        Args:
            source_url: URL du flux MPEG-TS
            output_format: 'hls' ou 'm3u'
        
        Returns:
            (stream_bytes, mimetype) ou (manifest_path, mimetype)
        """
        
        cmd = [
            'ffmpeg',
            '-i', source_url,
            '-c:v', 'copy',              # Copy video codec (pas de réencodage)
            '-c:a', 'aac',               # Reencode audio to AAC (HLS compatible)
            '-b:a', '128k',              # Audio bitrate
            '-f', 'hls',                 # HLS format
            '-hls_time', '6',            # 6s segments
            '-hls_list_size', '5',       # Keep 5 segments
            '-hls_flags', 'delete_segments+live_start',
            'pipe:1'                     # Output to stdout
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1024*1024
            )
            
            # Générer le stream
            def stream_gen():
                try:
                    while True:
                        chunk = process.stdout.read(4096)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    process.terminate()
                    process.wait(timeout=5)
            
            return stream_gen(), 'application/x-mpegURL'
        
        except Exception as e:
            logger.error(f'FFmpeg conversion failed: {e}')
            raise

    @staticmethod
    def get_health_check(source_url, timeout=5):
        """Vérifie que le flux est accessible"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_type',
            '-of', 'default=noprint_wrappers=1',
            source_url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=timeout)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            logger.error(f'Health check failed: {e}')
            return False
```

**`routes/player.py`** (ajouter/modifier):

```python
from flask import Blueprint, send_file, jsonify
from services.hls_converter import MPEGTStoHLSConverter
from models import Screen

player_bp = Blueprint('player', __name__, url_prefix='/api/player')

@player_bp.route('/<screen_code>/config', methods=['GET'])
def get_player_config(screen_code):
    """Récupère la config du player (playlist + overlays + stream)"""
    screen = Screen.query.filter_by(code=screen_code).first()
    if not screen:
        return {'error': 'Screen not found'}, 404
    
    return {
        'playlistUrl': f'/api/player/{screen_code}/playlist',
        'tvStreamUrl': f'/api/player/{screen_code}/tv-stream',
        'overlayConfig': screen.overlay_settings or {},
        'heartbeatUrl': f'/api/heartbeat/{screen_code}',
        'onlineTvEnabled': screen.onlinetv_enabled,
        'iptvUser': screen.iptv_user,
    }

@player_bp.route('/<screen_code>/tv-stream', methods=['GET'])
def get_tv_stream(screen_code):
    """
    Récupère le flux TV MPEG-TS et le convertit en HLS
    Utilisé par le player web pour le mode OnlineTV
    """
    screen = Screen.query.filter_by(code=screen_code).first()
    
    if not screen or not screen.onlinetv_enabled:
        return {'error': 'OnlineTV disabled'}, 403
    
    if not screen.iptv_user or not screen.iptv_pass:
        return {'error': 'IPTV credentials not configured'}, 400
    
    # URL source MPEG-TS (type d'URL que tu fournis)
    source_url = f"http://rahali44.xyz/get.php?username={screen.iptv_user}&password={screen.iptv_pass}&type=m3u_plus&output=mpegts"
    
    # Vérifier que le flux est accessible
    if not MPEGTStoHLSConverter.get_health_check(source_url):
        return {'error': 'IPTV stream unreachable'}, 503
    
    try:
        stream, mimetype = MPEGTStoHLSConverter.convert_stream(source_url)
        
        return send_file(
            stream,
            mimetype=mimetype,
            as_attachment=False
        )
    
    except Exception as e:
        return {
            'error': 'Stream conversion failed',
            'details': str(e)
        }, 500

app.register_blueprint(player_bp)
```

**`templates/player.html`** (mettre à jour le lecteur):

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AdScreen Player</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/hls.js@latest"></link>
    <style>
        * { margin: 0; padding: 0; }
        body { background: #000; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
        #video-container { position: relative; width: 100vw; height: 100vh; }
        video { width: 100%; height: 100%; object-fit: contain; }
        #overlay-container { 
            position: fixed; 
            top: 0; left: 0; 
            width: 100%; height: 100%; 
            pointer-events: none;
            z-index: 100;
        }
        .error-banner {
            position: fixed;
            bottom: 20px; right: 20px;
            background: rgba(255, 0, 0, 0.9);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            font-size: 14px;
            max-width: 300px;
            z-index: 200;
        }
    </style>
</head>
<body>
    <div id="video-container">
        <video id="tv-player" autoplay muted playsinline></video>
        <div id="overlay-container"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script>
        class AdScreenPlayer {
            constructor(screenCode) {
                this.screenCode = screenCode;
                this.video = document.getElementById('tv-player');
                this.hls = null;
                this.retryCount = 0;
                this.maxRetries = 5;
                this.config = null;
                
                this.init();
            }

            async init() {
                try {
                    // Récupérer la config
                    const response = await fetch(`/api/player/${this.screenCode}/config`);
                    this.config = await response.json();
                    
                    if (this.config.onlineTvEnabled) {
                        console.log('✓ OnlineTV mode enabled');
                        this.startTVStream();
                    } else {
                        this.startPlaylist();
                    }
                } catch (err) {
                    this.showError(`Init failed: ${err.message}`);
                    setTimeout(() => this.init(), 5000);  // Retry
                }
            }

            startTVStream() {
                const streamUrl = this.config.tvStreamUrl;
                console.log('📺 Starting TV stream:', streamUrl);
                
                if (!Hls.isSupported()) {
                    // Safari fallback
                    this.video.src = streamUrl;
                    this.video.play().catch(err => {
                        this.showError(`Safari play error: ${err.message}`);
                    });
                    return;
                }

                this.hls = new Hls({
                    enableWorker: true,
                    lowLatencyMode: true,
                    autoStartLoad: false,
                    maxBufferLength: 30,
                    maxMaxBufferLength: 600,
                    defaultAudioCodec: 'aac'
                });

                this.hls.loadSource(streamUrl);
                this.hls.attachMedia(this.video);

                this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
                    console.log('✓ Manifest parsed, starting playback');
                    this.retryCount = 0;
                    this.video.play().catch(err => {
                        console.error('Play error:', err);
                        setTimeout(() => this.video.play(), 1000);
                    });
                });

                this.hls.on(Hls.Events.ERROR, (event, data) => {
                    this.handleHLSError(data);
                });

                this.hls.startLoad();
            }

            handleHLSError(data) {
                console.error('HLS Error:', data.type, data.details);
                
                if (!data.fatal) return;

                const delay = Math.min(1000 * Math.pow(2, this.retryCount), 30000);

                switch(data.type) {
                    case Hls.ErrorTypes.NETWORK_ERROR:
                        console.log(`⚠️ Network error, retry in ${delay}ms`);
                        if (this.retryCount < this.maxRetries) {
                            setTimeout(() => {
                                this.hls.startLoad();
                                this.retryCount++;
                            }, delay);
                        } else {
                            this.showError('Flux TV indisponible - trop d\'erreurs');
                        }
                        break;

                    case Hls.ErrorTypes.MEDIA_ERROR:
                        console.log('⚠️ Media error, recovering...');
                        this.hls.recoverMediaError();
                        break;

                    default:
                        this.showError(`Erreur critique: ${data.details}`);
                        setTimeout(() => location.reload(), 5000);
                }
            }

            startPlaylist() {
                console.log('📹 Starting playlist mode');
                // Ton code playlist existant
            }

            showError(msg) {
                console.error('❌', msg);
                const banner = document.createElement('div');
                banner.className = 'error-banner';
                banner.textContent = msg;
                document.body.appendChild(banner);
                setTimeout(() => banner.remove(), 5000);
            }
        }

        // Démarrer le player
        const screenCode = new URLSearchParams(window.location.search).get('screen');
        if (screenCode) {
            new AdScreenPlayer(screenCode);
        } else {
            console.error('❌ Screen code not provided');
        }
    </script>
</body>
</html>
```


***

## Résumé des changements pour AdScreen

| Étape | Action |
| :-- | :-- |
| 1 | Ajouter `services/hls_converter.py` (conversion MPEG-TS → HLS) |
| 2 | Ajouter route `/api/player/<screen>/tv-stream` (blueprint player) |
| 3 | Mettre à jour `templates/player.html` avec hls.js et gestion erreurs |
| 4 | Installer ffmpeg: `apt-get install ffmpeg` (ou `brew install ffmpeg`) |
| 5 | Tester avec ton URL IPTV (`rahali44.xyz/get.php?...&output=mpegts`) |


***

## Tests

```bash
# 1️⃣ Vérifier que FFmpeg fonctionne
ffmpeg -version

# 2️⃣ Tester la conversion locale
ffmpeg -i "http://rahali44.xyz/get.php?username=056C940&password=KV41346&type=m3u_plus&output=mpegts" \
  -c:v copy -c:a aac -f hls -hls_time 6 -hls_list_size 5 test.m3u8

# 3️⃣ Ouvrir le player dans le navigateur
# http://localhost:5000/player.html?screen=screen123
```

Veux-tu que je crée le fichier complet à commiter sur ton repo GitHub ?
<span style="display:none">[^1][^2][^3]</span>

<div align="center">⁂</div>

[^1]: image.jpg

[^2]: image.jpg

[^3]: https://github.com/moa-digitalagency/AdScreen

