# Shabaka AdScreen - Fonctionnalités Détaillées

Ce document constitue la référence exhaustive de toutes les fonctionnalités de la plateforme Shabaka AdScreen. Il décrit le fonctionnement technique, les règles métier et les comportements attendus pour chaque module.

## 1. Authentification et Gestion des Utilisateurs

### 1.1 Types d'Utilisateurs et Rôles
Le système gère trois niveaux d'accès distincts via le modèle `User` :
*   **Superadmin (`role='superadmin'`)** : Accès total au backend `/admin`. Gestion des organisations, des administrateurs, des paramètres globaux et de la facturation plateforme.
*   **Administrateur Organisation (`role='admin'`)** : Gestionnaire d'un établissement (Organization). Accès au dashboard `/org`. Peut gérer ses écrans, voir ses revenus et valider les contenus.
*   **Écran (Player)** : Entité technique authentifiée via `screen_code` et `password`. Dispose d'une session spécifique pour l'affichage.

### 1.2 Mécanismes de Connexion
*   **Interface Web (Flask-Login)** :
    *   Utilise des sessions sécurisées (cookies `HttpOnly`, `SameSite=Lax`).
    *   Protection CSRF active sur tous les formulaires POST.
    *   Hachage des mots de passe via `werkzeug.security` (PBKDF2-SHA256).
    *   Redirection intelligente après login (`next` parameter) avec validation de l'URL de retour (`is_safe_url`).
*   **API Mobile (JWT)** :
    *   Authentification par Token (Access Token 24h, Refresh Token 30j).
    *   Endpoints : `/mobile/api/v1/auth/login` et `/mobile/api/v1/auth/refresh`.
    *   Rate Limiting strict sur ces endpoints (5 req/min pour login).

### 1.3 Inscription
*   **Formulaire Public** : Accessible via `/register`.
*   **Validation** : Vérification de l'unicité de l'email.
*   **Workflow** : Création d'une `RegistrationRequest`. Notification WhatsApp automatique envoyée à l'administrateur plateforme si configuré.

## 2. Gestion des Écrans (Screen Management)

### 2.1 Configuration de l'Écran
Chaque écran possède une configuration unique :
*   **Code Unique** : Généré aléatoirement, sert d'identifiant public pour la réservation.
*   **Résolution** : Définie à la création (ex: 1920x1080).
*   **Orientation** : Paysage (16:9), Portrait (9:16) ou Custom.
*   **Mot de passe** : Pour la connexion du player.
*   **Tarification** : Prix de base par minute (ex: 2.00€).

### 2.2 Modes de Fonctionnement
*   **Mode Playlist** : Boucle classique de contenus (Images/Vidéos).
*   **Mode IPTV/OnlineTV** :
    *   Diffusion d'un flux HLS/M3U8.
    *   Support du proxying pour contourner les restrictions CORS (`/player/api/stream-proxy`).
    *   Conversion MPEG-TS vers HLS à la volée via FFmpeg pour les flux incompatibles web.

### 2.3 Monitoring (Heartbeat)
*   Les écrans envoient un signal ("heartbeat") toutes les 30 secondes vers `/player/api/heartbeat`.
*   Statut calculé en temps réel :
    *   **Online** : Heartbeat reçu il y a < 2 minutes.
    *   **Offline** : Aucun signal depuis > 2 minutes.
*   Historique conservé dans `HeartbeatLog`.

## 3. Système de Réservation (Booking Engine)

