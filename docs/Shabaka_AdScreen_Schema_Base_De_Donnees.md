# Shabaka AdScreen - Schéma de Base de Données

Ce document décrit la structure des données de l'application. Les modèles sont définis avec SQLAlchemy et stockés dans le dossier `models/`.

## 1. Identité et Accès

### `User` (Utilisateurs)
Représente les acteurs humains du système.
*   **id** : Clé primaire.
*   **username** : Nom d'affichage.
*   **email** : Identifiant unique de connexion.
*   **password_hash** : Mot de passe haché (PBKDF2).
*   **role** : `superadmin`, `admin` (Organization Admin), `manager` (Futur usage).
*   **organization_id** : Lien vers `Organization` (Null pour Superadmin).
*   **permissions** : JSON stockant les droits granulaires.

### `Organization` (Établissements)
Représente un lieu physique ou une entreprise gérant des écrans.
*   **id** : Clé primaire.
*   **name** : Nom commercial.
*   **currency** : Devise utilisée (EUR, USD, MAD, XOF...).
*   **commission_rate** : % prélevé par la plateforme sur les revenus.
*   **is_paid** : Booléen (Abonnement payant ou gratuit).
*   **vat_rate** : Taux de TVA applicable.

### `RegistrationRequest` (Demandes d'Inscription)
Stocke les soumissions du formulaire public `/register`.
*   **status** : `pending`, `approved`, `rejected`.
*   **email**, **name**, **org_name**, **phone** : Données prospect.

## 2. Infrastructure d'Affichage

### `Screen` (Écrans)
L'unité de diffusion.
*   **id** : Clé primaire.
*   **organization_id** : Lien propriétaire.
*   **unique_code** : Code public alphanumérique (ex: `XJ9-22M`).
*   **resolution_width** / **resolution_height** : Dimensions physiques.
*   **orientation** : `landscape`, `portrait`, `custom`.
*   **password_hash** : Authentification du player.
*   **current_mode** : `playlist` (boucle) ou `iptv` (flux live).
*   **iptv_enabled** : Booléen autorisant le mode TV.
*   **last_heartbeat** : Timestamp de dernière activité.

### `TimeSlot` (Créneaux de Temps)
Les durées vendables sur un écran.
*   **screen_id** : Lien écran.
*   **duration_seconds** : Durée (ex: 10, 15, 30).
*   **price_per_play** : Prix de base pour une diffusion.
*   **content_type** : `image` ou `video`.

### `TimePeriod` (Périodes Horaires)
Modulateurs de prix selon l'heure.
*   **screen_id** : Lien écran.
*   **name** : Nom (Matin, Soir, Happy Hour).
*   **start_hour** / **end_hour** : Plage horaire (0-23).
*   **price_multiplier** : Facteur de prix (ex: 1.5 pour majoration).

## 3. Contenus et Diffusion

### `Content` (Contenus Clients)
Fichiers uploadés par les annonceurs pour une réservation.
*   **screen_id** : Lien écran cible.
*   **filename** : Nom sécurisé sur le disque.
*   **content_type** : `image` ou `video`.
*   **status** : `pending` (attente validation), `approved`, `rejected`.
*   **duration_seconds** : Durée réelle.

### `InternalContent` (Auto-promo)
Contenus diffusés par l'établissement lui-même.
*   **organization_id** / **screen_id** : Cible.
*   **priority** : Priorité d'affichage (défaut 80).

### `Filler` (Remplissage)
Contenu par défaut quand la playlist est vide.
*   **screen_id** : Cible.
*   Souvent un QR Code "Réservez cet écran".

### `Broadcast` (Campagnes Admin)
Messages poussés par le Superadmin sur tout le réseau.
*   **target_country**, **target_city**, **target_org_id** : Critères de ciblage.
*   **broadcast_type** : `content` (dans la boucle) ou `overlay` (ticker).
*   **priority** : Haute priorité (200).

### `AdContent` (Publicités Régie)
Publicités vendues par la plateforme, diffusées sur les écrans partenaires.
*   **cpm** : Coût pour mille (futur usage).
*   **max_daily_plays** : Plafond de diffusion.

### `ScreenOverlay` (Habillage)
Textes défilants ou logos superposés.
*   **screen_id** : Cible.
*   **position** : `top`, `bottom`, `middle`.
*   **content** : Texte ou HTML léger.

## 4. Commerce et Transactions

### `Booking` (Réservations)
L'acte d'achat d'un espace publicitaire.
*   **screen_id** / **content_id** : Liaisons.
*   **time_period_id** : Période choisie.
*   **num_plays** : Nombre total de diffusions achetées.
*   **plays_completed** : Compteur d'avancement.
*   **total_price** : Montant facturé.
*   **payment_status** : `paid` (immédiat pour l'instant), `pending`.
*   **status** : `active`, `completed`, `cancelled`.

### `Invoice` (Factures Hebdo)
Relevé de commission pour les établissements.
*   **organization_id** : Débiteur.
*   **week_start_date** / **week_end_date** : Période concernée.
*   **gross_revenue** : Total des ventes sur les écrans.
*   **commission_amount** : Part revenant à la plateforme.
*   **status** : `pending`, `paid`, `validated`.

### `PaymentProof` (Preuves de Virement)
Fichiers uploadés par l'établissement pour justifier le paiement de la commission.
*   **invoice_id** : Lien facture.
*   **file_path** : Chemin du fichier.

## 5. Analytics et Logs

### `StatLog` (Preuve de Diffusion)
Enregistrement atomique de chaque passage d'un contenu.
*   **screen_id** : Écran émetteur.
*   **content_id** / **content_type** : Média joué.
*   **played_at** : Timestamp exact.
*   **duration_seconds** : Durée effective.

### `HeartbeatLog` (Santé Système)
Historique de connectivité.
*   **screen_id** : Écran.
*   **status** : `online`, `offline`, `playing`.
*   **created_at** : Timestamp.

## 6. Configuration

### `SiteSetting` (Paramètres Globaux)
Stockage clé-valeur pour la config dynamique sans redéploiement.
*   **key** : Nom du paramètre (ex: `maintenance_mode`, `platform_vat_rate`).
*   **value** : Valeur (souvent typée en JSON ou String).
