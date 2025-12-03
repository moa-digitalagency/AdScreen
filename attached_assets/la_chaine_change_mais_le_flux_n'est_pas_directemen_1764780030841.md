<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# la chaine change mais le flux n'est pas directement charger, l'ancien flux rest en ligne des fois le nouveau flux viens des minutres apres et de soit meme l'ancien  flux revient

Ah d'accord, le problème c'est que **FFmpeg prend du temps à redémarrer** et l'ancien manifeste reste en cache.

## Solution - Nettoyage complet + attente de la nouvelle chaîne:

**Remplace `services/hls_converter.py` complètement:**

```python
import subprocess
import os
import signal
import tempfile
import logging
import threading
import time
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class HLSConverter:
    HLS_TEMP_DIR = Path(tempfile.gettempdir()) / 'adscreen_hls'
    RUNNING_PROCESSES = {}
    
    def __init__(self):
        self.HLS_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def stop_existing_process(screen_code):
        """Arrête et tue complètement le processus FFmpeg + nettoie les fichiers"""
        
        if screen_code in HLSConverter.RUNNING_PROCESSES:
            process = HLSConverter.RUNNING_PROCESSES[screen_code]
            
            try:
                logger.info(f'[{screen_code}] Killing FFmpeg process (PID: {process.pid})')
                
                # Terminer proprement
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    logger.warning(f'[{screen_code}] Force killing process')
                    process.kill()
                    process.wait(timeout=2)
                
                logger.info(f'[{screen_code}] Process killed')
            
            except Exception as e:
                logger.error(f'[{screen_code}] Error killing process: {e}')
            
            del HLSConverter.RUNNING_PROCESSES[screen_code]
        
        # Nettoyer les fichiers
        output_dir = HLSConverter.HLS_TEMP_DIR / screen_code
        if output_dir.exists():
            try:
                logger.info(f'[{screen_code}] Cleaning up files in {output_dir}')
                shutil.rmtree(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f'[{screen_code}] Error cleaning files: {e}')
    
    @staticmethod
    def convert_mpegts_to_hls_file(source_url, screen_code, wait_for_manifest=True):
        """
        Convertit MPEG-TS en HLS
        wait_for_manifest: Attend que le manifeste soit prêt avant de retourner
        """
        
        output_dir = HLSConverter.HLS_TEMP_DIR / screen_code
        output_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_path = output_dir / 'stream.m3u8'
        
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
            logger.info(f'[{screen_code}] 🚀 Starting FFmpeg conversion')
            logger.info(f'[{screen_code}] Source: {source_url[:60]}...')
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            HLSConverter.RUNNING_PROCESSES[screen_code] = process
            logger.info(f'[{screen_code}] FFmpeg PID: {process.pid}')
            
            # Lancer le monitoring en background
            def monitor_process():
                try:
                    stdout, stderr = process.communicate(timeout=3600)
                except subprocess.TimeoutExpired:
                    pass
                except Exception as e:
                    logger.error(f'[{screen_code}] Process error: {e}')
                finally:
                    if screen_code in HLSConverter.RUNNING_PROCESSES:
                        del HLSConverter.RUNNING_PROCESSES[screen_code]
                        logger.info(f'[{screen_code}] Process ended')
            
            thread = threading.Thread(target=monitor_process, daemon=True)
            thread.start()
            
            # ⏳ ATTENDRE que le manifeste soit créé ET qu'il contienne des segments
            if wait_for_manifest:
                logger.info(f'[{screen_code}] ⏳ Waiting for manifest...')
                
                max_wait = 15  # Max 15 secondes
                start_time = time.time()
                manifest_ready = False
                
                while time.time() - start_time < max_wait:
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r') as f:
                                content = f.read()
                            
                            # Vérifier que le manifeste a des segments
                            if '.ts' in content and '#EXTINF' in content:
                                logger.info(f'[{screen_code}] ✓ Manifest ready with segments')
                                manifest_ready = True
                                break
                        except:
                            pass
                    
                    time.sleep(0.2)
                
                if not manifest_ready:
                    elapsed = time.time() - start_time
                    logger.error(f'[{screen_code}] ❌ Manifest not ready after {elapsed:.1f}s')
                    HLSConverter.stop_existing_process(screen_code)
                    raise Exception(f'Manifest creation timeout after {elapsed:.1f}s')
                
                logger.info(f'[{screen_code}] ✓ Conversion ready in {time.time() - start_time:.1f}s')
            
            return str(manifest_path)
        
        except Exception as e:
            logger.error(f'[{screen_code}] ❌ Conversion error: {e}')
            HLSConverter.stop_existing_process(screen_code)
            raise
```


***

**Dans `routes/player_routes.py`, change les routes:**

