<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# ah aussi meme qd je change les chaines ca ne change pas la chaine ca montre tjrs la meme chaine bein sport 2 ar, qui la premier chaine que j'ai lancé apres imporssiblede mettre une chaine autre la premiere reviens toujours

Ah d'accord! Le problème c'est que **FFmpeg continue à tourner sur l'ancienne chaîne** et ne s'arrête jamais. Quand tu changes de chaîne, le processus FFmpeg ancien n'est pas tué.

## Solution - Tue le processus FFmpeg précédent:

**Remplace `services/hls_converter.py` par ceci:**

```python
import subprocess
import os
import signal
import tempfile
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

class HLSConverter:
    HLS_TEMP_DIR = Path(tempfile.gettempdir()) / 'adscreen_hls'
    RUNNING_PROCESSES = {}  # Tracker les processus par screen_code
    
    def __init__(self):
        self.HLS_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def stop_existing_process(screen_code):
        """Arrête le processus FFmpeg précédent pour cette chaîne"""
        
        if screen_code in HLSConverter.RUNNING_PROCESSES:
            process = HLSConverter.RUNNING_PROCESSES[screen_code]
            
            try:
                logger.info(f'[{screen_code}] Killing previous FFmpeg process (PID: {process.pid})')
                
                # Terminer proprement
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # Forcer si terminate ne marche pas
                    logger.warning(f'[{screen_code}] Force killing process')
                    process.kill()
                    process.wait()
                
                logger.info(f'[{screen_code}] Previous process stopped')
            
            except Exception as e:
                logger.error(f'[{screen_code}] Error stopping process: {e}')
            
            del HLSConverter.RUNNING_PROCESSES[screen_code]
    
    @staticmethod
    def convert_mpegts_to_hls_file(source_url, screen_code):
        """
        Convertit MPEG-TS en HLS et sauvegarde les segments sur disque
        Tue l'ancien processus si la chaîne change
        """
        
        # D'abord, arrête le processus précédent
        HLSConverter.stop_existing_process(screen_code)
        
        output_dir = HLSConverter.HLS_TEMP_DIR / screen_code
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Nettoyer les anciens segments
        for f in output_dir.glob('*.ts'):
            try:
                f.unlink()
            except:
                pass
        
        # Nettoyer l'ancien manifeste
        manifest_path = output_dir / 'stream.m3u8'
        if manifest_path.exists():
            try:
                manifest_path.unlink()
            except:
                pass
        
        cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-timeout', '30000000',
            '-i', source_url,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '96k',
            '-f', 'hls',
            '-hls_time', '2',
            '-hls_list_size', '3',
            '-hls_flags', 'delete_segments+live_start+independent_segments',
            '-flvflags', 'no_duration_filesize',
            str(manifest_path)
        ]
        
        try:
            logger.info(f'[{screen_code}] Starting FFmpeg conversion')
            logger.info(f'[{screen_code}] Source: {source_url[:80]}...')
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Créer un process group
            )
            
            # Enregistrer le processus
            HLSConverter.RUNNING_PROCESSES[screen_code] = process
            
            logger.info(f'[{screen_code}] FFmpeg started (PID: {process.pid})')
            
            # Lancer le monitoring en background
            def monitor_process():
                try:
                    stdout, stderr = process.communicate(timeout=3600)  # Max 1h
                except subprocess.TimeoutExpired:
                    pass
                except Exception as e:
                    logger.error(f'[{screen_code}] Process error: {e}')
                finally:
                    if screen_code in HLSConverter.RUNNING_PROCESSES:
                        del HLSConverter.RUNNING_PROCESSES[screen_code]
            
            thread = threading.Thread(target=monitor_process, daemon=True)
            thread.start()
            
            # Attendre que le manifeste soit créé
            import time
            for i in range(30):
                if manifest_path.exists():
                    logger.info(f'[{screen_code}] ✓ Manifest created after {i*100}ms')
                    return str(manifest_path)
                time.sleep(0.1)
            
            logger.error(f'[{screen_code}] Manifest not created after 3s')
            HLSConverter.stop_existing_process(screen_code)
            raise Exception('Manifest creation timeout')
        
        except Exception as e:
            logger.error(f'[{screen_code}] Conversion error: {e}')
            HLSConverter.stop_existing_process(screen_code)
            raise
```


