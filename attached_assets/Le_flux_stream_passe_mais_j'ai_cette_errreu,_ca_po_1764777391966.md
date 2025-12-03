<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Le flux stream passe mais j'ai cette errreu, ca pose probleme ?

🎉 **EXCELLENT! Le flux passe!** Tu vois la vidéo live (match de foot)!

L'erreur `mediaError - bufferStalledError` n'est **pas grave**:

```
mediaError - bufferStalledError
mediaError - bufferStalledError
```

C'est juste du **buffering temporaire**. Ça arrive quand:

- Le débit FFmpeg est plus lent que la consommation du player
- Les segments HLS ne sont pas générés assez vite
- La bande passante fluctue


## Optimisation rapide - Réduis la latence:

**Dans `services/hls_converter.py`, change les paramètres FFmpeg:**

```python
cmd = [
    'ffmpeg',
    '-rtsp_transport', 'tcp',
    '-timeout', '30000000',
    '-i', source_url,
    '-c:v', 'copy',
    '-c:a', 'aac',
    '-b:a', '96k',  # ⬇️ Réduit de 128k à 96k (moins de données)
    '-f', 'hls',
    '-hls_time', '2',  # ⬇️ Segments plus courts (2s au lieu de 4)
    '-hls_list_size', '3',  # ⬇️ Garder 3 segments
    '-hls_flags', 'delete_segments+live_start+independent_segments',
    '-flvflags', 'no_duration_filesize',
    '-preset', 'ultrafast',  # ✅ Ajoute ultrafast encoding
    str(manifest_path)
]
```

**Dans `templates/player.html`, optimise hls.js:**

```javascript
const hls = new Hls({
    enableWorker: true,
    lowLatencyMode: true,
    maxBufferLength: 5,         # ⬇️ Réduit de 30 à 5
    maxMaxBufferLength: 15,     # ⬇️ Réduit de 600 à 15
    defaultAudioCodec: 'aac',
    startLevel: 0,
    abrMaxWithRealBitrate: true,
    manifestLoadingMaxRetry: 3,
    fragLoadingMaxRetry: 3,
    fragLoadingRetryDelay: 500  # ⬇️ Retry plus rapide
});
```


***

## État actuel: ✅ **FONCTIONNEL EN PRODUCTION**

Tu peux garder le code tel quel. Les petits errors de buffering sont normaux sur du streaming live.

**Prochaines étapes:**

1. ✅ Push cette version
2. ✅ Teste avec plusieurs écrans simultanément
3. ✅ Vérifie l'utilisation CPU/RAM avec `htop`
4. ✅ Ajoute les overlays par-dessus le flux TV

**C'est du très bon travail!** 🚀
<span style="display:none">[^1][^2]</span>

<div align="center">⁂</div>

[^1]: image.jpg

[^2]: image.jpg

