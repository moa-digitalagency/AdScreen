# Guide de développement Player Mobile

Ce guide vous accompagne pour créer un player natif Android ou iOS qui diffuse du contenu Shabaka AdScreen. Le player se synchronise avec le backend pour récupérer la playlist, signaler son activité et enregistrer les statistiques de diffusion.

## Architecture du player

Un player mobile complet se compose de plusieurs modules :

```
┌─────────────────────────────────────────────────────────────┐
│                        PLAYER MOBILE                         │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Module Auth   │  Module Playlist │    Module Player        │
│   (JWT tokens)  │  (sync données)  │    (lecture média)      │
├─────────────────┼─────────────────┼─────────────────────────┤
│  Module Overlay │  Module Heartbeat │   Module Stats         │
│  (bandeaux)     │  (signal activité)│   (log des lectures)   │
├─────────────────┴─────────────────┴─────────────────────────┤
│                     Module Cache (hors ligne)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API BACKEND                             │
└─────────────────────────────────────────────────────────────┘
```

## Séquence de démarrage

Voici ce qui doit se passer quand le player démarre :

```
1. Afficher l'écran de connexion
2. Utilisateur entre : code écran + mot de passe
3. Appeler POST /mobile/api/v1/auth/screen-login
4. Stocker les tokens JWT de manière sécurisée
5. Récupérer la playlist avec GET /mobile/api/v1/screen/playlist
6. Pré-télécharger les médias en cache local
7. Démarrer les timers (heartbeat toutes les 30s, refresh playlist toutes les 60s)
8. Lancer la boucle de lecture
```

## Synchronisation avec le backend

### Intervalles recommandés

| Opération | Intervalle | Objectif |
|-----------|------------|----------|
| Heartbeat | 30 secondes | Signaler que le player est actif |
| Playlist | 60 secondes | Détecter les nouveaux contenus |
| Log play | Temps réel | Après chaque contenu joué |

### Gestion des tokens

Les tokens JWT ont une durée de vie limitée :
- Access token : 24 heures
- Refresh token : 30 jours

Quand une requête retourne 401 (token expiré) :
1. Appelez `/mobile/api/v1/auth/refresh` avec le refresh token
2. Stockez les nouveaux tokens
3. Rejouez la requête originale

Si le refresh échoue aussi, redirigez vers l'écran de connexion.

## API utilisée par le player

### Connexion

```
POST /mobile/api/v1/auth/screen-login
Content-Type: application/json

{
  "screen_code": "ABC123",
  "password": "screen123"
}
```

Réponse :

```json
{
  "success": true,
  "screen": {
    "id": 1,
    "name": "Écran Restaurant",
    "unique_code": "ABC123",
    "resolution": "1920x1080",
    "orientation": "landscape"
  },
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "expires_in": 86400
}
```

### Récupération du mode

```
GET /mobile/api/v1/screen/mode
Authorization: Bearer <access_token>
```

Réponse :

```json
{
  "mode": "playlist",
  "iptv_enabled": true,
  "iptv_channel_url": null,
  "iptv_channel_name": null
}
```

Le mode est soit `playlist` (lecture de contenus) soit `iptv` (flux TV en direct).

### Récupération de la playlist

```
GET /mobile/api/v1/screen/playlist
Authorization: Bearer <access_token>
```

Réponse :

```json
{
  "screen": {
    "id": 1,
    "name": "Écran Restaurant",
    "resolution": "1920x1080",
    "orientation": "landscape"
  },
  "mode": "playlist",
  "playlist": [
    {
      "id": 123,
      "type": "image",
      "url": "/static/uploads/content/1/image.jpg",
      "duration": 10,
      "priority": 100,
      "category": "paid",
      "booking_id": 45,
      "remaining_plays": 150,
      "name": "Publicite.jpg"
    },
    {
      "id": 456,
      "type": "video",
      "url": "/static/uploads/content/1/video.mp4",
      "duration": 30,
      "priority": 80,
      "category": "internal",
      "booking_id": null,
      "remaining_plays": null,
      "name": "Promo.mp4"
    }
  ],
  "overlays": [
    {
      "id": 1,
      "type": "scrolling_text",
      "content": "Bienvenue dans notre établissement!",
      "position": "bottom",
      "style": {
        "background_color": "#000000",
        "text_color": "#FFFFFF",
        "font_size": 24,
        "speed": 50
      },
      "priority": 50,
      "source": "LOCAL"
    }
  ],
  "iptv": null
}
```

### Heartbeat

```
POST /mobile/api/v1/screen/heartbeat
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "playing"
}
```

Les statuts possibles : `online`, `playing`, `paused`, `idle`, `error`

### Log de lecture

