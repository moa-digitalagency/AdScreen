![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue) ![Framework](https://img.shields.io/badge/Framework-Flask-green) ![Database](https://img.shields.io/badge/Database-PostgreSQL-orange) ![Status](https://img.shields.io/badge/Status-Proprietary-red) ![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red) ![Owner: MOA Digital Agency](https://img.shields.io/badge/Owner-MOA%20Digital%20Agency-purple)

# Shabaka AdScreen - Liste Exhaustive des Fonctionnalités (La Bible)

Ce document est la référence absolue de toutes les fonctionnalités, règles métier, validations et comportements système de la plateforme Shabaka AdScreen. Il sert de vérité terrain pour les développeurs, testeurs et auditeurs.

### 1. Cœur du Système (Core)

#### 1.1 Authentification & Sécurité
*   **Hashage Mot de Passe** : Utilisation de `werkzeug.security` (Scrypt par défaut, ou PBKDF2-SHA256 selon configuration) pour le stockage sécurisé.
*   **Session Management** :
    *   Cookies `HttpOnly`, `SameSite=Lax`.
    *   `Secure` flag activé en production (via variable d'env `FLASK_ENV=production`).
    *   Protection contre le vol de session via régénération d'ID.
*   **Protection CSRF (Cross-Site Request Forgery)** :
    *   Implémentation manuelle via `app.before_request`.
    *   Token unique par session (`_csrf_token`).
    *   Vérification sur toutes les méthodes `POST`, `PUT`, `DELETE`, `PATCH`.
    *   **Exceptions** : Endpoints API (`api.*`, `mobile_api.*`) et Webhooks (`billing.cron_generate_invoices`).
*   **En-têtes de Sécurité (Security Headers)** :
    *   `X-Content-Type-Options: nosniff`
    *   `X-Frame-Options: SAMEORIGIN`
    *   `Referrer-Policy: strict-origin-when-cross-origin`
    *   `Strict-Transport-Security: max-age=31536000; includeSubDomains` (si HTTPS).
*   **Rate Limiting** :
    *   Librairie : `Flask-Limiter`.
    *   Stockage : Mémoire (Dev) ou Redis (Prod).
    *   Règles par défaut :
        *   Login : **5 requêtes / minute**.
        *   API Mobile (Lecture) : **60 requêtes / minute**.
        *   Player Heartbeat : **120 requêtes / minute**.

#### 1.2 Validation des Entrées (Input Validation)
Toutes les données entrantes sont assainies via `services/input_validator.py`.
*   **Chaînes de caractères** : Nettoyage HTML (suppression des balises `<script>`, etc.) et troncature à 255 caractères par défaut.
*   **E-mails** : Validation via `email-validator` (vérification syntaxique RFC).
*   **Téléphones** : Regex `^\+?[\d]{8,15}$` (Format international, 8 à 15 chiffres).
*   **Codes Écrans** : Regex `^[A-Za-z0-9\-_]+$` (Alphanumérique, tirets, underscores uniquement).
*   **URLs** :
    *   Doit commencer par `http://` ou `https://`.
    *   Protection **SSRF** (Server-Side Request Forgery) : Résolution DNS et vérification que l'IP cible n'est pas privée/locale (sauf exception).
*   **Dates** : Format strict `YYYY-MM-DD`.
*   **Entiers Positifs** : Vérification stricte des bornes (min/max).

### 2. Gestion des Écrans (Screen Management)

#### 2.1 Configuration
*   **Identifiant Unique** : Code généré aléatoirement ou défini manuellement (validé par Regex).
*   **Résolution** : Largeur et Hauteur en pixels (ex: 1920x1080). Utilisé pour valider les uploads.
*   **Orientation** : 'landscape' (Paysage) ou 'portrait' (Portrait).
*   **Modes de Fonctionnement** :
    1.  **Playlist** : Boucle de contenus médias.
    2.  **IPTV** : Diffusion de flux HLS/M3U8.
        *   Support du Proxying pour contourner CORS.
        *   Conversion MPEG-TS vers HLS à la volée via FFmpeg (si activé).

#### 2.2 Monitoring
*   **Heartbeat** : Le player envoie un ping toutes les **30 secondes**.
*   **Statuts** :
    *   `Online` : Heartbeat reçu < 2 minutes.
    *   `Playing` : En cours de lecture.
    *   `Offline` : Aucun signal > 2 minutes.
*   **Logs** : Historique conservé dans la table `heartbeat_log`.

### 3. Moteur de Réservation (Booking Engine)

#### 3.1 Modes de Réservation
Le système supporte deux logiques de réservation distinctes :
1.  **Par Nombre de Diffusions (Plays Mode)** :
    *   Le client achète un nombre fixe de passages (ex: 100 diffusions).
    *   Validité : Jusqu'à épuisement du quota.
2.  **Par Date (Dates Mode)** :
    *   Le client achète une période (ex: du 01/01 au 07/01).
    *   Objectif : X diffusions par jour.
    *   **Algorithme de Distribution Équitable** : Le système calcule la disponibilité journalière et lisse la diffusion sur la période.

#### 3.2 Calcul du Prix
Formule exacte appliquée dans `booking_routes.py` :
```python
Prix_Base_Slot = Prix_Minute_Ecran * (Duree_Slot / 60)
Prix_Unitaire  = Prix_Base_Slot * Multiplicateur_Periode
Prix_Total_HT  = Prix_Unitaire * Nombre_Total_Diffusions
Prix_TTC       = Prix_Total_HT * (1 + Taux_TVA / 100)
```
*   **TimeSlots** : Durées prédéfinies (10s, 15s, 20s, 30s).
*   **TimePeriods** : Plages horaires avec multiplicateur (ex: 18h-23h = x1.5).

#### 3.3 Validation des Médias Uploadés
*   **Images** :
    *   Formats : JPG, PNG, GIF, WebP.
    *   Dimensions : Doit correspondre **au pixel près** à la résolution de l'écran.
    *   Poids : Max 100 Mo (config `MAX_CONTENT_LENGTH`).
*   **Vidéos** :
    *   Formats : MP4, WebM, MOV.
    *   Durée : Doit être **inférieure ou égale** au slot réservé (tolérance 0).
    *   Analyse : Utilisation de `ffprobe` pour extraire durée et dimensions.

### 4. Le Player (Logique d'Affichage)

#### 4.1 Priorisation des Contenus
L'algorithme de génération de playlist (`mobile_api_routes.py`) classe les contenus par score de priorité décroissant :
1.  **Broadcasts (200)** : Messages d'urgence/système (ex: "Fermeture exceptionnelle").
2.  **Paid Content (100)** : Publicités payantes actives (Quota > 0).
3.  **Internal Content (80)** : Auto-promotion de l'établissement.
4.  **AdContent (50)** : Publicités régie (Réseau tiers).
5.  **Fillers (20)** : Contenu de remplissage par défaut (ex: "Scannez ce QR Code").

#### 4.2 Lecture & Tracking
*   **Polling** : Récupération de la playlist JSON toutes les **60 secondes**.
*   **Preloading** : Mise en cache navigateur des assets pour fluidifier les transitions.
*   **Logging** : À chaque fin de lecture, le player appelle `/log-play`.
    *   Décrémente le compteur `remaining_plays` du Booking.
    *   Passe le statut à `completed` si le quota est atteint.
    *   Enregistre une entrée dans `stat_log` pour les rapports.

#### 4.3 Overlays (Superposition)
*   **Tickers** : Textes défilants configurables (Vitesse, Couleur, Position).
*   **Logique** : Peuvent être associés à une période spécifique ou être permanents.
*   **Compatibilité** : Fonctionnent par-dessus le mode Vidéo ET le mode IPTV.

### 5. API Mobile (Management)

L'API `/mobile/api/v1` est dédiée aux applications de gestion (Flutter/React Native).

#### 5.1 Codes d'Erreur Spécifiques
En plus des codes HTTP standards, l'API retourne des codes métier dans le JSON (`code`):
*   `MISSING_PASSWORD` : Mot de passe non fourni.
*   `INVALID_CREDENTIALS` : Email/Code ou mot de passe incorrect.
*   `ACCOUNT_DISABLED` : L'utilisateur a été désactivé par un admin.
*   `SCREEN_DISABLED` : L'écran a été désactivé.
*   `REFRESH_FAILED` : Token de rafraîchissement invalide ou expiré.
*   `SCREEN_NOT_FOUND` : ID d'écran inexistant ou hors périmètre organisation.
*   `VALIDATION_ERROR` : Échec de validation des données (détails dans le champ `field`).

#### 5.2 Authentification JWT
*   **Access Token** : Expiration 24 heures. Contient `user_id`, `role`, `organization_id`.
*   **Refresh Token** : Expiration 30 jours. Permet d'obtenir un nouveau Access Token sans relogin.

### 6. Facturation & Finance

#### 6.1 Cycle de Vie
1.  **Génération** : Cron Job (`billing_routes.py`) exécuté le **Dimanche à 23h59**.
2.  **Calcul** : Somme des `Booking` payés de la semaine passée.
3.  **Commission** : Application du pourcentage plateforme (défini par Organisation).
4.  **État** : `pending` -> `paid` (Preuve envoyée) -> `validated` (Argent reçu).

#### 6.2 Devises
*   Support multi-devises (EUR, USD, TND, etc.).
*   Le symbole monétaire est injecté globalement via le Context Processor `inject_currency`.

### 7. Internationalisation (i18n)

*   **Mécanisme** : Service custom `services/translation_service.py`.
*   **Stockage** : Fichiers JSON plats.
*   **Détection** :
    1.  URL `/set-language/<lang>`.
    2.  Cookie de session.
    3.  Header `Accept-Language` du navigateur.
    4.  Langue par défaut (`fr`).
