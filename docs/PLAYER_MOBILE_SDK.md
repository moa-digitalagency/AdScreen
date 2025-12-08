# Shabaka AdScreen - Guide de Developpement Player Mobile

Ce document fournit toutes les informations necessaires pour recoder le player d'ecran publicitaire en application mobile native (Android/iOS) tout en restant synchronise avec le backend.

## Table des matieres

1. [Architecture du Player](#architecture-du-player)
2. [Flux d'Authentification](#flux-dauthentification)
3. [Synchronisation des Donnees](#synchronisation-des-donnees)
4. [API Endpoints Player](#api-endpoints-player)
5. [Structure des Donnees](#structure-des-donnees)
6. [Logique de Lecture](#logique-de-lecture)
7. [Gestion des Overlays](#gestion-des-overlays)
8. [Mode IPTV](#mode-iptv)
9. [Gestion Hors-ligne](#gestion-hors-ligne)
10. [Implementation Flutter](#implementation-flutter)
11. [Implementation React Native](#implementation-react-native)
12. [Implementation iOS Swift](#implementation-ios-swift)

---

## Architecture du Player

```
+------------------+     +------------------+     +------------------+
|   Player Mobile  |<--->|   API Backend    |<--->|   Base Donnees   |
+------------------+     +------------------+     +------------------+
        |                        |
        v                        v
+------------------+     +------------------+
|  Cache Local     |     |  Fichiers Media  |
|  (IndexedDB/     |     |  (Images/Videos) |
|   SQLite)        |     +------------------+
+------------------+
```

### Composants Principaux

1. **Module Auth** - Gestion JWT tokens
2. **Module Playlist** - Recuperation et gestion du contenu
3. **Module Player** - Lecture media (images/videos)
4. **Module Overlay** - Affichage des bannieres/overlays
5. **Module Heartbeat** - Signalement d'activite
6. **Module Stats** - Enregistrement des lectures
7. **Module Cache** - Stockage hors-ligne

---

## Flux d'Authentification

### Sequence de Connexion

```
1. Utilisateur entre: code_ecran + mot_de_passe
2. POST /mobile/api/v1/auth/screen-login
3. Recevoir: access_token + refresh_token + infos_ecran
4. Stocker tokens de maniere securisee
5. Demarrer le player
```

### Gestion des Tokens

```
Token Expiration:
- Access Token: 24 heures
- Refresh Token: 30 jours

Flux de rafraichissement:
1. Requete retourne 401
2. POST /mobile/api/v1/auth/refresh avec refresh_token
3. Recevoir nouveaux tokens
4. Rejouer la requete originale
```

---

## Synchronisation des Donnees

### Intervalles Recommandes

| Operation | Intervalle | Description |
|-----------|------------|-------------|
| Heartbeat | 30 secondes | Signaler que le player est actif |
| Playlist | 60 secondes | Verifier les mises a jour de contenu |
| Log Play | Temps reel | Apres chaque lecture complete |

### Diagramme de Synchronisation

```
[Demarrage]
     |
     v
[Connexion JWT] --> [Erreur] --> [Afficher ecran login]
     |
     v
[Recuperer Playlist]
     |
     v
[Pre-telecharger Media] --> [Cache local]
     |
     v
[Boucle de Lecture]
     |
     +---> [Heartbeat toutes les 30s]
     |
     +---> [Rafraichir Playlist toutes les 60s]
     |
     +---> [Log Play apres chaque contenu]
     |
     v
[Verifier mode: playlist ou iptv]
     |
     +---> [Mode Playlist] --> [Lire contenu suivant]
     |
     +---> [Mode IPTV] --> [Lire flux HLS]
```

---

## API Endpoints Player

### POST /mobile/api/v1/auth/screen-login

Authentifie l'ecran et retourne les tokens JWT.

**Request:**
```json
{
  "screen_code": "ABC123",
  "password": "motdepasse"
}
```

**Response (200):**
```json
{
  "success": true,
  "screen": {
    "id": 1,
    "name": "Ecran Restaurant",
    "unique_code": "ABC123",
    "resolution": "1920x1080",
    "orientation": "landscape"
  },
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

---

### GET /mobile/api/v1/screen/mode

Retourne le mode actuel de l'ecran.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "mode": "playlist",
  "iptv_enabled": true,
  "iptv_channel_url": null,
  "iptv_channel_name": null,
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

---

### GET /mobile/api/v1/screen/playlist

Retourne la playlist complete avec overlays.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "screen": {
    "id": 1,
    "name": "Ecran Restaurant",
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
      "content": "Bienvenue dans notre etablissement!",
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
  "iptv": null,
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

---

### POST /mobile/api/v1/screen/heartbeat

Signale que l'ecran est actif.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "status": "playing"
}
```

**Status possibles:** `online`, `playing`, `paused`, `idle`, `error`

**Response:**
```json
{
  "success": true,
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

---

### POST /mobile/api/v1/screen/log-play

Enregistre une lecture de contenu pour les statistiques.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "content_id": 123,
  "content_type": "image",
  "category": "paid",
  "duration": 10,
  "booking_id": 45
}
```

**Response:**
```json
{
  "success": true,
  "exhausted": false
}
```

> **Note:** `exhausted: true` indique que le contenu a atteint son quota de lectures et sera retire de la playlist.

---

## Structure des Donnees

### Contenu (Content Item)

```typescript
interface ContentItem {
  id: number;
  type: 'image' | 'video';
  url: string;
  duration: number;        // secondes
  priority: number;        // 20-200
  category: 'paid' | 'internal' | 'filler' | 'broadcast' | 'ad_content';
  booking_id: number | null;
  remaining_plays: number | null;
  name: string;
}
```

### Priorites de Contenu

| Categorie | Priorite | Description |
|-----------|----------|-------------|
| broadcast | 200 | Diffusion superadmin (priorite max) |
| paid | 100 | Contenu client paye |
| internal | 80 | Contenu interne etablissement |
| ad_content | 60 | Publicites superadmin |
| filler | 20 | Contenu de remplissage |

### Overlay

```typescript
interface Overlay {
  id: number;
  type: 'scrolling_text' | 'static_image' | 'static_text';
  content: string;         // texte ou URL image
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
  speed?: number;          // pour scrolling_text
  opacity?: number;
}
```

---

## Logique de Lecture

### Algorithme de Selection

```python
def get_next_content(playlist, current_index):
    # 1. Trier par priorite decroissante
    sorted_playlist = sorted(playlist, key=lambda x: x['priority'], reverse=True)
    
    # 2. Filtrer les contenus epuises
    available = [c for c in sorted_playlist if c.get('remaining_plays', 1) > 0]
    
    # 3. Selection round-robin dans chaque groupe de priorite
    next_index = (current_index + 1) % len(available)
    
    return available[next_index]
```

### Gestion de la Duree

```
Pour images:
- Utiliser la duree specifiee dans l'item
- Defaut: 10 secondes

Pour videos:
- Utiliser la duree reelle de la video
- Ignorer la duree specifiee dans l'item
```

### Boucle de Lecture

```
1. Recuperer contenu suivant
2. Afficher/Lire le contenu
3. Attendre fin de duree/video
4. Envoyer log-play au backend
5. Verifier si contenu epuise
6. Retirer si epuise
7. Retour a l'etape 1
```

---

## Gestion des Overlays

### Affichage Simultane

Les overlays s'affichent par-dessus le contenu principal:

```
+----------------------------------+
|          [Overlay Top]           |
+----------------------------------+
|                                  |
|       CONTENU PRINCIPAL          |
|       (Image/Video/IPTV)         |
|                                  |
+----------------------------------+
|        [Overlay Bottom]          |
+----------------------------------+
```

### Priorite des Sources

```
BROADCAST > LOCAL

Si un overlay BROADCAST est actif:
- Mettre en pause les overlays LOCAL
- Afficher uniquement BROADCAST
- Reprendre LOCAL apres fin BROADCAST
```

### Types d'Overlay

1. **scrolling_text**: Texte defilant horizontalement
2. **static_image**: Image fixe (logo, QR code)
3. **static_text**: Texte fixe (annonces)

---

## Mode IPTV

Quand `mode == 'iptv'`:

```json
{
  "mode": "iptv",
  "iptv": {
    "url": "https://stream.example.com/live.m3u8",
    "name": "Chaine Info"
  },
  "playlist": [],
  "overlays": [...]
}
```

### Implementation HLS

```javascript
// Utiliser HLS.js ou ExoPlayer/AVPlayer natif
if (mode === 'iptv' && iptv.url) {
  // Arreter playlist
  // Demarrer flux HLS
  // Afficher overlays par-dessus
}
```

---

## Gestion Hors-ligne

### Strategie de Cache

```
1. Pre-telecharger tous les medias de la playlist
2. Stocker dans le cache local (SQLite/IndexedDB)
3. Servir depuis le cache si hors-ligne
4. Mettre en queue les log-play
5. Synchroniser a la reconnexion
```

### Schema de Cache

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

---

## Implementation Flutter

### Classe AdScreenPlayer

```dart
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:video_player/video_player.dart';

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

  // === AUTHENTIFICATION ===
  
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
      await _saveTokens();
      return true;
    }
    return false;
  }

  Future<void> _saveTokens() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', accessToken!);
    await prefs.setString('refresh_token', refreshToken!);
    await prefs.setString('screen_info', json.encode(screenInfo));
  }

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

  Map<String, String> get _authHeaders => {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer $accessToken',
  };

  Future<http.Response> _authenticatedRequest(
    String method,
    String endpoint, {
    Map<String, dynamic>? body,
  }) async {
    var response = await _makeRequest(method, endpoint, body: body);
    
    if (response.statusCode == 401) {
      final refreshed = await _refreshToken();
      if (refreshed) {
        response = await _makeRequest(method, endpoint, body: body);
      }
    }
    
    return response;
  }

  Future<http.Response> _makeRequest(
    String method,
    String endpoint, {
    Map<String, dynamic>? body,
  }) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    
    switch (method) {
      case 'GET':
        return http.get(uri, headers: _authHeaders);
      case 'POST':
        return http.post(uri, headers: _authHeaders, body: json.encode(body));
      default:
        throw Exception('Unsupported method');
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
      await _saveTokens();
      return true;
    }
    return false;
  }

  // === SYNCHRONISATION ===

  Future<String> getMode() async {
    final response = await _authenticatedRequest('GET', '/mobile/api/v1/screen/mode');
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['mode'];
    }
    return 'playlist';
  }

  Future<void> fetchPlaylist() async {
    final response = await _authenticatedRequest('GET', '/mobile/api/v1/screen/playlist');
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      playlist = List<Map<String, dynamic>>.from(data['playlist']);
      overlays = List<Map<String, dynamic>>.from(data['overlays'] ?? []);
      
      // Trier par priorite
      playlist.sort((a, b) => (b['priority'] as int).compareTo(a['priority'] as int));
    }
  }

  Future<void> sendHeartbeat(String status) async {
    await _authenticatedRequest('POST', '/mobile/api/v1/screen/heartbeat', 
      body: {'status': status});
  }

  Future<bool> logPlay(Map<String, dynamic> content) async {
    final response = await _authenticatedRequest('POST', '/mobile/api/v1/screen/log-play',
      body: {
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

  // === LECTURE ===

  void startPlayer() {
    // Demarrer heartbeat toutes les 30s
    heartbeatTimer = Timer.periodic(Duration(seconds: 30), (_) {
      sendHeartbeat('playing');
    });

    // Rafraichir playlist toutes les 60s
    playlistTimer = Timer.periodic(Duration(seconds: 60), (_) {
      fetchPlaylist();
    });

    // Premiere recuperation
    fetchPlaylist().then((_) => _playNext());
  }

  void stopPlayer() {
    heartbeatTimer?.cancel();
    playlistTimer?.cancel();
  }

  Map<String, dynamic>? getCurrentContent() {
    if (playlist.isEmpty) return null;
    return playlist[currentIndex % playlist.length];
  }

  Future<void> _playNext() async {
    if (playlist.isEmpty) {
      await Future.delayed(Duration(seconds: 5));
      _playNext();
      return;
    }

    final content = getCurrentContent()!;
    
    // Attendre la duree du contenu
    if (content['type'] == 'image') {
      await Future.delayed(Duration(seconds: content['duration'] ?? 10));
    }
    // Pour video, attendre la fin de la video (gere par VideoPlayerController)

    // Logger la lecture
    final exhausted = await logPlay(content);
    
    // Retirer si epuise
    if (exhausted) {
      playlist.removeAt(currentIndex % playlist.length);
    } else {
      currentIndex++;
    }

    // Continuer la lecture
    _playNext();
  }

  // === OVERLAYS ===

  List<Map<String, dynamic>> getActiveOverlays() {
    return overlays.where((o) => o['active'] == true).toList()
      ..sort((a, b) => (b['priority'] as int).compareTo(a['priority'] as int));
  }

  String getMediaUrl(String path) {
    if (path.startsWith('http')) return path;
    return '$baseUrl$path';
  }
}
```

### Widget Player Flutter

```dart
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:cached_network_image/cached_network_image.dart';

class PlayerScreen extends StatefulWidget {
  final AdScreenPlayer player;

  const PlayerScreen({Key? key, required this.player}) : super(key: key);

  @override
  _PlayerScreenState createState() => _PlayerScreenState();
}

class _PlayerScreenState extends State<PlayerScreen> {
  VideoPlayerController? _videoController;
  Map<String, dynamic>? _currentContent;

  @override
  void initState() {
    super.initState();
    widget.player.startPlayer();
    _startPlaybackLoop();
  }

  @override
  void dispose() {
    widget.player.stopPlayer();
    _videoController?.dispose();
    super.dispose();
  }

  void _startPlaybackLoop() async {
    while (mounted) {
      await widget.player.fetchPlaylist();
      
      final content = widget.player.getCurrentContent();
      if (content == null) {
        await Future.delayed(Duration(seconds: 5));
        continue;
      }

      setState(() => _currentContent = content);

      if (content['type'] == 'video') {
        await _playVideo(content);
      } else {
        await Future.delayed(Duration(seconds: content['duration'] ?? 10));
      }

      final exhausted = await widget.player.logPlay(content);
      if (exhausted) {
        widget.player.playlist.remove(content);
      } else {
        widget.player.currentIndex++;
      }
    }
  }

  Future<void> _playVideo(Map<String, dynamic> content) async {
    final url = widget.player.getMediaUrl(content['url']);
    _videoController = VideoPlayerController.network(url);
    await _videoController!.initialize();
    await _videoController!.play();
    
    // Attendre fin de video
    await _videoController!.position.then((pos) async {
      while (_videoController!.value.isPlaying) {
        await Future.delayed(Duration(milliseconds: 500));
      }
    });
    
    _videoController!.dispose();
    _videoController = null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Contenu principal
          Center(child: _buildMainContent()),
          
          // Overlays
          ..._buildOverlays(),
        ],
      ),
    );
  }

  Widget _buildMainContent() {
    if (_currentContent == null) {
      return CircularProgressIndicator(color: Colors.white);
    }

    if (_currentContent!['type'] == 'video' && _videoController != null) {
      return AspectRatio(
        aspectRatio: _videoController!.value.aspectRatio,
        child: VideoPlayer(_videoController!),
      );
    }

    return CachedNetworkImage(
      imageUrl: widget.player.getMediaUrl(_currentContent!['url']),
      fit: BoxFit.contain,
      placeholder: (context, url) => CircularProgressIndicator(),
      errorWidget: (context, url, error) => Icon(Icons.error, color: Colors.red),
    );
  }

  List<Widget> _buildOverlays() {
    final activeOverlays = widget.player.getActiveOverlays();
    return activeOverlays.map((overlay) {
      switch (overlay['position']) {
        case 'top':
          return Positioned(top: 0, left: 0, right: 0, child: _buildOverlay(overlay));
        case 'bottom':
          return Positioned(bottom: 0, left: 0, right: 0, child: _buildOverlay(overlay));
        default:
          return SizedBox.shrink();
      }
    }).toList();
  }

  Widget _buildOverlay(Map<String, dynamic> overlay) {
    final style = overlay['style'] ?? {};
    final bgColor = _parseColor(style['background_color'] ?? '#000000');
    final textColor = _parseColor(style['text_color'] ?? '#FFFFFF');
    final fontSize = (style['font_size'] ?? 24).toDouble();

    if (overlay['type'] == 'scrolling_text') {
      return Container(
        color: bgColor.withOpacity(0.8),
        height: fontSize + 20,
        child: Marquee(
          text: overlay['content'],
          style: TextStyle(color: textColor, fontSize: fontSize),
          scrollAxis: Axis.horizontal,
          velocity: (style['speed'] ?? 50).toDouble(),
        ),
      );
    }

    return Container(
      color: bgColor.withOpacity(0.8),
      padding: EdgeInsets.all(10),
      child: Text(
        overlay['content'],
        style: TextStyle(color: textColor, fontSize: fontSize),
        textAlign: TextAlign.center,
      ),
    );
  }

  Color _parseColor(String hex) {
    return Color(int.parse(hex.replaceFirst('#', '0xFF')));
  }
}
```

---

## Implementation React Native

### Classe PlayerService

```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';

class PlayerService {
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

  // === AUTH ===

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
    await AsyncStorage.setItem('player_session', JSON.stringify({
      accessToken: this.accessToken,
      refreshToken: this.refreshToken,
      screenInfo: this.screenInfo,
    }));
  }

  async loadSession() {
    const session = await AsyncStorage.getItem('player_session');
    if (session) {
      const data = JSON.parse(session);
      this.accessToken = data.accessToken;
      this.refreshToken = data.refreshToken;
      this.screenInfo = data.screenInfo;
      return true;
    }
    return false;
  }

  async authenticatedFetch(endpoint, options = {}) {
    let response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.accessToken}`,
        ...options.headers,
      },
    });

    if (response.status === 401) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        response = await fetch(`${this.baseUrl}${endpoint}`, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.accessToken}`,
            ...options.headers,
          },
        });
      }
    }

    return response;
  }

  async refreshAccessToken() {
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

  // === SYNC ===

  async fetchPlaylist() {
    const response = await this.authenticatedFetch('/mobile/api/v1/screen/playlist');
    if (response.ok) {
      const data = await response.json();
      this.playlist = data.playlist || [];
      this.overlays = data.overlays || [];
      this.playlist.sort((a, b) => b.priority - a.priority);
      return data;
    }
    return null;
  }

  async sendHeartbeat(status = 'playing') {
    await this.authenticatedFetch('/mobile/api/v1/screen/heartbeat', {
      method: 'POST',
      body: JSON.stringify({ status }),
    });
  }

  async logPlay(content) {
    const response = await this.authenticatedFetch('/mobile/api/v1/screen/log-play', {
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
      return data.exhausted;
    }
    return false;
  }

  // === PLAYER ===

  startSync() {
    this.heartbeatInterval = setInterval(() => this.sendHeartbeat('playing'), 30000);
    this.playlistInterval = setInterval(() => this.fetchPlaylist(), 60000);
  }

  stopSync() {
    clearInterval(this.heartbeatInterval);
    clearInterval(this.playlistInterval);
  }

  getCurrentContent() {
    if (this.playlist.length === 0) return null;
    return this.playlist[this.currentIndex % this.playlist.length];
  }

  nextContent() {
    this.currentIndex++;
  }

  removeExhausted(content) {
    this.playlist = this.playlist.filter(c => c.id !== content.id);
  }

  getMediaUrl(path) {
    if (path.startsWith('http')) return path;
    return `${this.baseUrl}${path}`;
  }

  getActiveOverlays() {
    return this.overlays
      .filter(o => o.active !== false)
      .sort((a, b) => b.priority - a.priority);
  }
}

export default PlayerService;
```

---

## Implementation iOS Swift

### Classe AdScreenPlayer

```swift
import Foundation

class AdScreenPlayer: ObservableObject {
    let baseUrl: String
    
    @Published var accessToken: String?
    @Published var refreshToken: String?
    @Published var screenInfo: ScreenInfo?
    @Published var playlist: [ContentItem] = []
    @Published var overlays: [Overlay] = []
    @Published var currentIndex: Int = 0
    
    private var heartbeatTimer: Timer?
    private var playlistTimer: Timer?
    
    init(baseUrl: String) {
        self.baseUrl = baseUrl
    }
    
    // MARK: - Auth
    
    func login(screenCode: String, password: String) async throws -> Bool {
        let url = URL(string: "\(baseUrl)/mobile/api/v1/auth/screen-login")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode([
            "screen_code": screenCode,
            "password": password
        ])
        
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            return false
        }
        
        let loginResponse = try JSONDecoder().decode(LoginResponse.self, from: data)
        
        DispatchQueue.main.async {
            self.accessToken = loginResponse.accessToken
            self.refreshToken = loginResponse.refreshToken
            self.screenInfo = loginResponse.screen
        }
        
        saveSession()
        return true
    }
    
    private func saveSession() {
        UserDefaults.standard.set(accessToken, forKey: "access_token")
        UserDefaults.standard.set(refreshToken, forKey: "refresh_token")
    }
    
    func loadSession() -> Bool {
        accessToken = UserDefaults.standard.string(forKey: "access_token")
        refreshToken = UserDefaults.standard.string(forKey: "refresh_token")
        return accessToken != nil
    }
    
    // MARK: - API
    
    func fetchPlaylist() async throws {
        guard let token = accessToken else { return }
        
        let url = URL(string: "\(baseUrl)/mobile/api/v1/screen/playlist")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(PlaylistResponse.self, from: data)
        
        DispatchQueue.main.async {
            self.playlist = response.playlist.sorted { $0.priority > $1.priority }
            self.overlays = response.overlays ?? []
        }
    }
    
    func sendHeartbeat(status: String = "playing") async {
        guard let token = accessToken else { return }
        
        let url = URL(string: "\(baseUrl)/mobile/api/v1/screen/heartbeat")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.httpBody = try? JSONEncoder().encode(["status": status])
        
        _ = try? await URLSession.shared.data(for: request)
    }
    
    func logPlay(content: ContentItem) async -> Bool {
        guard let token = accessToken else { return false }
        
        let url = URL(string: "\(baseUrl)/mobile/api/v1/screen/log-play")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let body: [String: Any] = [
            "content_id": content.id,
            "content_type": content.type,
            "category": content.category,
            "duration": content.duration,
            "booking_id": content.bookingId as Any
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        let (data, _) = try! await URLSession.shared.data(for: request)
        let response = try? JSONDecoder().decode(LogPlayResponse.self, from: data)
        return response?.exhausted ?? false
    }
    
    // MARK: - Player Control
    
    func startPlayer() {
        heartbeatTimer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { _ in
            Task { await self.sendHeartbeat() }
        }
        
        playlistTimer = Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { _ in
            Task { try? await self.fetchPlaylist() }
        }
    }
    
    func stopPlayer() {
        heartbeatTimer?.invalidate()
        playlistTimer?.invalidate()
    }
    
    func getCurrentContent() -> ContentItem? {
        guard !playlist.isEmpty else { return nil }
        return playlist[currentIndex % playlist.count]
    }
    
    func getMediaUrl(_ path: String) -> URL {
        if path.hasPrefix("http") {
            return URL(string: path)!
        }
        return URL(string: "\(baseUrl)\(path)")!
    }
}

// MARK: - Models

struct LoginResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let screen: ScreenInfo
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case screen
    }
}

struct ScreenInfo: Codable {
    let id: Int
    let name: String
    let uniqueCode: String
    let resolution: String
    let orientation: String
    
    enum CodingKeys: String, CodingKey {
        case id, name, resolution, orientation
        case uniqueCode = "unique_code"
    }
}

struct PlaylistResponse: Codable {
    let playlist: [ContentItem]
    let overlays: [Overlay]?
}

struct ContentItem: Codable, Identifiable {
    let id: Int
    let type: String
    let url: String
    let duration: Int
    let priority: Int
    let category: String
    let bookingId: Int?
    let remainingPlays: Int?
    let name: String
    
    enum CodingKeys: String, CodingKey {
        case id, type, url, duration, priority, category, name
        case bookingId = "booking_id"
        case remainingPlays = "remaining_plays"
    }
}

struct Overlay: Codable, Identifiable {
    let id: Int
    let type: String
    let content: String
    let position: String
    let priority: Int
    let source: String
}

struct LogPlayResponse: Codable {
    let success: Bool
    let exhausted: Bool
}
```

---

## Bonnes Pratiques

### Performance

1. **Pre-chargement**: Telecharger les 3-5 prochains contenus a l'avance
2. **Cache agressif**: Stocker tous les medias localement
3. **Compression**: Utiliser des formats optimises (WebP, H.265)

### Fiabilite

1. **Retry automatique**: 3 tentatives avec backoff exponentiel
2. **Queue hors-ligne**: Stocker les logs en local si pas de reseau
3. **Watchdog**: Redemarrer le player si bloque

### Securite

1. **Stockage securise**: Keychain (iOS) / Keystore (Android) pour tokens
2. **Certificate Pinning**: En production
3. **Pas de logs sensibles**: Ne jamais logger les tokens

---

*Documentation Player Mobile SDK v1.0*
*Generee le 2024-01-15*
