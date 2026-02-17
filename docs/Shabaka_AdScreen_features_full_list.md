© MOA Digital Agency (myoneart.com) - Auteur : Aisance KALONJI
[ 🇫🇷 Français ] | [ 🇬🇧 English ](Shabaka_AdScreen_features_full_list_en.md)

# BIBLE DES FONCTIONNALITÉS - SHABAKA ADSCREEN

> **STATUT :** CONFIDENTIEL & PROPRIÉTAIRE.
> Ce document recense l'intégralité des règles métier, algorithmes et processus de l'application Shabaka AdScreen.

---

## 1. Gestion des Utilisateurs et Organisations

### 1.1 Rôles et Permissions
*   **Superadmin :** Accès total. Gestion des organisations, validation des contenus globaux, configuration système.
*   **Administrateur Organisation (Org Admin) :** Gestion de ses propres écrans, validation des contenus locaux, accès à la facturation de son entité.
*   **Utilisateur Standard :** Création de campagnes, upload de contenu, paiement.

### 1.2 Hiérarchie
*   Un utilisateur appartient à une ou plusieurs **Organisations**.
*   Les commissions sur les publicités sont reversées à l'Organisation propriétaire de l'écran.

---

## 2. Gestion des Écrans (Screens)

### 2.1 Attributs Clés
*   **Statut :** Online (Actif), Offline (Inactif > 5min), Maintenance (Désactivé manuellement).
*   **Orientation :** Paysage (16:9) ou Portrait (9:16).
*   **Configuration Technique :** Résolution, Code de jumelage (Pairing Code).

### 2.2 Heartbeat & Monitoring
*   Chaque écran envoie un "Heartbeat" (battement de cœur) régulier au serveur (`/api/screen/heartbeat`).
*   **Logique Offline :** Si aucun heartbeat n'est reçu pendant > 5 minutes, l'écran passe automatiquement en statut `Offline`.
*   **Synchronisation :** Le heartbeat renvoie le hash de la playlist courante pour déclencher une mise à jour si nécessaire.

---

## 3. Gestion des Contenus (Content)

### 3.1 Types de Contenu & Priorité
Le Player utilise une file de priorité stricte pour décider quel contenu afficher :

1.  **Broadcast (Priorité 200) :** Messages d'urgence ou annonces système critiques. Interrompt tout le reste.
2.  **Paid Content (Priorité 100) :** Publicités payantes (AdContent) validées.
3.  **Internal Content (Priorité 80) :** Contenu propre à l'organisation (promotions internes).
4.  **AdContent (Priorité 50) :** Publicités réseau (si applicable).
5.  **Filler (Priorité 20) :** Contenu de remplissage par défaut (Météo, News, Logo Agence) pour éviter l'écran noir.

### 3.2 Validation Technique
*   **Vidéos :** Format MP4 obligatoire. Conversion automatique en HLS pour le streaming adaptatif.
*   **Images :** JPG, PNG. Durée d'affichage configurable (défaut : 10s).
*   **Poids Max :** Limité par la configuration serveur (défaut 100MB).

---

## 4. Moteur de Réservation & Pricing (Booking)

### 4.1 Algorithme de Prix
Le prix d'une campagne est calculé dynamiquement selon la formule :

`Prix Total = (Prix de Base du Slot) x (Multiplicateur Période) x (Nombre de Diffusions)`

*   **Prix de Base (TimeSlot) :** Défini par l'écran pour une durée donnée (ex: 15s = 2€).
*   **Multiplicateur (TimePeriod) :** Coefficient selon l'heure de la journée (ex: Heure de pointe 18h-20h = x1.5).
*   **Nombre de Diffusions :** Quantité de passages achetés.

### 4.2 Règles de Commission
*   Chaque écran génère des revenus pour son Organisation propriétaire.
*   Le système calcule automatiquement la part revenant à MOA Digital Agency (frais de service) et la part reversée à l'Organisation.

---

## 5. Facturation & Paiements (Billing)

### 5.1 Workflow de Facture (AdContentInvoice)
1.  **Pending (En attente) :** Facture générée, paiement non reçu.
2.  **Paid (Payée) :** Paiement confirmé (Preuve uploadée ou transaction validée).
3.  **Validated (Validée) :** Facture vérifiée par la comptabilité MOA, commission débloquée.

### 5.2 Preuve de Paiement
*   Les utilisateurs peuvent uploader une preuve de virement (PDF/JPG).
*   La validation manuelle par un Admin change le statut en `Paid`.

---

## 6. Player & Diffusion

### 6.1 Logique de Lecture
*   Le Player est une application Web (HTML/JS) tournant sur le navigateur de l'écran.
*   Il met en cache les contenus pour fonctionner hors-ligne (si supporté par le navigateur).
*   Il interroge l'API `/player/api/playlist` pour obtenir l'ordre de diffusion.

### 6.2 Sécurité Player
*   Authentification par Token de Session.
*   Protection CSRF désactivée pour les endpoints de lecture critiques (Heartbeat, Log Play) pour assurer la fluidité, mais sécurisée par validation d'IP/Device ID.