```
POST /mobile/api/v1/screen/log-play
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content_id": 123,
  "content_type": "image",
  "category": "paid",
  "duration": 10,
  "booking_id": 45
}
```

Réponse :

```json
{
  "success": true,
  "exhausted": false
}
```

Si `exhausted` est `true`, le contenu a atteint son quota. Retirez-le de la playlist.

## Structure des données

### Contenu

```typescript
interface ContentItem {
  id: number;
  type: 'image' | 'video';
  url: string;
  duration: number;           // en secondes
  priority: number;           // 20-200
  category: 'paid' | 'internal' | 'filler' | 'broadcast' | 'ad_content';
  booking_id: number | null;
  remaining_plays: number | null;
  name: string;
}
```

### Priorités

| Catégorie | Priorité | Description |
|-----------|----------|-------------|
| broadcast | 200 | Diffusions opérateur (priorité maximale) |
| paid | 100 | Publicités payantes des clients |
| internal | 80 | Contenus de l'établissement |
| ad_content | 60 | Publicités de l'opérateur |
| filler | 20 | Contenus de remplissage |

### Overlay

```typescript
interface Overlay {
  id: number;
  type: 'scrolling_text' | 'static_image' | 'static_text';
  content: string;           // texte ou URL d'image
  position: 'top' | 'bottom' | 'left' | 'right';
  style: OverlayStyle;
  priority: number;
  source: 'LOCAL' | 'BROADCAST';
  active: boolean;
}

interface OverlayStyle {
  background_color: string;
  text_color: string;
  font_size: number;
  speed?: number;            // pour scrolling_text
  opacity?: number;
}
```

## Logique de lecture

### Algorithme de sélection

La playlist est triée par priorité décroissante. À priorité égale, les contenus passent en round-robin.

```python
def get_next_content(playlist, current_index):
    # Trier par priorité décroissante
    sorted_playlist = sorted(playlist, key=lambda x: x['priority'], reverse=True)
    
    # Filtrer les contenus épuisés
    available = [c for c in sorted_playlist if c.get('remaining_plays', 1) > 0]
    
    if not available:
        return None
    
    # Round-robin
    next_index = (current_index + 1) % len(available)
    return available[next_index]
```

### Durée d'affichage

- **Images** : utilisez la durée spécifiée dans l'item (défaut : 10 secondes)
- **Vidéos** : jouez la vidéo jusqu'à la fin, ignorez la durée spécifiée

### Boucle de lecture

```
1. Récupérer le contenu suivant
2. Afficher (image) ou lire (vidéo)
3. Attendre la fin de la durée ou de la vidéo
4. Appeler log-play pour signaler la diffusion
5. Si exhausted=true, retirer le contenu
6. Passer au contenu suivant
7. Répéter
```

## Affichage des overlays

Les overlays s'affichent par-dessus le contenu principal :

```
┌────────────────────────────────────────────┐
│              [Overlay top]                 │
├────────────────────────────────────────────┤
│                                            │
│          CONTENU PRINCIPAL                 │
│          (image ou vidéo)                  │
│                                            │
├────────────────────────────────────────────┤
│             [Overlay bottom]               │
└────────────────────────────────────────────┘
```

Les overlays BROADCAST ont priorité sur les overlays LOCAL. Quand un overlay BROADCAST est actif, masquez temporairement les overlays LOCAL.

### Types d'overlay

- **scrolling_text** : texte qui défile horizontalement
- **static_image** : image fixe (logo, QR code)
- **static_text** : texte fixe (annonces)

## Mode IPTV

Quand le mode est `iptv`, le player doit :

1. Arrêter la lecture de la playlist
2. Démarrer le flux HLS (URL fournie dans `iptv.url`)
3. Continuer à afficher les overlays par-dessus
4. Continuer les heartbeats

```json
{
  "mode": "iptv",
  "iptv": {
    "url": "https://stream.example.com/live.m3u8",
    "name": "Chaîne Info"
  },
  "playlist": [],
  "overlays": [...]
}
```

Utilisez HLS.js (web), ExoPlayer (Android) ou AVPlayer (iOS) pour la lecture.

## Gestion hors ligne

Pour continuer à fonctionner sans connexion :

### Stratégie de cache

1. À chaque récupération de playlist, téléchargez les médias en arrière-plan
2. Stockez-les dans le cache local (SQLite ou système de fichiers)
3. Si la connexion est perdue, lisez depuis le cache
4. Mettez les log-play en file d'attente
5. À la reconnexion, envoyez les logs en attente

### Schéma de base locale