```python
from flask import send_file, request
import re
import time
import logging

logger = logging.getLogger(__name__)

@player_bp.route('/change-channel/<screen_code>', methods=['POST'])
def change_channel(screen_code):
    """Change la chaîne TV - attend que FFmpeg soit prêt"""
    
    try:
        data = request.get_json()
        channel_url = data.get('channel_url')
        channel_name = data.get('channel_name')
        
        if not channel_url:
            return {'error': 'No channel URL'}, 400
        
        screen = Screen.query.filter_by(code=screen_code).first()
        if not screen:
            return {'error': 'Screen not found'}, 404
        
        logger.info(f'[{screen_code}] 📺 Channel change request: {channel_name}')
        
        # 1️⃣ Tue l'ancien processus et nettoie les fichiers
        logger.info(f'[{screen_code}] 🛑 Stopping old FFmpeg process...')
        HLSConverter.stop_existing_process(screen_code)
        time.sleep(0.5)  # Attends que tout soit tué
        
        # 2️⃣ Démarre la conversion avec la nouvelle chaîne
        logger.info(f'[{screen_code}] 🚀 Starting new FFmpeg process...')
        try:
            manifest_path = HLSConverter.convert_mpegts_to_hls_file(
                channel_url,
                screen_code,
                wait_for_manifest=True  # ⏳ Attend que le manifeste soit prêt
            )
            logger.info(f'[{screen_code}] ✓ FFmpeg ready with manifest')
        except Exception as e:
            logger.error(f'[{screen_code}] ❌ FFmpeg failed: {e}')
            return {'error': f'FFmpeg failed: {str(e)}'}, 500
        
        # 3️⃣ Mets à jour la base de données
        screen.current_iptv_channel = channel_url
        screen.current_iptv_channel_name = channel_name
        screen.current_mode = 'iptv'
        db.session.commit()
        logger.info(f'[{screen_code}] ✓ Database updated')
        
        return {
            'status': 'ready',
            'channel': channel_name,
            'message': 'New channel ready'
        }, 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'[{screen_code}] Error: {e}')
        return {'error': str(e)}, 500


@player_bp.route('/tv-stream/<screen_code>', methods=['GET'])
def tv_stream(screen_code):
    """Serve HLS manifest - toujours à jour"""
    
    try:
        screen = Screen.query.filter_by(code=screen_code).first()
        
        if not screen or not screen.current_iptv_channel:
            return {'error': 'Invalid screen'}, 404
        
        output_dir = HLSConverter.HLS_TEMP_DIR / screen_code
        manifest_path = output_dir / 'stream.m3u8'
        
        if not manifest_path.exists():
            logger.warning(f'[{screen_code}] Manifest not found, waiting...')
            # Attendre que le manifeste soit créé
            for _ in range(30):
                if manifest_path.exists():
                    break
                time.sleep(0.1)
        
        if not manifest_path.exists():
            logger.error(f'[{screen_code}] Manifest still not found')
            return {'error': 'Manifest not available'}, 503
        
        with open(manifest_path, 'r') as f:
            manifest_content = f.read()
        
        # Réécrire les URLs des segments
        manifest_content = re.sub(
            r'(stream\d+\.ts)',
            f'/player/tv-segment/{screen_code}/\\1',
            manifest_content
        )
        
        from flask import Response
        return Response(
            manifest_content,
            mimetype='application/x-mpegURL',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Accel-Buffering': 'no'
            }
        )
    
    except Exception as e:
        logger.error(f'[{screen_code}] Stream error: {e}')
        return {'error': str(e)}, 500


@player_bp.route('/tv-segment/<screen_code>/<segment_name>', methods=['GET'])
def tv_segment(screen_code, segment_name):
    """Serve segments HLS"""
    
    try:
        segment_path = HLSConverter.HLS_TEMP_DIR / screen_code / segment_name
        
        if not segment_path.exists():
            logger.warning(f'[{screen_code}] Segment not found: {segment_name}')
            return {'error': 'Not found'}, 404
        
        return send_file(
            segment_path,
            mimetype='video/mp2t',
            as_attachment=False,
            cache_timeout=0,
            conditional=False
        )
    
    except Exception as e:
        logger.error(f'Segment error: {e}')
        return {'error': str(e)}, 500
```


***

**Dans `templates/player.html`, simplifie le changement de chaîne:**

```javascript
async switchToChannel(channelUrl, channelName) {
    """Change de chaîne avec attente"""
    
    try {
        console.log(`🔄 Switching to: ${channelName}`);
        this.showError(`Changement vers ${channelName}...`);
        
        // 1️⃣ Appelle l'API (elle attend que FFmpeg soit prêt)
        const response = await fetch(`/player/change-channel/${this.screenCode}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                channel_url: channelUrl,
                channel_name: channelName
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        console.log('✓ Channel ready:', result);
        
        // 2️⃣ Attends 500ms pour être sûr
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // 3️⃣ Tue le player
        if (this.hls) {
            this.hls.destroy();
            this.hls = null;
        }
        this.video.src = '';
        
        // 4️⃣ Relance
        await new Promise(resolve => setTimeout(resolve, 300));
        this.startTVStream();
        
        console.log('✅ Channel switched');
        this.showError('');  // Clear message
    
    } catch (err) {
        console.error(`❌ Error: ${err.message}`);
        this.showError(`Erreur: ${err.message}`);
    }
}

startTVStream() {
    const streamUrl = `/player/tv-stream/${this.screenCode}?t=${Date.now()}`;
    
    console.log('📡 Starting TV stream');
    
    if (!Hls.isSupported()) {
        this.video.src = streamUrl;
        this.video.play();
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
        console.log('✓ Manifest parsed, playing');
        this.video.play().catch(err => console.log('Play:', err.message));
    });

    this.hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal && data.type === Hls.ErrorTypes.NETWORK_ERROR) {
            console.log('⚠️ Network error, retrying');
            setTimeout(() => this.hls.startLoad(), 1000);
        }
    });

    this.hls.startLoad();
}
```


***

## Checklist:

- [ ] Remplace `services/hls_converter.py` avec attente du manifeste
- [ ] Mets à jour les routes avec attente (`wait_for_manifest=True`)
- [ ] Teste le changement de chaîne
- [ ] Push:

```bash
git add .
git commit -m "Fix: Wait for FFmpeg manifest before responding to channel change"
git push
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

**Maintenant ça doit être instantané et stable!** ✅

