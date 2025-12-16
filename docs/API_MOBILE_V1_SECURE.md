# API Mobile sécurisée v1

Cette version de l'API utilise JWT (JSON Web Tokens) pour l'authentification et intègre une protection contre les abus (rate limiting).

## Pourquoi cette version ?

L'API classique utilise des cookies de session, ce qui fonctionne bien pour les navigateurs mais pose des problèmes sur mobile :
- Les cookies sont difficiles à gérer sur certaines plateformes
- La session peut expirer de façon imprévisible
- Pas de mécanisme standard de renouvellement

L'API v1 sécurisée résout ces problèmes avec des tokens JWT :
- Stockage simple (chaîne de caractères)
- Expiration prévisible (24h pour l'access token)
- Renouvellement automatique avec le refresh token

## URL de base

```
/mobile/api/v1/
```

## Authentification

### Comment ça marche

1. L'application appelle `/auth/login` ou `/auth/screen-login`
2. Le serveur retourne deux tokens : `access_token` et `refresh_token`
3. L'application stocke ces tokens de manière sécurisée
4. Chaque requête inclut l'access token dans le header `Authorization`
5. Quand l'access token expire, l'application utilise le refresh token pour en obtenir un nouveau

### Durée de vie des tokens

| Token | Durée | Usage |
|-------|-------|-------|
| Access token | 24 heures | Accès aux endpoints protégés |
| Refresh token | 30 jours | Obtention d'un nouveau access token |

### Connecter un utilisateur

```
POST /mobile/api/v1/auth/login
Content-Type: application/json

{
  "email": "manager@restaurant.fr",
  "password": "motdepasse"
}
```

Retourne :

```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "manager@restaurant.fr",
    "role": "admin",
    "organization_id": 1
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### Connecter un écran

```
POST /mobile/api/v1/auth/screen-login
Content-Type: application/json

{
  "screen_code": "ABC123",
  "password": "screen123"
}
```

Retourne :

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
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### Renouveler le token

Quand l'access token expire (erreur 401), utilisez le refresh token :

```
POST /mobile/api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

Retourne de nouveaux tokens :

```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

## Rate limiting

Pour protéger le serveur contre les abus, chaque endpoint a une limite de requêtes par minute.

| Catégorie | Endpoint | Limite |
|-----------|----------|--------|
| Authentification | /auth/login | 5/min |
| Authentification | /auth/screen-login | 5/min |
| Authentification | /auth/refresh | 10/min |
| Player | /screen/playlist | 60/min |
| Player | /screen/heartbeat | 120/min |
| Player | /screen/log-play | 120/min |
| Dashboard | /dashboard/* | 100/min |

Si vous dépassez la limite, vous recevez une erreur 429 :

```json
{
  "error": "Too many requests. Please slow down.",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": "60 seconds"
}
```

Attendez le délai indiqué avant de réessayer.

## Endpoints écran

Tous ces endpoints nécessitent un token écran dans le header :

```http
Authorization: Bearer <access_token>
```

### Récupérer le mode

```
GET /mobile/api/v1/screen/mode
```

Retourne :

```json
{
  "mode": "playlist",
  "iptv_enabled": true,
  "iptv_channel_url": null,
  "iptv_channel_name": null,
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

### Récupérer la playlist

```
GET /mobile/api/v1/screen/playlist
```

Retourne :

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
    }
  ],
  "overlays": [],
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

### Envoyer un heartbeat

```
POST /mobile/api/v1/screen/heartbeat
Content-Type: application/json

{
  "status": "playing"
}
```

### Enregistrer une diffusion

```
POST /mobile/api/v1/screen/log-play
Content-Type: application/json

{
  "content_id": 123,
  "content_type": "image",
  "category": "paid",
  "duration": 10,
  "booking_id": 45
}
```

Retourne :

```json
{
  "success": true,
  "exhausted": false
}
```

## Endpoints dashboard

