# API Mobile Shabaka AdScreen

Ce document explique comment intégrer Shabaka AdScreen dans vos applications mobiles ou vos systèmes tiers.

## Ce que fait l'API

L'API permet de :
- Connecter un écran et récupérer sa playlist de contenus
- Signaler qu'un écran est actif (heartbeat)
- Enregistrer les diffusions pour le suivi statistique
- Gérer les réservations depuis une application externe
- Consulter les statistiques d'un tableau de bord mobile

## URL de base

```
Production : https://votre-domaine.com
Développement : http://localhost:5000
```

Toutes les requêtes doivent inclure :

```http
Content-Type: application/json
Accept: application/json
```

## Authentification

L'API utilise des cookies de session. Après une connexion réussie, le serveur renvoie un cookie que vous devez conserver et renvoyer avec chaque requête suivante.

### Connecter un utilisateur (dashboard)

Pour les managers d'établissement qui veulent accéder à leur tableau de bord.

```
POST /login
Content-Type: application/x-www-form-urlencoded

email=manager@restaurant.fr&password=motdepasse
```

En cas de succès, vous êtes redirigé vers `/org/dashboard` et recevez un cookie de session.

### Connecter un écran (player)

Pour les écrans qui doivent diffuser du contenu.

```
POST /player/login
Content-Type: application/x-www-form-urlencoded

screen_code=ABC123&password=screen123
```

En cas de succès, vous êtes redirigé vers `/player/display` et recevez un cookie de session.

### Déconnecter un écran

```
GET /player/logout
```

L'écran passe en statut "offline" et le cookie est invalidé.

## Endpoints publics

Ces endpoints ne nécessitent pas d'authentification.

### Liste des villes par pays

```
GET /api/cities/FR
```

Retourne :

```json
{
  "country": "FR",
  "cities": ["Paris", "Lyon", "Marseille", "Bordeaux", "Toulouse"]
}
```

### Recherche de villes

Pour l'autocomplétion dans les formulaires.

```
GET /api/cities?country=FR&q=Par
```

Retourne :

```json
["Paris", "Pantin", "Pau"]
```

## Endpoints player

Ces endpoints nécessitent une session écran active. Envoyez le cookie de session avec chaque requête.

### Récupérer le mode de l'écran