### 3.1 Parcours Client (Annonceur)
1.  **Scan QR Code** : Redirection vers `/book/<screen_code>`.
2.  **Sélection** : Choix du type de contenu (Image/Vidéo), durée du slot (10s, 15s, 30s...), et période horaire.
3.  **Upload & Validation** :
    *   **Images** : JPG, PNG, GIF, WebP. Validation stricte de la résolution (doit correspondre exactement à l'écran).
    *   **Vidéos** : MP4, WebM, MOV. Validation de la durée (doit être <= slot choisi) et de la résolution.
    *   Génération de noms de fichiers sécurisés (UUID).
4.  **Paiement** :
    *   Calcul du prix en temps réel (Prix base * Multiplicateur période * Nombre de diffusions).
    *   Ajout de la TVA si configurée.
    *   Génération d'un reçu (Ticket thermique PNG ou PDF).

### 3.2 Logique de Prix
*   **TimeSlots** : Définis par l'organisation (ex: 10s = 0.5€).
*   **TimePeriods** : Multiplicateurs horaires (ex: "Soirée" 18h-23h = x1.5).
*   **Formule** : `Prix_Unitaire = (Prix_Base_Minute * (Durée/60)) * Multiplicateur_Période`.

### 3.3 Validation des Contenus
*   Les contenus uploadés sont en statut `pending` par défaut.
*   L'organisation doit les valider depuis son dashboard `/org`.
*   Motif de refus obligatoire en cas de rejet.

## 4. Le Player (Affichage)

### 4.1 Architecture du Player
*   Page web unique : `/player/display`.
*   Logique client en JavaScript pur (Vanilla JS).
*   **Polling** : Récupération de la playlist JSON toutes les 60s via `/player/api/playlist`.
*   **Mise en cache** : Pré-chargement des médias pour éviter les écrans noirs.

### 4.2 Algorithme de Playlist
La playlist est construite dynamiquement par le backend en agrégeant plusieurs sources :
1.  **Broadcasts (Priorité 200)** : Messages d'urgence ou campagnes globales de l'opérateur.
2.  **Contenus Payants (Priorité 100)** : Réservations validées et actives.
3.  **Contenus Internes (Priorité 80)** : Auto-promotion de l'établissement.
4.  **AdContent (Priorité 50)** : Publicités régie (si autorisé par l'écran).
5.  **Fillers (Priorité 20)** : Contenu de remplissage (ex: QR Code "Réservez ici") si aucun autre contenu n'est disponible.

### 4.3 Overlays (Superposition)
*   Support des textes défilants (tickers) par-dessus la vidéo/image.
*   Positionnement configurable (Haut, Bas).
*   Compatible avec le mode IPTV.

## 5. Facturation et Revenus

### 5.1 Cycle de Facturation
*   **Hebdomadaire** : Du lundi au dimanche.
*   **Génération** : Automatique le dimanche à 23h59 via Cron (`/billing/cron/generate-invoices`).

### 5.2 Modèle de Commission
*   L'opérateur prélève une commission (ex: 20%) sur les revenus générés par les écrans.
*   Une facture est générée pour l'organisation indiquant le montant à reverser à la plateforme.
*   Workflow : Génération -> Upload Preuve Virement -> Validation Admin -> Clôture.

## 6. API Mobile et Intégrations

### 6.1 API Mobile (`/mobile/api/v1`)
*   Conçue pour une application de gestion (Flutter/React Native).
*   Authentification JWT.
*   Endpoints pour :
    *   Login Manager & Écran.
    *   Dashboard statistique (Vues, Revenus).
    *   Heartbeat & Logs de lecture.

### 6.2 Sécurité API
*   **Rate Limiting** : Protection contre le brute-force (Flask-Limiter).
*   **Input Validation** : Validation stricte des types et formats (email, entiers positifs).
*   **CORS** : Configuration restrictive.

## 7. Fonctionnalités Système Avancées

### 7.1 Proxy HLS (Streaming)
*   Le backend agit comme un proxy pour les flux `.m3u8` et `.ts` afin de :
    *   Contourner les restrictions CORS des fournisseurs IPTV.
    *   Masquer l'URL réelle du flux source.
    *   Gérer les redirections et les headers User-Agent spécifiques (ex: VLC).

### 7.2 Conversion Vidéo
*   Utilisation de `FFmpeg` (via `subprocess`) pour convertir les flux MPEG-TS bruts en HLS compatible navigateur si nécessaire.
*   Gestion des segments `.ts` sur le disque local avec nettoyage automatique.

### 7.3 Internationalisation (i18n)
*   Support multi-langues (FR, EN, AR, ES).
*   Détection automatique via IP ou préférence navigateur.
*   Service de traduction custom (`services/translation_service.py`) utilisant des fichiers JSON.
