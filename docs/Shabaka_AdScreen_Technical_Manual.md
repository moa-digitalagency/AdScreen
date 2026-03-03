© MOA Digital Agency (myoneart.com) - Auteur : Aisance KALONJI
[ 🇫🇷 Français ] | [ 🇬🇧 English ](Shabaka_AdScreen_Technical_Manual_en.md)

# MANUEL TECHNIQUE - SHABAKA ADSCREEN

> **CONFIDENTIEL :** Ce document détaille l'architecture interne et la pile technologique de la solution propriétaire Shabaka AdScreen.

---

## 1. Architecture Globale

### 1.1 Type d'Architecture
Application **Monolithique Modulaire** basée sur le framework **Flask** (Python).
L'application est structurée autour de **Blueprints** pour isoler les domaines fonctionnels et faciliter la maintenance.

### 1.2 Structure des Dossiers
*   `app.py` : Point d'entrée, configuration, initialisation des extensions (DB, Login, CSRF).
*   `models/` : Modèles de données SQLAlchemy (ORM).
*   `routes/` : Contrôleurs (Blueprints) gérant les requêtes HTTP.
*   `services/` : Logique métier complexe (Calculs, Traitements, I/O).
*   `templates/` : Vues Jinja2 (Rendu serveur).
*   `static/` : Assets frontend (JS, CSS, Images).

### 1.3 Blueprints Principaux
*   `auth_bp` : Authentification et gestion de session.
*   `admin_bp` : Back-office Superadmin.
*   `org_bp` : Gestion des Organisations (SaaS).
*   `screen_bp` : Gestion technique des écrans.
*   `player_bp` : Interface de diffusion pour les écrans physiques.
*   `booking_bp` : Moteur de réservation de campagnes.
*   `api_bp` / `mobile_api_bp` : Interfaces API pour intégrations et mobile.

---

## 2. Stack Technologique

### 2.1 Backend
*   **Langage :** Python 3.x
*   **Framework :** Flask
*   **ORM :** SQLAlchemy (Supporte SQLite et PostgreSQL)
*   **Auth :** Flask-Login, PyJWT (pour API Mobile)

### 2.2 Frontend
*   **Template Engine :** Jinja2
*   **CSS Framework :** Tailwind CSS (via CDN ou build process)
*   **JavaScript :** Vanilla JS (ES6+), pas de framework lourd côté client pour le dashboard.

### 2.3 Base de Données
*   **Système :** Compatible PostgreSQL (Prod) et SQLite (Dev/Test).
*   **Migrations :** Gérées via `init_db.py` (Script propriétaire d'initialisation). L'ORM SQLAlchemy s'occupe de l'abstraction des dialectes.

---

## 3. Architecture de Haute Disponibilité (24/7)

Pour assurer une diffusion ininterrompue des contenus sur les écrans (tolérance aux pannes), le Player intègre une architecture de haute disponibilité robuste :

### 3.1 Caching et Service Worker (Offline Fallback)
*   **Mise en Cache Active :** Le Player utilise l'API `CacheStorage` et un **Service Worker** (`static/js/player-sw.js`) pour mettre en cache l'application web et les contenus multimédias (vidéos, images) au fur et à mesure de leur lecture.
*   **Tolérance aux pannes réseau :** En cas de perte de connexion internet, le Service Worker intercepte les requêtes de médias et renvoie les versions en cache. Le Player continue ainsi de lire la dernière playlist valide en boucle.
*   **Reprise automatique :** Dès que la connexion est rétablie, le Player télécharge les nouveaux contenus en arrière-plan et met à jour son cache de manière transparente.

### 3.2 File d'attente intelligente et LocalStorage
*   **Gestion d'état locale :** L'index de la playlist en cours, les logs de diffusion en attente d'envoi et la dernière configuration valide sont sauvegardés dans le `LocalStorage` du navigateur de l'écran.
*   **Continuité après redémarrage :** En cas de coupure de courant et de redémarrage de l'écran physique, le Player récupère son état depuis le `LocalStorage` et reprend la diffusion immédiatement, sans attendre une réponse du serveur distant si ce dernier est injoignable.
*   **Synchronisation différée :** Les statistiques de diffusion (logs) générées pendant une période hors ligne sont empilées localement et envoyées au serveur sous forme de lot (`batch`) dès le retour de la connectivité, garantissant qu'aucune facturation n'est perdue.

---

## 4. Sécurité & Conformité

### 4.1 Authentification
*   Mots de passe hachés via `werkzeug.security` (PBKDF2 ou Scrypt).
*   Protection des sessions via `HttpOnly` et `Secure` cookies.

### 4.2 Protection CSRF
*   Implémentation double : Token de session + Token formulaire/header.
*   Validation stricte sur toutes les méthodes mutantes (POST, PUT, DELETE, PATCH).
*   Exceptions configurées pour les endpoints critiques du Player (Heartbeat) pour éviter les interruptions de service, sécurisés par validation IP/Device.

### 4.3 En-têtes de Sécurité (Security Headers)
*   `X-Content-Type-Options: nosniff`
*   `X-Frame-Options: SAMEORIGIN`
*   `Strict-Transport-Security` (HSTS) en production.

---

## 5. Modèle de Données (Aperçu)

### 5.1 Entités Cœurs
*   **User :** Utilisateur du système (Rôles : Superadmin, Org Admin, User).
*   **Organization :** Entité juridique possédant des écrans.
*   **Screen :** Dispositif d'affichage physique.
*   **Booking :** Réservation d'espace publicitaire.
*   **TimeSlot / TimePeriod :** Définition des créneaux et tarifs.

### 4.2 Entités Contenu
*   **AdContent :** Contenu publicitaire payant.
*   **Broadcast :** Contenu prioritaire (Urgence).
*   **InternalContent :** Contenu propre à l'organisation.
*   **Filler :** Contenu de remplissage.

### 4.3 Entités Facturation
*   **AdContentInvoice :** Facture générée pour une campagne.
*   **AdContentStat :** Preuve de diffusion (Logs journaliers).

---

## 6. Services Métier Clés

### 6.1 Pricing Service (`services/pricing_service.py`)
Calcule le coût des campagnes en temps réel en fonction de la grille tarifaire complexe (Durée x Période x Écran).

### 5.2 Playlist Service (`services/playlist_service.py`)
Génère la liste de lecture pour chaque écran en respectant la file de priorité et les quotas de diffusion achetés.

### 5.3 Input Validator (`services/input_validator.py`)
Assure la validation stricte des entrées utilisateur et des fichiers uploadés (MIME types, extensions) pour prévenir les injections.
