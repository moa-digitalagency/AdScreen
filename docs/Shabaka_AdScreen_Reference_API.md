# Shabaka AdScreen - Référence API

La plateforme expose deux APIs distinctes :
1.  **Management API (`/mobile/api/v1`)** : Pour l'application mobile de gestion (Managers). Authentification JWT.
2.  **Player API (`/player/api`)** : Pour le navigateur du player web. Authentification par Session.

---

## 1. Management API (Mobile)

**Base URL** : `https://votre-domaine.com/mobile/api/v1`
**Auth** : Header `Authorization: Bearer <access_token>`

### 1.1 Authentification

#### `POST /auth/login`
Récupère les tokens d'accès.
*   **Body** : `{ "email": "admin@org.com", "password": "..." }`
*   **Réponse** :
    ```json
    {
      "success": true,
      "user": { "id": 1, "role": "admin", ... },
      "access_token": "eyJ...",
      "refresh_token": "def..."
    }
    ```

#### `POST /auth/refresh`
Rafraîchit un token expiré.
*   **Body** : `{ "refresh_token": "def..." }`
*   **Réponse** : `{ "success": true, "access_token": "new..." }`

### 1.2 Dashboard

#### `GET /dashboard/summary`
Statistiques globales pour l'organisation connectée.
*   **Réponse** :
    ```json
    {
      "total_screens": 5,
      "online_screens": 3,
      "pending_contents": 2,
      "total_revenue": 1250.50
    }
    ```

#### `GET /dashboard/screens`
Liste tous les écrans et leur statut temps réel.
*   **Réponse** : `{"screens": [...], "total": 5}`

#### `GET /dashboard/screen/<id>/stats`
Statistiques détaillées d'un écran (Vues par jour, par catégorie).
*   **Query Params** : `?days=7` (Défaut).

---

## 2. Player API (Web)

**Base URL** : `https://votre-domaine.com/player/api`
**Auth** : Cookie de session (obtenu via le formulaire `/player/login`).

### 2.1 Fonctionnement
Le player web effectue un polling régulier sur ces endpoints pour mettre à jour son contenu.

### 2.2 Endpoints

#### `GET /playlist`
Récupère la liste de lecture complète pour l'écran connecté.
*   **Réponse** :
    ```json
    {
      "mode": "playlist", // ou "iptv"
      "playlist": [
        {
          "id": 123,
          "type": "video",
          "url": "/static/uploads/...",
          "duration": 15,
          "priority": 100
        }
      ],
      "overlays": [...] // Tickers défilants
    }
    ```

#### `POST /heartbeat`
Signale que l'écran est actif (appel toutes les 30s).
*   **Body** : `{ "status": "playing" }`
*   **Réponse** : `{ "success": true, "timestamp": "..." }`

#### `POST /log-play`
Enregistre la diffusion d'un contenu (pour les stats et la facturation).
*   **Body** :
    ```json
    {
      "content_id": 123,
      "content_type": "video",
      "category": "paid",
      "duration": 15,
      "booking_id": 45
    }
    ```
*   **Réponse** : `{ "success": true, "exhausted": false }` (Si `exhausted=true`, le quota est atteint).

#### `GET /stream-proxy`
Proxy pour les flux HLS/M3U8 afin de contourner les CORS.
*   **Query Param** : `?url=http://flux-externe.m3u8`
*   **Réponse** : Le contenu du fichier M3U8 avec les URLs des segments réécrites.

---

## 3. Codes d'Erreur Communs

| Code | Signification |
|------|---------------|
| `200` | Succès |
| `400` | Requête invalide (paramètre manquant, format incorrect) |
| `401` | Non authentifié (Token manquant ou expiré) |
| `403` | Interdit (Compte désactivé ou rôle insuffisant) |
| `429` | Trop de requêtes (Rate Limit atteint) |
| `500` | Erreur serveur interne |
