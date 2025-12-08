# Shabaka AdScreen - API Mobile Securisee v1

## Table des matieres

1. [Introduction](#introduction)
2. [Securite](#securite)
3. [Authentification JWT](#authentification-jwt)
4. [Rate Limiting](#rate-limiting)
5. [Endpoints API Mobile](#endpoints-api-mobile)
6. [Codes d'Erreur](#codes-derreur)
7. [Exemples d'Integration](#exemples-dintegration)

---

## Introduction

Cette API securisee utilise **JWT (JSON Web Tokens)** pour l'authentification et integre le **rate limiting** pour proteger contre les abus.

### URL de Base

```
/mobile/api/v1/
```

### Caracteristiques de Securite

- Authentification JWT avec tokens d'acces et de rafraichissement
- Rate limiting par IP
- Validation stricte des entrees
- Protection CSRF pour les endpoints non-API
- HTTPS obligatoire en production

---

## Securite

### Headers Requis

```http
Content-Type: application/json
Authorization: Bearer <access_token>
```

### Tokens JWT

| Type | Duree de Validite | Usage |
|------|-------------------|-------|
| Access Token | 24 heures | Acces aux endpoints proteges |
| Refresh Token | 30 jours | Obtention d'un nouveau access token |

### Flux d'Authentification

```
1. POST /mobile/api/v1/auth/login ou /auth/screen-login
   -> Retourne access_token + refresh_token

2. Utiliser access_token dans le header Authorization
   -> Authorization: Bearer <access_token>

3. Quand access_token expire:
   POST /mobile/api/v1/auth/refresh
   -> Retourne nouveau access_token + refresh_token
```

---

## Authentification JWT

### Connexion Utilisateur

#### POST /mobile/api/v1/auth/login

Authentifie un utilisateur et retourne les tokens JWT.

**Rate Limit:** 5 requetes/minute

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "motdepasse"
}
```

**Response Success (200):**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "user@example.com",
    "role": "admin",
    "organization_id": 1
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

**Response Error (401):**
```json
{
  "error": "Invalid email or password",
  "code": "INVALID_CREDENTIALS"
}
```

---

### Connexion Ecran

#### POST /mobile/api/v1/auth/screen-login

Authentifie un ecran et retourne les tokens JWT.

**Rate Limit:** 5 requetes/minute

**Request Body:**
```json
{
  "screen_code": "ABC123",
  "password": "motdepasse"
}
```

**Response Success (200):**
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
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

---

### Rafraichir le Token

#### POST /mobile/api/v1/auth/refresh

Obtient un nouveau access token avec le refresh token.

**Rate Limit:** 10 requetes/minute

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response Success (200):**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

---

## Rate Limiting

### Limites par Categorie

| Categorie | Endpoint | Limite |
|-----------|----------|--------|
| Auth | /auth/login | 5/minute |
| Auth | /auth/screen-login | 5/minute |
| Auth | /auth/refresh | 10/minute |
| Player | /screen/playlist | 60/minute |
| Player | /screen/heartbeat | 120/minute |
| Player | /screen/log-play | 120/minute |
| Dashboard | /dashboard/* | 100/minute |

### Response Rate Limit Exceeded (429)

```json
{
  "error": "Too many requests. Please slow down.",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": "60 seconds"
}
```

---

## Endpoints API Mobile

### Endpoints Ecran (Screen JWT Required)

#### GET /mobile/api/v1/screen/mode

Retourne le mode actuel de l'ecran.

**Headers:**
```http
Authorization: Bearer <screen_access_token>
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

#### GET /mobile/api/v1/screen/playlist

Retourne la playlist complete.

**Headers:**
```http
Authorization: Bearer <screen_access_token>
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
    }
  ],
  "overlays": [],
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

---

#### POST /mobile/api/v1/screen/heartbeat

Signale que l'ecran est actif.

**Headers:**
```http
Authorization: Bearer <screen_access_token>
```

**Request Body:**
```json
{
  "status": "playing"
}
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

---

#### POST /mobile/api/v1/screen/log-play

Enregistre une diffusion de contenu.

**Headers:**
```http
Authorization: Bearer <screen_access_token>
```

**Request Body:**
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

---

### Endpoints Dashboard (User JWT Required)

#### GET /mobile/api/v1/dashboard/screens

Liste tous les ecrans de l'utilisateur.

**Headers:**
```http
Authorization: Bearer <user_access_token>
```

**Response:**
```json
{
  "screens": [
    {
      "id": 1,
      "name": "Ecran Restaurant",
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

---

#### GET /mobile/api/v1/dashboard/screen/{screen_id}/stats

Statistiques d'un ecran.

**Headers:**
```http
Authorization: Bearer <user_access_token>
```

**Query Parameters:**
| Parametre | Type | Default | Description |
|-----------|------|---------|-------------|
| days | integer | 7 | Nombre de jours (1-90) |

**Response:**
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

---

#### GET /mobile/api/v1/dashboard/summary

Resume global du dashboard.

**Headers:**
```http
Authorization: Bearer <user_access_token>
```

**Response:**
```json
{
  "total_screens": 5,
  "online_screens": 3,
  "pending_contents": 2,
  "total_revenue": 1250.50
}
```

---

### Endpoint Public

#### GET /mobile/api/v1/health

Verifie l'etat de l'API.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000000",
  "version": "1.0"
}
```

---

## Codes d'Erreur

### Codes d'Authentification

| Code | HTTP | Description |
|------|------|-------------|
| TOKEN_MISSING | 401 | Token d'autorisation manquant |
| TOKEN_INVALID | 401 | Token invalide ou expire |
| INVALID_TOKEN_TYPE | 401 | Type de token incorrect |
| INVALID_CREDENTIALS | 401 | Email/mot de passe incorrect |
| ACCOUNT_DISABLED | 403 | Compte desactive |
| SCREEN_DISABLED | 403 | Ecran desactive |
| SCREEN_TOKEN_REQUIRED | 403 | Token ecran requis |
| USER_TOKEN_REQUIRED | 403 | Token utilisateur requis |
| SUPERADMIN_REQUIRED | 403 | Acces superadmin requis |

### Codes de Validation

| Code | HTTP | Description |
|------|------|-------------|
| INVALID_CONTENT_TYPE | 400 | Content-Type doit etre JSON |
| INVALID_JSON | 400 | Corps JSON invalide |
| MISSING_FIELDS | 400 | Champs requis manquants |
| VALIDATION_ERROR | 400 | Erreur de validation |

### Codes Systeme

| Code | HTTP | Description |
|------|------|-------------|
| RATE_LIMIT_EXCEEDED | 429 | Trop de requetes |
| SCREEN_NOT_FOUND | 404 | Ecran non trouve |
| USER_NOT_FOUND | 404 | Utilisateur non trouve |

---

## Exemples d'Integration

### Flutter/Dart - Client Complet

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';
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

  Future<void> _saveTokens(Map<String, dynamic> tokens) async {
    final prefs = await SharedPreferences.getInstance();
    accessToken = tokens['access_token'];
    refreshToken = tokens['refresh_token'];
    await prefs.setString('access_token', accessToken!);
    await prefs.setString('refresh_token', refreshToken!);
  }

  Map<String, String> get _authHeaders => {
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
      throw Exception('Session expired');
    }
  }

  Future<http.Response> _authenticatedRequest(
    String method,
    String endpoint,
    {Map<String, dynamic>? body}
  ) async {
    var response = await _makeRequest(method, endpoint, body: body);
    
    if (response.statusCode == 401) {
      await _refreshAccessToken();
      response = await _makeRequest(method, endpoint, body: body);
    }
    
    return response;
  }

  Future<http.Response> _makeRequest(
    String method,
    String endpoint,
    {Map<String, dynamic>? body}
  ) async {
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

  Future<Map<String, dynamic>> getPlaylist() async {
    final response = await _authenticatedRequest('GET', '/mobile/api/v1/screen/playlist');
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to load playlist');
  }

  Future<void> sendHeartbeat(String status) async {
    await _authenticatedRequest('POST', '/mobile/api/v1/screen/heartbeat', body: {'status': status});
  }

  Future<Map<String, dynamic>> logPlay({
    required int contentId,
    required String contentType,
    required String category,
    required int duration,
    int? bookingId,
  }) async {
    final response = await _authenticatedRequest(
      'POST',
      '/mobile/api/v1/screen/log-play',
      body: {
        'content_id': contentId,
        'content_type': contentType,
        'category': category,
        'duration': duration,
        'booking_id': bookingId,
      },
    );
    return json.decode(response.body);
  }
}
```

### React Native - Client Complet

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

  async saveTokens(tokens) {
    this.accessToken = tokens.access_token;
    this.refreshToken = tokens.refresh_token;
    await AsyncStorage.setItem('access_token', tokens.access_token);
    await AsyncStorage.setItem('refresh_token', tokens.refresh_token);
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
      throw new Error('Session expired');
    }
  }

  async authenticatedFetch(endpoint, options = {}) {
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
    const response = await this.authenticatedFetch('/mobile/api/v1/screen/playlist');
    return response.json();
  }

  async sendHeartbeat(status = 'playing') {
    await this.authenticatedFetch('/mobile/api/v1/screen/heartbeat', {
      method: 'POST',
      body: JSON.stringify({ status }),
    });
  }

  async logPlay({ contentId, contentType, category, duration, bookingId = null }) {
    const response = await this.authenticatedFetch('/mobile/api/v1/screen/log-play', {
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

---

## Bonnes Pratiques de Securite

### Stockage des Tokens

- **Mobile:** Utilisez un stockage securise (Keychain iOS, Keystore Android)
- **Ne jamais** stocker les tokens dans le code source
- **Ne jamais** exposer les tokens dans les logs

### Gestion des Erreurs 401

1. Tentez de rafraichir le token automatiquement
2. Si le refresh echoue, redirigez vers la connexion
3. Effacez les tokens stockes

### Rate Limiting

1. Implementez un backoff exponentiel en cas de 429
2. Cachez les responses quand possible
3. Regroupez les requetes si possible

### HTTPS

- Utilisez **toujours** HTTPS en production
- Validez les certificats SSL
- Implementez le certificate pinning pour plus de securite

---

*Documentation API Mobile Securisee v1.0*
*Generee le 2024-01-15*