***

**Dans `routes/player_routes.py`, ajoute aussi:**

```python
@player_bp.route('/tv-stop/<screen_code>', methods=['POST'])
def stop_tv_stream(screen_code):
    """Arrête le stream TV d'un écran"""
    
    try:
        logger.info(f'[{screen_code}] Stopping TV stream')
        HLSConverter.stop_existing_process(screen_code)
        return {'status': 'stopped'}, 200
    except Exception as e:
        logger.error(f'Stop error: {e}')
        return {'error': str(e)}, 500
```


***

**Dans `templates/player.html`, appelle `/tv-stop` avant de changer:**

```javascript
class AdScreenPlayer {
    constructor(screenCode) {
        this.screenCode = screenCode;
        this.video = document.getElementById('tv-player');
        this.hls = null;
        this.currentMode = 'playlist';
        this.init();
    }

    async switchToChannel(channelUrl) {
        """Change de chaîne TV"""
        
        try {
            logger.info(`Switching to new channel: ${channelUrl.substring(0, 80)}...`);
            
            // 1️⃣ Arrête le stream FFmpeg précédent côté serveur
            await fetch(`/player/tv-stop/${this.screenCode}`, { method: 'POST' });
            
            // 2️⃣ Attends 500ms que le processus soit tué
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // 3️⃣ Détruis l'instance hls.js
            if (this.hls) {
                this.hls.destroy();
                this.hls = null;
            }
            
            // 4️⃣ Vide la vidéo
            this.video.src = '';
            
            // 5️⃣ Lance la conversion FFmpeg pour la nouvelle chaîne
            this.startTVStream();
            
            logger.info('Channel switched successfully');
        
        } catch (err) {
            logger.error(`Switch error: ${err.message}`);
            this.showError(`Erreur changement chaîne: ${err.message}`);
        }
    }

    startTVStream() {
        const streamUrl = `/player/tv-stream/${this.screenCode}`;
        
        if (!Hls.isSupported()) {
            this.video.src = streamUrl;
            this.video.play().catch(err => this.showError(err.message));
            return;
        }

        this.hls = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
            maxBufferLength: 5,
            maxMaxBufferLength: 15,
            defaultAudioCodec: 'aac',
            manifestLoadingMaxRetry: 3,
            fragLoadingMaxRetry: 3,
            fragLoadingRetryDelay: 500
        });

        this.hls.loadSource(streamUrl);
        this.hls.attachMedia(this.video);

        this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
            console.log('✓ Manifest loaded');
            this.video.play().catch(err => console.error('Play error:', err));
        });

        this.hls.on(Hls.Events.ERROR, (event, data) => {
            if (data.fatal) {
                console.error('Fatal HLS error:', data);
                if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
                    setTimeout(() => this.hls.startLoad(), 1000);
                }
            }
        });

        this.hls.startLoad();
    }

    showError(msg) {
        console.error('❌', msg);
        // Afficher message d'erreur UI
    }
}
```


***

## Checklist:

- [ ] Remplace `services/hls_converter.py` avec gestion des processus
- [ ] Ajoute la route `/tv-stop/<screen_code>` dans `routes/player_routes.py`
- [ ] Met à jour `templates/player.html` avec `switchToChannel()`
- [ ] Push et teste:

```bash
git add .
git commit -m "Fix: Kill previous FFmpeg process when switching channels"
git push
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

**Maintenant tu peux changer de chaîne sans problème!** ✅

