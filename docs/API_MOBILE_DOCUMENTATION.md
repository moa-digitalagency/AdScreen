# Shabaka AdScreen - Documentation API Mobile

## Table des matieres

1. [Introduction](#introduction)
2. [Authentification](#authentification)
3. [Endpoints Publics](#endpoints-publics)
4. [Endpoints Player (Ecran)](#endpoints-player-ecran)
5. [Endpoints API Dashboard](#endpoints-api-dashboard)
6. [Endpoints Booking](#endpoints-booking)
7. [Modeles de Donnees](#modeles-de-donnees)
8. [Codes d'Erreur](#codes-derreur)
9. [Exemples d'Integration](#exemples-dintegration)

---

## Introduction

Cette documentation decrit l'API REST de la plateforme Shabaka AdScreen pour le developpement d'applications mobiles. L'API permet de:

- Authentifier les utilisateurs et les ecrans
- Gerer les playlists et contenus
- Suivre les statistiques de diffusion
- Effectuer des reservations publicitaires

### URL de Base

```
Production: https://votre-domaine.com
Developpement: http://localhost:5000
```

### Headers Standards

```http
Content-Type: application/json
Accept: application/json
```

### Gestion des Sessions

L'API utilise des cookies de session pour l'authentification. Les clients mobiles doivent:
1. Conserver les cookies retournes lors de la connexion
2. Envoyer ces cookies avec chaque requete subsequente

---

## Authentification

### Authentification Utilisateur (Dashboard)

#### POST /login

Connecte un utilisateur au dashboard de gestion.

**Request Body (form-data):**
```
email: string (required)
password: string (required)
```

**Response Success (redirect):**
- Superadmin: Redirect vers `/admin/dashboard`
- Organisation: Redirect vers `/org/dashboard`

**Response Error:**
```json
{
  "flash": "Email ou mot de passe incorrect."
}
```

---

### Authentification Ecran (Player)

#### POST /player/login

Connecte un ecran pour la diffusion.

**Request Body (form-data):**
```
screen_code: string (required) - Code unique de l'ecran
password: string (required) - Mot de passe de l'ecran
```

**Response Success:**
- Redirect vers `/player/display`
- Cookie de session avec `screen_id`

**Response Error:**
```json
{
  "flash": "Code ecran ou mot de passe incorrect."
}
```

---

### Deconnexion Ecran

#### GET /player/logout

Deconnecte l'ecran et met son statut a "offline".

**Response:**
- Redirect vers `/player/login`

---

## Endpoints Publics

### Obtenir les Villes par Pays

#### GET /api/cities/{country_code}

Retourne la liste des villes pour un pays donne.

**Parametres URL:**
| Parametre | Type | Description |
|-----------|------|-------------|
| country_code | string | Code ISO du pays (ex: FR, MA, US) |

**Response:**
```json
{
  "country": "FR",
  "cities": [
    "Paris",
    "Lyon",
    "Marseille",
    "Bordeaux",
    "Toulouse"
  ]
}
```

---

### Recherche de Villes (Autocomplete)

#### GET /api/cities

Recherche de villes avec autocomplete.

**Query Parameters:**
| Parametre | Type | Description |
|-----------|------|-------------|
| country | string | Code ISO du pays |
| q | string | Terme de recherche |

**Response:**
```json
["Paris", "Pau", "Pantin"]
```

---

## Endpoints Player (Ecran)

> **Note:** Tous les endpoints Player necessitent une session ecran active.

### Obtenir le Mode de l'Ecran

#### GET /player/api/screen-mode

Retourne le mode actuel de l'ecran (playlist ou IPTV).

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

**Mode IPTV:**
```json
{
  "mode": "iptv",
  "iptv_enabled": true,
  "iptv_channel_url": "http://stream.example.com/channel.m3u8",
  "iptv_channel_name": "France 24",
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

**Erreurs:**
| Code | Message |
|------|---------|
| 401 | `{"error": "Non authentifie"}` |
| 404 | `{"error": "Ecran non trouve"}` |

---

### Obtenir la Playlist

#### GET /player/api/playlist

Retourne la playlist complete de contenus a diffuser.

**Response (Mode Playlist):**
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
      "name": "Promo Noel"
    },
    {
      "id": 789,
      "type": "image",
      "url": "/static/uploads/fillers/1/ambiance.jpg",
      "duration": 10,
      "priority": 20,
      "category": "filler",
      "name": "ambiance.jpg"
    }
  ],
  "overlays": [
    {
      "id": 1,
      "type": "text",
      "content": "PROMO -20%",
      "position": "bottom-right",
      "priority": 100,
      "style": {
        "background_color": "rgba(0,0,0,0.7)",
        "text_color": "#ffffff",
        "font_size": 24
      }
    }
  ],
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

**Response (Mode IPTV):**
```json
{
  "screen": {
    "id": 1,
    "name": "Ecran Restaurant",
    "resolution": "1920x1080",
    "orientation": "landscape"
  },
  "mode": "iptv",
  "iptv": {
    "url": "http://stream.example.com/channel.m3u8",
    "name": "France 24"
  },
  "playlist": [],
  "overlays": [
    {
      "id": 1,
      "type": "logo",
      "image_url": "/static/uploads/overlays/logo.png",
      "position": "top-left"
    }
  ],
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

**Categories de Contenu:**
| Category | Description | Priorite |
|----------|-------------|----------|
| paid | Contenu publicitaire paye | 100 |
| internal | Contenu interne de l'organisation | Variable |
| ad_content | Contenu publicitaire admin | 50 |
| filler | Contenu de remplissage | 20 |

---

### Envoyer un Heartbeat

#### POST /player/api/heartbeat

Signale que l'ecran est actif et met a jour son statut.

**Request Body:**
```json
{
  "status": "playing"
}
```

**Valeurs de Status:**
| Status | Description |
|--------|-------------|
| online | Ecran connecte, en attente |
| playing | Ecran en cours de diffusion |
| offline | Ecran deconnecte |

**Response:**
```json
{
  "success": true,
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

**Frequence Recommandee:** Toutes les 30 secondes

---

### Enregistrer une Diffusion

#### POST /player/api/log-play

Enregistre qu'un contenu a ete diffuse.

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

**Champs de Response:**
| Champ | Type | Description |
|-------|------|-------------|
| success | boolean | Operation reussie |
| exhausted | boolean | true si le booking a atteint son quota de diffusions |

---

### Proxy de Stream IPTV

#### GET /player/api/stream-proxy

Proxy pour les streams IPTV/HLS (bypass CORS).

**Query Parameters:**
| Parametre | Type | Description |
|-----------|------|-------------|
| url | string | URL du stream a proxifier |

**Response:**
- Pour manifests M3U8: Contenu reecrit avec URLs absolues
- Pour segments TS: Stream binaire chunked

**Headers de Response:**
```http
Access-Control-Allow-Origin: *
Content-Type: video/mp2t (pour TS) ou application/vnd.apple.mpegurl (pour M3U8)
Cache-Control: no-cache, no-store, must-revalidate
```

---

### Changer de Chaine TV

#### POST /player/change-channel/{screen_code}

Change la chaine IPTV d'un ecran.

**Parametres URL:**
| Parametre | Type | Description |
|-----------|------|-------------|
| screen_code | string | Code unique de l'ecran |

**Request Body:**
```json
{
  "channel_url": "http://stream.example.com/channel.m3u8",
  "channel_name": "France 24"
}
```

**Response Success:**
```json
{
  "status": "ready",
  "screen_code": "ABC123",
  "channel_name": "France 24"
}
```

---

### Arreter le Stream TV

#### POST /player/tv-stop/{screen_code}

Arrete le stream IPTV d'un ecran.

**Response:**
```json
{
  "status": "stopped",
  "screen_code": "ABC123"
}
```

---

## Endpoints API Dashboard

> **Note:** Ces endpoints necessitent une authentification utilisateur.

### Statut des Ecrans

#### GET /api/screens/status

Retourne le statut de tous les ecrans de l'utilisateur.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Ecran Restaurant",
    "status": "playing",
    "last_heartbeat": "2024-01-15T14:30:00.000000",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Ecran Entree",
    "status": "offline",
    "last_heartbeat": "2024-01-15T12:00:00.000000",
    "is_active": true
  }
]
```

**Logique de Statut:**
- Un ecran est considere "online" si son dernier heartbeat date de moins de 2 minutes
- Sinon, le statut est "offline"

---

### Statistiques d'un Ecran

#### GET /api/screen/{screen_id}/stats

Retourne les statistiques de diffusion d'un ecran.

**Response:**
```json
{
  "daily_plays": [
    {"date": "2024-01-08", "count": 450},
    {"date": "2024-01-09", "count": 523},
    {"date": "2024-01-10", "count": 498},
    {"date": "2024-01-11", "count": 512},
    {"date": "2024-01-12", "count": 487},
    {"date": "2024-01-13", "count": 534},
    {"date": "2024-01-14", "count": 501}
  ],
  "category_stats": [
    {"category": "paid", "count": 1250},
    {"category": "internal", "count": 890},
    {"category": "filler", "count": 1365}
  ]
}
```

---

### Resume du Dashboard

#### GET /api/dashboard/summary

Retourne un resume des metriques principales.

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

## Endpoints Booking

### Page de Reservation

#### GET /book/{screen_code}

Affiche la page de reservation pour un ecran.

**Response:** Page HTML de reservation

---

### Calculer le Prix

#### POST /book/{screen_code}/calculate

Calcule le prix d'une reservation.

**Request Body:**
```json
{
  "content_type": "image",
  "slot_duration": 10,
  "period_id": 1,
  "num_plays": 100
}
```

**Response:**
```json
{
  "price_per_play": 0.25,
  "total_price": 25.00,
  "vat_rate": 20,
  "vat_amount": 5.00,
  "total_price_with_vat": 30.00,
  "num_plays": 100
}
```

---

### Verifier la Disponibilite

#### POST /book/{screen_code}/availability

Verifie la disponibilite pour une periode donnee.

**Request Body:**
```json
{
  "start_date": "2024-01-20",
  "end_date": "2024-01-27",
  "period_id": 1,
  "slot_duration": 10,
  "content_type": "image"
}
```

**Response:**
```json
{
  "availability": {
    "total_available_seconds": 36000,
    "available_plays": 3600,
    "slot_duration": 10,
    "num_days": 7,
    "periods": [
      {
        "id": 1,
        "name": "Midi",
        "start_hour": 11,
        "end_hour": 14
      }
    ]
  },
  "distribution": {
    "plays_per_day": 514,
    "distribution": [
      {"date": "2024-01-20", "plays": 514},
      {"date": "2024-01-21", "plays": 514}
    ]
  },
  "price_per_play": 0.25,
  "recommended_plays": 360
}
```

---

### Calculer pour Periode de Dates

#### POST /book/{screen_code}/calculate-dates

Calcule le nombre de diffusions pour une plage de dates.

**Request Body:**
```json
{
  "start_date": "2024-01-20",
  "end_date": "2024-01-27",
  "period_id": 1,
  "slot_duration": 10,
  "content_type": "image",
  "plays_per_day": 20
}
```

**Response:**
```json
{
  "num_days": 7,
  "plays_per_day": 20,
  "total_plays": 140,
  "max_available_plays": 3600,
  "price_per_play": 0.25,
  "total_price": 35.00,
  "vat_rate": 20,
  "vat_amount": 7.00,
  "total_price_with_vat": 42.00,
  "distribution": [
    {"date": "2024-01-20", "plays": 20},
    {"date": "2024-01-21", "plays": 20}
  ]
}
```

---

### Soumettre une Reservation

#### POST /book/{screen_code}/submit

Soumet une nouvelle reservation avec upload de fichier.

**Request Body (multipart/form-data):**
| Champ | Type | Description |
|-------|------|-------------|
| client_name | string | Nom du client |
| client_email | string | Email du client |
| client_phone | string | Telephone du client |
| content_type | string | "image" ou "video" |
| slot_duration | integer | Duree en secondes |
| period_id | integer | ID de la periode horaire |
| booking_mode | string | "plays" ou "dates" |
| num_plays | integer | Nombre de diffusions (mode plays) |
| start_date | string | Date debut (YYYY-MM-DD) |
| end_date | string | Date fin (YYYY-MM-DD) |
| file | file | Fichier image ou video |

**Formats Acceptes:**
- Images: JPG, JPEG, PNG, GIF
- Videos: MP4, WEBM, MOV

**Response:** Page HTML de confirmation avec numero de reservation

---

### Telecharger le Recu

#### GET /book/receipt/{reservation_number}

Telecharge le recu de reservation en image PNG.

**Response:**
- Content-Type: image/png
- Content-Disposition: attachment; filename="recu_{reservation_number}.png"

---

## Modeles de Donnees

### Screen (Ecran)

```json
{
  "id": 1,
  "name": "Ecran Restaurant",
  "unique_code": "ABC123",
  "resolution_width": 1920,
  "resolution_height": 1080,
  "orientation": "landscape",
  "status": "playing",
  "is_active": true,
  "current_mode": "playlist",
  "iptv_enabled": true,
  "last_heartbeat": "2024-01-15T14:30:00.000000"
}
```

### Content (Contenu)

```json
{
  "id": 123,
  "filename": "image.jpg",
  "original_filename": "ma_pub.jpg",
  "content_type": "image",
  "file_path": "static/uploads/content/1/image.jpg",
  "file_size": 256000,
  "width": 1920,
  "height": 1080,
  "duration_seconds": 10,
  "status": "approved",
  "in_playlist": true
}
```

### Booking (Reservation)

```json
{
  "id": 45,
  "reservation_number": "RES-2024-00045",
  "screen_id": 1,
  "content_id": 123,
  "booking_mode": "plays",
  "slot_duration": 10,
  "num_plays": 100,
  "plays_completed": 25,
  "price_per_play": 0.25,
  "total_price": 25.00,
  "vat_rate": 20,
  "vat_amount": 5.00,
  "total_price_with_vat": 30.00,
  "start_date": "2024-01-15",
  "end_date": "2024-01-31",
  "status": "active",
  "payment_status": "paid"
}
```

### Overlay (Superposition)

```json
{
  "id": 1,
  "type": "text",
  "content": "PROMO -20%",
  "position": "bottom-right",
  "priority": 100,
  "is_active": true,
  "style": {
    "background_color": "rgba(0,0,0,0.7)",
    "text_color": "#ffffff",
    "font_size": 24,
    "padding": 10
  }
}
```

---

## Codes d'Erreur

### Codes HTTP Standards

| Code | Description |
|------|-------------|
| 200 | Succes |
| 400 | Requete invalide |
| 401 | Non authentifie |
| 403 | Acces refuse |
| 404 | Ressource non trouvee |
| 500 | Erreur serveur |

### Format des Erreurs

```json
{
  "error": "Description de l'erreur"
}
```

### Erreurs Courantes

| Erreur | Description | Solution |
|--------|-------------|----------|
| Non authentifie | Session expiree ou absente | Reconnecter l'ecran/utilisateur |
| Ecran non trouve | Code ecran invalide | Verifier le code ecran |
| Ecran desactive | L'ecran a ete desactive | Contacter l'administrateur |
| Creneau non disponible | Le type/duree demande n'existe pas | Choisir un autre creneau |
| Format de fichier non supporte | Extension non autorisee | Utiliser JPG, PNG, MP4, etc. |

---

## Exemples d'Integration

### Flutter/Dart - Connexion Ecran

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class AdScreenApi {
  final String baseUrl;
  String? sessionCookie;

  AdScreenApi(this.baseUrl);

  Future<bool> loginScreen(String screenCode, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/player/login'),
      body: {
        'screen_code': screenCode,
        'password': password,
      },
    );

    if (response.statusCode == 302 || response.statusCode == 200) {
      sessionCookie = response.headers['set-cookie'];
      return true;
    }
    return false;
  }

  Future<Map<String, dynamic>> getPlaylist() async {
    final response = await http.get(
      Uri.parse('$baseUrl/player/api/playlist'),
      headers: {'Cookie': sessionCookie ?? ''},
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to load playlist');
  }

  Future<void> sendHeartbeat(String status) async {
    await http.post(
      Uri.parse('$baseUrl/player/api/heartbeat'),
      headers: {
        'Cookie': sessionCookie ?? '',
        'Content-Type': 'application/json',
      },
      body: json.encode({'status': status}),
    );
  }

  Future<void> logPlay({
    required int contentId,
    required String contentType,
    required String category,
    required int duration,
    int? bookingId,
  }) async {
    await http.post(
      Uri.parse('$baseUrl/player/api/log-play'),
      headers: {
        'Cookie': sessionCookie ?? '',
        'Content-Type': 'application/json',
      },
      body: json.encode({
        'content_id': contentId,
        'content_type': contentType,
        'category': category,
        'duration': duration,
        'booking_id': bookingId,
      }),
    );
  }
}
```

### React Native - Exemple Complet

```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';

class AdScreenClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.sessionCookie = null;
  }

  async init() {
    this.sessionCookie = await AsyncStorage.getItem('sessionCookie');
  }

  async loginScreen(screenCode, password) {
    const formData = new FormData();
    formData.append('screen_code', screenCode);
    formData.append('password', password);

    const response = await fetch(`${this.baseUrl}/player/login`, {
      method: 'POST',
      body: formData,
      redirect: 'manual',
    });

    const cookies = response.headers.get('set-cookie');
    if (cookies) {
      this.sessionCookie = cookies;
      await AsyncStorage.setItem('sessionCookie', cookies);
      return true;
    }
    return false;
  }

  async getPlaylist() {
    const response = await fetch(`${this.baseUrl}/player/api/playlist`, {
      headers: {
        'Cookie': this.sessionCookie,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch playlist');
    }

    return response.json();
  }

  async getScreenMode() {
    const response = await fetch(`${this.baseUrl}/player/api/screen-mode`, {
      headers: {
        'Cookie': this.sessionCookie,
      },
    });

    return response.json();
  }

  async sendHeartbeat(status = 'playing') {
    await fetch(`${this.baseUrl}/player/api/heartbeat`, {
      method: 'POST',
      headers: {
        'Cookie': this.sessionCookie,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status }),
    });
  }

  async logContentPlay(contentId, type, category, duration, bookingId = null) {
    const response = await fetch(`${this.baseUrl}/player/api/log-play`, {
      method: 'POST',
      headers: {
        'Cookie': this.sessionCookie,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content_id: contentId,
        content_type: type,
        category: category,
        duration: duration,
        booking_id: bookingId,
      }),
    });

    return response.json();
  }
}

// Usage
const client = new AdScreenClient('https://votre-domaine.com');
await client.init();

// Login
const success = await client.loginScreen('ABC123', 'password');

// Get playlist and start playing
const playlist = await client.getPlaylist();
for (const content of playlist.playlist) {
  // Display content...
  await client.logContentPlay(
    content.id,
    content.type,
    content.category,
    content.duration,
    content.booking_id
  );
}

// Heartbeat every 30 seconds
setInterval(() => client.sendHeartbeat('playing'), 30000);
```

### iOS Swift - Exemple

```swift
import Foundation

class AdScreenAPI {
    let baseURL: String
    var sessionCookie: String?
    
    init(baseURL: String) {
        self.baseURL = baseURL
    }
    
    func loginScreen(code: String, password: String, completion: @escaping (Bool) -> Void) {
        let url = URL(string: "\(baseURL)/player/login")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let body = "screen_code=\(code)&password=\(password)"
        request.httpBody = body.data(using: .utf8)
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let httpResponse = response as? HTTPURLResponse,
               let cookies = httpResponse.allHeaderFields["Set-Cookie"] as? String {
                self.sessionCookie = cookies
                completion(true)
            } else {
                completion(false)
            }
        }.resume()
    }
    
    func getPlaylist(completion: @escaping (PlaylistResponse?) -> Void) {
        let url = URL(string: "\(baseURL)/player/api/playlist")!
        var request = URLRequest(url: url)
        
        if let cookie = sessionCookie {
            request.setValue(cookie, forHTTPHeaderField: "Cookie")
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data else {
                completion(nil)
                return
            }
            
            let playlist = try? JSONDecoder().decode(PlaylistResponse.self, from: data)
            completion(playlist)
        }.resume()
    }
    
    func sendHeartbeat(status: String) {
        let url = URL(string: "\(baseURL)/player/api/heartbeat")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let cookie = sessionCookie {
            request.setValue(cookie, forHTTPHeaderField: "Cookie")
        }
        
        let body = ["status": status]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request).resume()
    }
}

// Models
struct PlaylistResponse: Codable {
    let screen: ScreenInfo
    let mode: String
    let playlist: [ContentItem]
    let overlays: [Overlay]
    let timestamp: String
}

struct ScreenInfo: Codable {
    let id: Int
    let name: String
    let resolution: String
    let orientation: String
}

struct ContentItem: Codable {
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

struct Overlay: Codable {
    let id: Int
    let type: String
    let content: String?
    let position: String
    let priority: Int
}
```

---

## Bonnes Pratiques

### Gestion du Cache

- Desactivez le cache pour les endpoints `/player/api/playlist` et `/player/api/screen-mode`
- Les headers `Cache-Control: no-cache` sont deja definis cote serveur

### Gestion de la Connexion

1. Stockez le cookie de session de maniere securisee
2. Implementez un mecanisme de reconnexion automatique
3. Verifiez la validite de la session avant chaque appel

### Heartbeat

1. Envoyez un heartbeat toutes les 30 secondes
2. Utilisez le status "playing" pendant la diffusion
3. Utilisez le status "online" en attente de contenu

### Gestion des Erreurs

1. Implementez un retry avec backoff exponentiel
2. Loggez les erreurs pour le diagnostic
3. Affichez des messages clairs a l'utilisateur

### Optimisation

1. Cachez localement la playlist entre les rafraichissements
2. Pre-chargez les contenus suivants pendant la diffusion
3. Utilisez la compression gzip pour les requetes

---

## Support

Pour toute question technique:
- Email: support@shabaka-adscreen.com
- Documentation: https://docs.shabaka-adscreen.com

---

*Documentation generee le 2024-01-15*
*Version API: 1.0*
