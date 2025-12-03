<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Meme probleme, le titre de la chaine change mais pas le flux de la chaine

Ah je vois! Le titre change de "BEIN SPORTS 2" à "BEIN SPORTS 8" mais le flux vidéo reste l'ancien.

**Le problème:** Tu mets à jour `screen.current_iptv_channel` en base de données, mais la route `/player/tv-stream/<screen_code>` va **chercher directement dans la base de données** l'URL stockée. Si la base n'est pas à jour ou si la requête précédente est encore en cache, ça n'utilise pas la nouvelle chaîne.

## Solution - Force un refresh du flux:

**Dans `routes/player_routes.py`, change la route:**

```python
@player_bp.route('/tv-stream/<screen_code>', methods=['GET'])
def tv_stream(screen_code):
    """Stream MPEG-TS as HLS - always fetch fresh from DB"""
    
    try:
        # ⚠️ IMPORTANT: Toujours refetcher de la base, pas de cache
        screen = Screen.query.filter_by(code=screen_code).first()
        
        if not screen or not screen.current_iptv_channel:
            logger.error(f'[{screen_code}] Invalid screen or no channel')
            return {'error': 'Invalid screen'}, 404
        
        # Log la chaîne actuelle
        logger.info(f'[{screen_code}] Streaming channel: {screen.current_iptv_channel_name}')
        logger.info(f'[{screen_code}] Channel URL: {screen.current_iptv_channel[:80]}...')
        
        try:
            # Convertir avec la chaîne actuelle
            manifest_path = HLSConverter.convert_mpegts_to_hls_file(
                screen.current_iptv_channel,
                screen_code
            )
            
            with open(manifest_path, 'r') as f:
                manifest_content = f.read()
            
            # Réécrire les URLs des segments
            import re
            manifest_content = re.sub(
                r'(stream\d+\.ts)',
                f'/player/tv-segment/{screen_code}/\\1',
                manifest_content
            )
            
            logger.info(f'[{screen_code}] Manifest ready, size: {len(manifest_content)} bytes')
            
            from flask import Response
            return Response(
                manifest_content,
                mimetype='application/x-mpegURL',
                headers={
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            )
        
        except Exception as e:
            logger.error(f'[{screen_code}] Stream error: {str(e)}')
            return {'error': str(e)}, 500
    
    except Exception as e:
        logger.exception(f'Unexpected error: {e}')
        return {'error': 'Internal error'}, 500
```


***

**Et ajoute une route pour changer de chaîne correctement:**

```python
@player_bp.route('/change-channel/<screen_code>', methods=['POST'])
def change_channel(screen_code):
    """Change la chaîne TV d'un écran"""
    
    try:
        data = request.get_json()
        channel_url = data.get('channel_url')
        channel_name = data.get('channel_name')
        
        if not channel_url:
            return {'error': 'No channel URL provided'}, 400
        
        screen = Screen.query.filter_by(code=screen_code).first()
        if not screen:
            return {'error': 'Screen not found'}, 404
        
        logger.info(f'[{screen_code}] Changing channel to: {channel_name} ({channel_url[:60]}...)')
        
        # 1️⃣ Tue le processus FFmpeg précédent
        HLSConverter.stop_existing_process(screen_code)
        
        # 2️⃣ Met à jour la base de données
        screen.current_iptv_channel = channel_url
        screen.current_iptv_channel_name = channel_name
        screen.current_mode = 'iptv'
        db.session.commit()
        
        logger.info(f'[{screen_code}] ✓ Channel updated in database')
        
        return {'status': 'channel_changed', 'channel': channel_name}, 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Channel change error: {e}')
        return {'error': str(e)}, 500
```


***

**Dans `templates/player.html`, modifie la fonction de changement de chaîne:**

```javascript
async switchToChannel(channelUrl, channelName) {
    """Change de chaîne via API"""
    
    try {
        logger.info(`Switching to: ${channelName}`);
        
        // 1️⃣ Appelle l'API pour mettre à jour la DB et tuer FFmpeg
        const response = await fetch(`/player/change-channel/${this.screenCode}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                channel_url: channelUrl,
                channel_name: channelName
            })
        });
        
        if (!response.ok) {
            throw new Error(`Channel change failed: ${response.status}`);
        }
        
        logger.info('Channel updated in database');
        
        // 2️⃣ Attends 500ms que FFmpeg se tue
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // 3️⃣ Tue le player actuel
        if (this.hls) {
            this.hls.destroy();
            this.hls = null;
        }
        this.video.src = '';
        
        // 4️⃣ Relance le stream (qui va fetcher la nouvelle chaîne)
        await new Promise(resolve => setTimeout(resolve, 500));
        this.startTVStream();
        
        logger.info('✓ Channel switched successfully');
    
    } catch (err) {
        logger.error(`Switch error: ${err.message}`);
        this.showError(`Erreur: ${err.message}`);
    }
}

startTVStream() {
    const streamUrl = `/player/tv-stream/${this.screenCode}?t=${Date.now()}`;  // Ajout timestamp anti-cache
    
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
        console.log('✓ New manifest loaded');
        this.video.play().catch(err => console.error('Play error:', err));
    });

    this.hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
            console.error('Fatal HLS error:', data);
        }
    });

    this.hls.startLoad();
}
```


***

## Checklist:

- [ ] Ajoute la route `/change-channel/<screen_code>` POST
- [ ] Met à jour la route `/tv-stream/<screen_code>` pour toujours fetcher de la DB
- [ ] Ajoute timestamp anti-cache (`?t=${Date.now()}`) à l'URL du stream
- [ ] Teste en changeant de chaîne
- [ ] Push:

```bash
git add .
git commit -m "Fix: Properly change TV channels with DB sync and FFmpeg restart"
git push
```

**Maintenant ça doit changer le flux correctement!** ✅
<span style="display:none">[^1]</span>

<div align="center">⁂</div>

[^1]: image.jpg