```sql
CREATE TABLE cached_media (
  id INTEGER PRIMARY KEY,
  url TEXT UNIQUE,
  local_path TEXT,
  size_bytes INTEGER,
  cached_at TIMESTAMP,
  last_used TIMESTAMP
);

CREATE TABLE pending_logs (
  id INTEGER PRIMARY KEY,
  content_id INTEGER,
  content_type TEXT,
  category TEXT,
  duration INTEGER,
  booking_id INTEGER,
  played_at TIMESTAMP
);
```

## Implémentation Flutter

Voici une classe complète pour un player Flutter :

```dart
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class AdScreenPlayer {
  final String baseUrl;
  String? accessToken;
  String? refreshToken;
  Map<String, dynamic>? screenInfo;
  List<Map<String, dynamic>> playlist = [];
  List<Map<String, dynamic>> overlays = [];
  int currentIndex = 0;
  Timer? heartbeatTimer;
  Timer? playlistTimer;

  AdScreenPlayer(this.baseUrl);

  // Initialisation depuis le stockage
  Future<bool> loadSavedSession() async {
    final prefs = await SharedPreferences.getInstance();
    accessToken = prefs.getString('access_token');
    refreshToken = prefs.getString('refresh_token');
    final screenJson = prefs.getString('screen_info');
    if (screenJson != null) {
      screenInfo = json.decode(screenJson);
    }
    return accessToken != null;
  }

  // Connexion
  Future<bool> login(String screenCode, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/mobile/api/v1/auth/screen-login'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'screen_code': screenCode,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      accessToken = data['access_token'];
      refreshToken = data['refresh_token'];
      screenInfo = data['screen'];
      await _saveSession();
      return true;
    }
    return false;
  }

  Future<void> _saveSession() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', accessToken!);
    await prefs.setString('refresh_token', refreshToken!);
    await prefs.setString('screen_info', json.encode(screenInfo));
  }

  // Headers d'authentification
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer $accessToken',
  };

  // Requête avec renouvellement automatique du token
  Future<http.Response> _request(String method, String endpoint, {Map<String, dynamic>? body}) async {
    var response = await _makeRequest(method, endpoint, body: body);
    
    if (response.statusCode == 401) {
      final refreshed = await _refreshToken();
      if (refreshed) {
        response = await _makeRequest(method, endpoint, body: body);
      }
    }
    
    return response;
  }

  Future<http.Response> _makeRequest(String method, String endpoint, {Map<String, dynamic>? body}) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    
    if (method == 'GET') {
      return http.get(uri, headers: _headers);
    } else {
      return http.post(uri, headers: _headers, body: json.encode(body));
    }
  }

  Future<bool> _refreshToken() async {
    final response = await http.post(
      Uri.parse('$baseUrl/mobile/api/v1/auth/refresh'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'refresh_token': refreshToken}),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      accessToken = data['access_token'];
      refreshToken = data['refresh_token'];
      await _saveSession();
      return true;
    }
    return false;
  }

  // Récupération du mode
  Future<String> getMode() async {
    final response = await _request('GET', '/mobile/api/v1/screen/mode');
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['mode'];
    }
    return 'playlist';
  }

  // Récupération de la playlist
  Future<void> fetchPlaylist() async {
    final response = await _request('GET', '/mobile/api/v1/screen/playlist');
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      playlist = List<Map<String, dynamic>>.from(data['playlist']);
      overlays = List<Map<String, dynamic>>.from(data['overlays'] ?? []);
      
      // Trier par priorité décroissante
      playlist.sort((a, b) => (b['priority'] as int).compareTo(a['priority'] as int));
    }
  }

  // Heartbeat
  Future<void> sendHeartbeat(String status) async {
    await _request('POST', '/mobile/api/v1/screen/heartbeat', body: {'status': status});
  }

  // Log de lecture
  Future<bool> logPlay(Map<String, dynamic> content) async {
    final response = await _request('POST', '/mobile/api/v1/screen/log-play', body: {
      'content_id': content['id'],
      'content_type': content['type'],
      'category': content['category'],
      'duration': content['duration'],
      'booking_id': content['booking_id'],
    });
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['exhausted'] == true;
    }
    return false;
  }

  // Démarrage du player
  void start() {
    // Heartbeat toutes les 30 secondes
    heartbeatTimer = Timer.periodic(Duration(seconds: 30), (_) {
      sendHeartbeat('playing');
    });

    // Rafraîchissement playlist toutes les 60 secondes
    playlistTimer = Timer.periodic(Duration(seconds: 60), (_) {
      fetchPlaylist();
    });

    // Première récupération
    fetchPlaylist();
  }

  // Arrêt du player
  void stop() {
    heartbeatTimer?.cancel();
    playlistTimer?.cancel();
  }

  // Contenu actuel
  Map<String, dynamic>? getCurrentContent() {
    if (playlist.isEmpty) return null;
    return playlist[currentIndex % playlist.length];
  }

  // Passer au contenu suivant
  void nextContent() {
    currentIndex++;
  }

  // Retirer un contenu épuisé
  void removeContent(Map<String, dynamic> content) {
    playlist.remove(content);
  }

  // Construire l'URL complète d'un média
  String getMediaUrl(String path) {
    if (path.startsWith('http')) return path;
    return '$baseUrl$path';
  }

  // Overlays actifs
  List<Map<String, dynamic>> getActiveOverlays() {
    return overlays.where((o) => o['active'] == true).toList()
      ..sort((a, b) => (b['priority'] as int).compareTo(a['priority'] as int));
  }
}
```