Ces endpoints nécessitent un token utilisateur.

### Liste des écrans

```
GET /mobile/api/v1/dashboard/screens
```

Retourne :

```json
{
  "screens": [
    {
      "id": 1,
      "name": "Écran Restaurant",
      "unique_code": "ABC123",
      "status": "playing",
      "last_heartbeat": "2024-01-15T14:30:00.000000",
      "is_active": true,
      "current_mode": "playlist",
      "resolution": "1920x1080",
      "orientation": "landscape"
    }
  ],
  "total": 1
}
```

### Statistiques d'un écran

```
GET /mobile/api/v1/dashboard/screen/1/stats?days=7
```

Retourne :

```json
{
  "screen_id": 1,
  "period_days": 7,
  "daily_plays": [
    {"date": "2024-01-08", "count": 450},
    {"date": "2024-01-09", "count": 523}
  ],
  "category_stats": [
    {"category": "paid", "count": 1250},
    {"category": "internal", "count": 890}
  ],
  "total_plays": 973
}
```

### Résumé global

```
GET /mobile/api/v1/dashboard/summary
```

Retourne :

```json
{
  "total_screens": 5,
  "online_screens": 3,
  "pending_contents": 2,
  "total_revenue": 1250.50
}
```

## Endpoint santé

Pour vérifier que l'API fonctionne, sans authentification :

```
GET /mobile/api/v1/health
```

Retourne :

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000000",
  "version": "1.0"
}
```

## Codes d'erreur

### Erreurs d'authentification

| Code | HTTP | Signification |
|------|------|---------------|
| TOKEN_MISSING | 401 | Header Authorization absent |
| TOKEN_INVALID | 401 | Token expiré ou invalide |
| INVALID_TOKEN_TYPE | 401 | Mauvais type de token |
| INVALID_CREDENTIALS | 401 | Email ou mot de passe incorrect |
| ACCOUNT_DISABLED | 403 | Compte désactivé |
| SCREEN_DISABLED | 403 | Écran désactivé |

### Erreurs de validation

| Code | HTTP | Signification |
|------|------|---------------|
| INVALID_CONTENT_TYPE | 400 | Content-Type doit être JSON |
| INVALID_JSON | 400 | Corps de requête mal formé |
| MISSING_FIELDS | 400 | Champs requis manquants |

### Erreurs système

| Code | HTTP | Signification |
|------|------|---------------|
| RATE_LIMIT_EXCEEDED | 429 | Trop de requêtes |
| SCREEN_NOT_FOUND | 404 | Écran non trouvé |
| USER_NOT_FOUND | 404 | Utilisateur non trouvé |

## Exemple Flutter complet

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class SecureAdScreenApi {
  final String baseUrl;
  String? accessToken;
  String? refreshToken;

  SecureAdScreenApi(this.baseUrl);

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    accessToken = prefs.getString('access_token');
    refreshToken = prefs.getString('refresh_token');
  }

  Future<void> _saveTokens(Map<String, dynamic> data) async {
    final prefs = await SharedPreferences.getInstance();
    accessToken = data['access_token'];
    refreshToken = data['refresh_token'];
    await prefs.setString('access_token', accessToken!);
    await prefs.setString('refresh_token', refreshToken!);
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer $accessToken',
  };

  Future<Map<String, dynamic>> loginScreen(String screenCode, String password) async {
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
      await _saveTokens(data);
      return data;
    }
    throw Exception(json.decode(response.body)['error']);
  }

  Future<void> _refreshAccessToken() async {
    final response = await http.post(
      Uri.parse('$baseUrl/mobile/api/v1/auth/refresh'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'refresh_token': refreshToken}),
    );

    if (response.statusCode == 200) {
      await _saveTokens(json.decode(response.body));
    } else {
      throw Exception('Session expirée');
    }
  }

  Future<http.Response> _request(String method, String endpoint, {Map<String, dynamic>? body}) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    http.Response response;

    if (method == 'GET') {
      response = await http.get(uri, headers: _headers);
    } else {
      response = await http.post(uri, headers: _headers, body: json.encode(body));
    }

    if (response.statusCode == 401) {
      await _refreshAccessToken();
      if (method == 'GET') {
        response = await http.get(uri, headers: _headers);
      } else {
        response = await http.post(uri, headers: _headers, body: json.encode(body));
      }
    }

    return response;
  }

  Future<Map<String, dynamic>> getPlaylist() async {
    final response = await _request('GET', '/mobile/api/v1/screen/playlist');
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Impossible de récupérer la playlist');
  }

  Future<void> sendHeartbeat(String status) async {
    await _request('POST', '/mobile/api/v1/screen/heartbeat', body: {'status': status});
  }

  Future<Map<String, dynamic>> logPlay({
    required int contentId,
    required String contentType,
    required String category,
    required int duration,
    int? bookingId,
  }) async {
    final response = await _request('POST', '/mobile/api/v1/screen/log-play', body: {
      'content_id': contentId,
      'content_type': contentType,
      'category': category,
      'duration': duration,
      'booking_id': bookingId,
    });
    return json.decode(response.body);
  }
}
```