```
GET /player/api/screen-mode
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

Le mode peut être `playlist` (lecture de contenus) ou `iptv` (flux TV en direct).

### Récupérer la playlist

C'est l'endpoint principal pour le player. Il retourne tout ce dont l'écran a besoin pour fonctionner.

```
GET /player/api/playlist
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
    },
    {
      "id": 456,
      "type": "video",
      "url": "/static/uploads/content/1/video.mp4",
      "duration": 30,
      "priority": 80,
      "category": "internal",
      "name": "Promo Noel"
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

Les catégories de contenu définissent la priorité d'affichage :

| Catégorie | Priorité | Description |
|-----------|----------|-------------|
| broadcast | 200 | Diffusions opérateur (priorité max) |
| paid | 100 | Publicités payantes |
| internal | 80 | Contenus de l'établissement |
| ad_content | 50 | Publicités opérateur |
| filler | 20 | Contenus de remplissage |

### Envoyer un heartbeat

Le player doit signaler régulièrement qu'il est actif. Recommandé : toutes les 30 secondes.

```
POST /player/api/heartbeat
Content-Type: application/json

{
  "status": "playing"
}
```

Les statuts possibles sont `online`, `playing`, `paused`, `idle` ou `error`.

Retourne :

```json
{
  "success": true,
  "timestamp": "2024-01-15T14:30:00.000000"
}
```

### Enregistrer une diffusion

Après chaque contenu joué, signalez-le au serveur. Cela permet de suivre les statistiques et de décompter les diffusions payantes.

```
POST /player/api/log-play
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

Si `exhausted` est `true`, le contenu a atteint son quota de diffusions. Retirez-le de la playlist locale.

### Proxy pour le streaming IPTV

Pour contourner les restrictions CORS sur les flux HLS.

```
GET /player/api/stream-proxy?url=https://stream.example.com/live.m3u8
```

Retourne le manifeste M3U8 avec les URLs réécrites pour passer par le proxy.

### Changer de chaîne TV

```
POST /player/change-channel/ABC123
Content-Type: application/json

{
  "channel_url": "https://stream.example.com/live.m3u8",
  "channel_name": "France 24"
}
```

### Arrêter le flux TV

```
POST /player/tv-stop/ABC123
```

## Endpoints dashboard

Ces endpoints nécessitent une session utilisateur (manager ou admin).

### Statut des écrans

```
GET /api/screens/status
```

Retourne :

```json
[
  {
    "id": 1,
    "name": "Écran Restaurant",
    "status": "playing",
    "last_heartbeat": "2024-01-15T14:30:00.000000",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Écran Entrée",
    "status": "offline",
    "last_heartbeat": "2024-01-15T12:00:00.000000",
    "is_active": true
  }
]
```

Un écran est considéré "online" si son dernier heartbeat date de moins de 2 minutes.

### Statistiques d'un écran

```
GET /api/screen/1/stats
```

Retourne :

```json
{
  "daily_plays": [
    {"date": "2024-01-08", "count": 450},
    {"date": "2024-01-09", "count": 523}
  ],
  "category_stats": [
    {"category": "paid", "count": 1250},
    {"category": "internal", "count": 890},
    {"category": "filler", "count": 1365}
  ]
}
```

### Résumé du dashboard

```
GET /api/dashboard/summary
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

## Endpoints réservation

Ces endpoints sont utilisés par l'interface de réservation publique.

### Page de réservation

```
GET /book/ABC123
```

Retourne la page HTML de réservation pour l'écran avec le code ABC123.

### Calculer le prix

```
POST /book/ABC123/calculate
Content-Type: application/json

{
  "content_type": "image",
  "slot_duration": 10,
  "period_id": 1,
  "num_plays": 100
}
```

Retourne :

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

### Vérifier la disponibilité

```
POST /book/ABC123/availability
Content-Type: application/json

{
  "start_date": "2024-01-20",
  "end_date": "2024-01-27",
  "period_id": 1,
  "slot_duration": 10,
  "content_type": "image"
}
```

Retourne les créneaux disponibles et une recommandation de nombre de diffusions.

### Soumettre une réservation

```
POST /book/ABC123/submit
Content-Type: multipart/form-data

client_name: Jean Dupont
client_email: jean@example.com
client_phone: +33612345678
content_type: image
slot_duration: 10
period_id: 1
booking_mode: plays
num_plays: 100
start_date: 2024-01-20
end_date: 2024-01-27
file: [fichier image ou vidéo]
```

Formats acceptés :
- Images : JPG, JPEG, PNG, GIF, WebP
- Vidéos : MP4, WebM, MOV

### Télécharger le reçu

```
GET /book/receipt/RES-2024-00045
```

Retourne l'image PNG du reçu au format ticket thermique.

## Modèles de données

### Screen (écran)

```json
{
  "id": 1,
  "name": "Écran Restaurant",
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

### Content (contenu)

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

### Booking (réservation)

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
  "status": "active",
  "payment_status": "paid"
}
```

## Gestion des erreurs

L'API utilise les codes HTTP standards :

| Code | Signification |
|------|---------------|
| 200 | Succès |
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Accès refusé |
| 404 | Ressource non trouvée |
| 500 | Erreur serveur |

Les erreurs retournent un JSON :

```json
{
  "error": "Description du problème"
}
```

## Exemple d'intégration Flutter

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
    throw Exception('Impossible de récupérer la playlist');
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

  Future<void> logPlay(int contentId, String type, String category, int duration, int? bookingId) async {
    await http.post(
      Uri.parse('$baseUrl/player/api/log-play'),
      headers: {
        'Cookie': sessionCookie ?? '',
        'Content-Type': 'application/json',
      },
      body: json.encode({
        'content_id': contentId,
        'content_type': type,
        'category': category,
        'duration': duration,
        'booking_id': bookingId,
      }),
    );
  }
}
```

## Exemple d'intégration React Native

```javascript
class AdScreenClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.sessionCookie = null;
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
      return true;
    }
    return false;
  }

  async getPlaylist() {
    const response = await fetch(`${this.baseUrl}/player/api/playlist`, {
      headers: { 'Cookie': this.sessionCookie },
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

  async logPlay(contentId, type, category, duration, bookingId = null) {
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
```

## Boucle de lecture recommandée

Pour un player fonctionnel, voici la séquence à implémenter :

1. **Connexion** : Authentifiez l'écran avec son code et mot de passe
2. **Récupération** : Appelez `/player/api/playlist` pour obtenir les contenus
3. **Heartbeat** : Démarrez un timer qui appelle `/player/api/heartbeat` toutes les 30 secondes
4. **Rafraîchissement** : Démarrez un timer qui appelle `/player/api/playlist` toutes les 60 secondes
5. **Lecture** : Pour chaque contenu, affichez-le pendant sa durée
6. **Signalement** : Après chaque contenu, appelez `/player/api/log-play`
7. **Épuisement** : Si `exhausted: true`, retirez le contenu de la playlist locale
8. **Boucle** : Passez au contenu suivant

Les overlays doivent être affichés par-dessus le contenu principal, selon leur position (top, bottom, left, right).