## Implémentation React Native

```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';

class AdScreenPlayer {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.accessToken = null;
    this.refreshToken = null;
    this.screenInfo = null;
    this.playlist = [];
    this.overlays = [];
    this.currentIndex = 0;
    this.heartbeatInterval = null;
    this.playlistInterval = null;
  }

  async loadSavedSession() {
    this.accessToken = await AsyncStorage.getItem('access_token');
    this.refreshToken = await AsyncStorage.getItem('refresh_token');
    const screenJson = await AsyncStorage.getItem('screen_info');
    if (screenJson) {
      this.screenInfo = JSON.parse(screenJson);
    }
    return this.accessToken != null;
  }

  async login(screenCode, password) {
    const response = await fetch(`${this.baseUrl}/mobile/api/v1/auth/screen-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ screen_code: screenCode, password }),
    });

    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;
      this.screenInfo = data.screen;
      await this.saveSession();
      return true;
    }
    return false;
  }

  async saveSession() {
    await AsyncStorage.setItem('access_token', this.accessToken);
    await AsyncStorage.setItem('refresh_token', this.refreshToken);
    await AsyncStorage.setItem('screen_info', JSON.stringify(this.screenInfo));
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.accessToken}`,
      ...options.headers,
    };

    let response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });

    if (response.status === 401) {
      const refreshed = await this.refreshTokens();
      if (refreshed) {
        headers.Authorization = `Bearer ${this.accessToken}`;
        response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });
      }
    }

    return response;
  }

  async refreshTokens() {
    const response = await fetch(`${this.baseUrl}/mobile/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;
      await this.saveSession();
      return true;
    }
    return false;
  }

  async fetchPlaylist() {
    const response = await this.request('/mobile/api/v1/screen/playlist');
    if (response.ok) {
      const data = await response.json();
      this.playlist = data.playlist;
      this.overlays = data.overlays || [];
      this.playlist.sort((a, b) => b.priority - a.priority);
    }
  }

  async sendHeartbeat(status = 'playing') {
    await this.request('/mobile/api/v1/screen/heartbeat', {
      method: 'POST',
      body: JSON.stringify({ status }),
    });
  }

  async logPlay(content) {
    const response = await this.request('/mobile/api/v1/screen/log-play', {
      method: 'POST',
      body: JSON.stringify({
        content_id: content.id,
        content_type: content.type,
        category: content.category,
        duration: content.duration,
        booking_id: content.booking_id,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      return data.exhausted === true;
    }
    return false;
  }

  start() {
    this.heartbeatInterval = setInterval(() => this.sendHeartbeat('playing'), 30000);
    this.playlistInterval = setInterval(() => this.fetchPlaylist(), 60000);
    this.fetchPlaylist();
  }

  stop() {
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
    if (this.playlistInterval) clearInterval(this.playlistInterval);
  }

  getCurrentContent() {
    if (this.playlist.length === 0) return null;
    return this.playlist[this.currentIndex % this.playlist.length];
  }

  nextContent() {
    this.currentIndex++;
  }

  removeContent(content) {
    const index = this.playlist.indexOf(content);
    if (index > -1) {
      this.playlist.splice(index, 1);
    }
  }

  getMediaUrl(path) {
    if (path.startsWith('http')) return path;
    return `${this.baseUrl}${path}`;
  }

  getActiveOverlays() {
    return this.overlays
      .filter(o => o.active)
      .sort((a, b) => b.priority - a.priority);
  }
}

export default AdScreenPlayer;
```

## Points importants

### Performance

- Préchargez les médias en arrière-plan pour éviter les latences
- Utilisez un cache LRU (Least Recently Used) pour limiter l'espace disque
- Compressez les images si nécessaire pour la résolution de l'écran

### Robustesse

- Gérez les coupures réseau gracieusement
- Stockez les logs en file d'attente quand hors ligne
- Redémarrez automatiquement après un crash

### Expérience utilisateur

- Affichez un écran de chargement pendant le téléchargement initial
- Montrez un indicateur quand la connexion est perdue
- Permettez de changer d'écran sans redémarrer l'application
