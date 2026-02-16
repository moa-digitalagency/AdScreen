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
Récupère les tokens d'accès pour un administrateur.
*   **Body** : `{ "email": "admin@org.com", "password": "..." }`
*   **Réponse Succès (200)** :
    ```json
    {
      "success": true,
      "user": { "id": 1, "role": "admin", ... },
      "access_token": "eyJ...",
      "refresh_token": "def..."
    }
    ```

#### `POST /auth/screen-login`
Connecte un écran via son code unique.
*   **Body** : `{ "screen_code": "HOTEL-LOBBY-01", "password": "..." }`
*   **Réponse Succès (200)** :
    ```json
    {
      "success": true,
      "screen": { "id": 12, "resolution": "1920x1080" },
      "access_token": "...",
      "refresh_token": "..."
    }
    ```

#### `POST /auth/refresh`
Rafraîchit un token expiré.
*   **Body** : `{ "refresh_token": "def..." }`
*   **Réponse Succès (200)** : `{ "success": true, "access_token": "new..." }`

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
          "priority": 100,
          "remaining_plays": 50
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

## 3. Codes d'Erreur & Formats

L'API utilise des codes HTTP standards couplés à un code d'erreur interne JSON pour plus de précision.

### 3.1 Format d'Erreur JSON
```json
{
  "error": "Message lisible pour l'humain",
  "code": "INTERNAL_ERROR_CODE",
  "field": "field_name" // Optionnel, pour les erreurs de validation
}
```

### 3.2 Codes Métier (Internal Codes)

| Code Interne | HTTP | Description |
| :--- | :--- | :--- |
| `MISSING_PASSWORD` | 400 | Le champ mot de passe est vide. |
| `MISSING_FIELDS` | 400 | Champs obligatoires manquants dans le JSON. |
| `INVALID_JSON` | 400 | Le corps de la requête n'est pas un JSON valide. |
| `VALIDATION_ERROR` | 400 | Un champ ne respecte pas le format attendu (Email, Regex...). |
| `INVALID_CREDENTIALS` | 401 | Email/Code ou mot de passe incorrect. |
| `REFRESH_FAILED` | 401 | Le Refresh Token est invalide, expiré ou révoqué. |
| `ACCOUNT_DISABLED` | 403 | Le compte utilisateur a été désactivé par un administrateur. |
| `SCREEN_DISABLED` | 403 | L'écran a été désactivé (impayés ou maintenance). |
| `SCREEN_NOT_FOUND` | 404 | L'ID d'écran est introuvable ou vous n'y avez pas accès. |
| `USER_NOT_FOUND` | 404 | Utilisateur introuvable. |

### 3.3 Rate Limits (Limites)
Les en-têtes `X-RateLimit-Limit`, `X-RateLimit-Remaining` et `X-RateLimit-Reset` sont inclus dans les réponses.

| Endpoint | Limite | Conséquence |
| :--- | :--- | :--- |
| Auth (`/login`, `/refresh`) | 5 / minute | HTTP 429 |
| API Mobile (Global) | 60 / minute | HTTP 429 |
| Player Heartbeat | 120 / minute | HTTP 429 |