## Exemple React Native complet

```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';

class SecureAdScreenClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.accessToken = null;
    this.refreshToken = null;
  }

  async init() {
    this.accessToken = await AsyncStorage.getItem('access_token');
    this.refreshToken = await AsyncStorage.getItem('refresh_token');
  }

  async saveTokens(data) {
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;
    await AsyncStorage.setItem('access_token', data.access_token);
    await AsyncStorage.setItem('refresh_token', data.refresh_token);
  }

  async loginScreen(screenCode, password) {
    const response = await fetch(`${this.baseUrl}/mobile/api/v1/auth/screen-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ screen_code: screenCode, password }),
    });

    const data = await response.json();
    if (response.ok) {
      await this.saveTokens(data);
      return data;
    }
    throw new Error(data.error);
  }

  async refreshAccessToken() {
    const response = await fetch(`${this.baseUrl}/mobile/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      await this.saveTokens(data);
    } else {
      throw new Error('Session expirée');
    }
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.accessToken}`,
      ...options.headers,
    };

    let response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });

    if (response.status === 401) {
      await this.refreshAccessToken();
      headers.Authorization = `Bearer ${this.accessToken}`;
      response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });
    }

    return response;
  }

  async getPlaylist() {
    const response = await this.request('/mobile/api/v1/screen/playlist');
    return response.json();
  }

  async sendHeartbeat(status = 'playing') {
    await this.request('/mobile/api/v1/screen/heartbeat', {
      method: 'POST',
      body: JSON.stringify({ status }),
    });
  }

  async logPlay({ contentId, contentType, category, duration, bookingId = null }) {
    const response = await this.request('/mobile/api/v1/screen/log-play', {
      method: 'POST',
      body: JSON.stringify({
        content_id: contentId,
        content_type: contentType,
        category: category,
        duration: duration,
        booking_id: bookingId,
      }),
    });
    return response.json();
  }
}

export default SecureAdScreenClient;
```

## Bonnes pratiques

### Stockage des tokens

- Sur iOS : utilisez le Keychain
- Sur Android : utilisez le Keystore ou EncryptedSharedPreferences
- Ne stockez jamais les tokens en clair dans les logs

### Gestion des erreurs 401

1. Interceptez les erreurs 401
2. Tentez de renouveler le token avec le refresh token
3. Si le renouvellement échoue, redirigez vers l'écran de connexion
4. Effacez les tokens stockés

### Rate limiting

- Implémentez un backoff exponentiel en cas de 429
- Cachez les réponses quand c'est possible
- Regroupez les requêtes similaires

### HTTPS

En production, utilisez toujours HTTPS. Les tokens JWT passent en clair dans les headers et doivent être protégés.
