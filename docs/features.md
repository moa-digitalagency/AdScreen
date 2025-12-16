# Guide des fonctionnalités

Ce document décrit tout ce que Shabaka AdScreen sait faire, fonctionnalité par fonctionnalité.

## Les quatre types d'utilisateurs

Shabaka AdScreen distingue quatre rôles avec des interfaces et des droits différents.

### L'opérateur (Super-administrateur)

C'est vous, ou votre équipe. L'opérateur contrôle l'ensemble de la plateforme depuis l'interface `/admin`.

**Gestion des établissements**
- Créer, modifier, suspendre des établissements
- Définir le taux de commission de chaque établissement (pourcentage prélevé sur les revenus)
- Assigner des plans d'abonnement (basic, premium, enterprise)
- Distinguer les établissements payants (accès complet) des établissements gratuits (fonctionnalités limitées)

**Gestion des administrateurs**
- Créer d'autres administrateurs pour déléguer certaines tâches
- Attribuer des permissions granulaires : chaque admin n'accède qu'aux menus autorisés
- Les permissions disponibles : tableau de bord, établissements, écrans, diffusions, statistiques, facturation, demandes d'inscription, paramètres, gestion des utilisateurs

**Diffusions centralisées**
- Pousser du contenu (bandeau défilant ou contenu dans la playlist) vers n'importe quel écran
- Cibler par pays (tous les écrans de France), par ville (tous les écrans de Paris), par établissement ou par écran spécifique
- Programmer des diffusions à une date et heure précises
- Configurer des récurrences : quotidien, hebdomadaire (certains jours), mensuel
- Définir une priorité pour contrôler l'ordre d'affichage
- Activer le mode "override" pour interrompre la playlist normale

**Facturation**
- Les factures sont générées automatiquement chaque semaine (lundi à dimanche)
- Chaque facture calcule la commission due par l'établissement
- Les établissements uploadent leurs preuves de paiement
- L'opérateur valide les preuves et marque les factures comme réglées

**Paramètres globaux**
- Numéro WhatsApp pour recevoir les demandes d'inscription
- Paramètres SEO (titre, description du site)
- Mode maintenance (désactive temporairement l'accès public)
- Commission par défaut pour les nouveaux établissements

**Statistiques globales**
- Revenus totaux par devise
- Nombre d'écrans actifs
- Uptime moyen du réseau
- Réservations en attente de validation

### L'établissement (Manager)

Chaque établissement gère ses propres écrans depuis l'interface `/org`.

**Gestion des écrans**
- Créer et configurer des écrans avec nom, emplacement, résolution
- Définir l'orientation : paysage (16:9), portrait (9:16) ou personnalisée
- Activer/désactiver les types de contenu acceptés (images, vidéos, ou les deux)
- Fixer le prix par minute et la taille maximale des fichiers

**Configuration des créneaux**
- Définir les durées disponibles : 10s, 15s, 30s pour les images ; 15s, 30s, 60s pour les vidéos
- Le prix de chaque créneau est calculé automatiquement à partir du prix par minute

**Périodes horaires**
- Définir des multiplicateurs de prix selon l'heure de la journée
- Exemple classique : matin (x0.8), midi (x1.5), après-midi (x1.0), soir (x1.8), nuit (x0.5)
- Le prix final = prix du créneau × multiplicateur de la période

**Validation des contenus**
- Les contenus soumis par les annonceurs arrivent dans une file d'attente
- Chaque contenu peut être prévisualisé à la résolution exacte de l'écran
- L'établissement valide ou refuse avec un motif explicite
- Les contenus validés passent en diffusion, les refusés sont archivés

**Contenus internes**
- L'établissement peut créer ses propres contenus promotionnels
- Ces contenus utilisent le même système de programmation que les réservations clients
- Ils sont répartis équitablement sur la période choisie

**Fillers (contenus de remplissage)**
- À la création d'un écran, un filler est généré automatiquement
- Il affiche le QR code de réservation avec le message "Votre publicité ici"
- Les fillers sont diffusés quand il n'y a pas d'autre contenu

**Overlays et bandeaux**
- Créer des bandeaux défilants qui s'affichent par-dessus le contenu principal
- Personnaliser les couleurs, la vitesse de défilement, la taille du texte
- Positionner en haut, au centre ou en bas de l'écran
- Définir la fréquence d'affichage (pendant X secondes ou X fois par jour)

**Mode OnlineTV**
- Activer la diffusion de chaînes TV en direct quand il n'y a pas de publicité
- Configurer une URL de liste M3U
- Les overlays restent actifs pendant la diffusion TV
- Basculer instantanément entre mode playlist et mode TV

**Contrôle des publicités opérateur**
- Par défaut, les établissements acceptent les publicités diffusées par l'opérateur
- Cette option peut être désactivée dans les paramètres
- N'affecte pas les bandeaux et diffusions propres à l'établissement

**Statistiques**
- Revenus par écran, par jour, par période
- Nombre de diffusions par contenu
- Uptime des écrans
- Temps moyen de validation des contenus

**QR Codes**
- Chaque écran génère automatiquement un QR code unique
- Le QR code pointe vers la page de réservation de cet écran
- Peut être téléchargé et imprimé

### L'annonceur (Client)

Les annonceurs accèdent via le QR code ou un lien direct vers `/book/<code>`.

**Consultation**
- Voir les caractéristiques de l'écran : résolution, orientation, types acceptés
- Consulter les prix dans la devise locale
- Voir les disponibilités par période

**Réservation**
- Choisir le type de contenu (image ou vidéo)
- Sélectionner la durée du créneau
- Choisir la période horaire (matin, midi, soir, etc.)
- Définir le nombre de diffusions souhaité
- Sélectionner les dates de diffusion

**Upload**
- Uploader une image (JPEG, PNG, GIF, WebP) ou une vidéo (MP4, WebM, MOV)
- Le système vérifie automatiquement que le contenu respecte la résolution et la durée
- Les contenus non conformes sont rejetés avec un message explicatif

**Confirmation**
- Le prix total est affiché avant validation
- Après soumission, un numéro de réservation unique est attribué
- Deux formats de reçu sont disponibles : image (style ticket thermique) et PDF

**Suivi**
- Consulter le statut de la réservation : en attente, validé ou refusé
- Si refusé, le motif est affiché

### L'écran (Player)

L'interface de diffusion fonctionne sur `/player`.

**Authentification**
- Connexion avec le code unique de l'écran et un mot de passe
- Session persistante pour éviter les reconnexions

**Playlist**
- Récupération automatique des contenus à diffuser
- Ordre basé sur la priorité : diffusions opérateur (200), contenus payants (100), contenus internes (80), fillers (20)
- Rafraîchissement régulier pour intégrer les nouveaux contenus

**Diffusion**
- Enchaînement automatique des contenus
- Les images sont affichées pendant la durée du créneau
- Les vidéos sont lues intégralement (si plus courtes que le créneau, la dernière image reste affichée)

**Overlays**
- Affichage des bandeaux défilants par-dessus le contenu
- Les overlays de l'opérateur ont priorité sur ceux de l'établissement
- Affichage simultané possible selon les positions

**Mode OnlineTV**
- Quand activé, le player bascule sur le flux TV
- Les overlays continuent de s'afficher
- L'audio est synchronisé avec l'état mute/unmute

**Contrôles**
- Mode plein écran avec F11
- Mute/unmute avec la touche M ou le bouton à l'écran
- Pause/play avec la barre d'espace

**Heartbeat**
- Signal envoyé toutes les 30 secondes pour confirmer que l'écran fonctionne
- Permet le monitoring en temps réel depuis les interfaces admin et établissement

**Mode hors ligne**
- Les contenus sont mis en cache automatiquement
- Si la connexion est perdue, la lecture continue avec les contenus cachés
- Les statistiques de lecture sont mises en file d'attente et envoyées au retour de la connexion

**Streaming adaptatif**
- En mode OnlineTV, la qualité vidéo s'adapte automatiquement à la bande passante
- Un indicateur affiche la résolution actuelle (1080p, 720p, 480p, etc.)
- Pas de coupure : la qualité baisse plutôt que de couper

## Devises et pays

La plateforme supporte nativement 4 devises :

| Devise | Symbole | Pays principaux |
|--------|---------|-----------------|
| EUR (Euro) | € | France, Belgique, Allemagne... |
| MAD (Dirham marocain) | DH | Maroc |
| XOF (Franc CFA) | FCFA | Sénégal, Côte d'Ivoire, Mali... |
| TND (Dinar tunisien) | DT | Tunisie |

Chaque établissement est associé à un pays et une devise. Tous les prix, reçus et statistiques s'affichent dans cette devise.

La base de données contient 208 pays et plus de 4 600 villes, permettant une couverture mondiale.

## Système de diffusion (Broadcast)

Les diffusions centralisées sont un outil puissant pour l'opérateur.

**Ciblage hiérarchique**
- Par pays : touche tous les écrans du pays
- Par ville : touche tous les écrans de la ville
- Par établissement : touche tous les écrans de l'établissement
- Par écran : touche un écran spécifique

**Types de diffusion**
- Overlay : bandeau défilant, image fixe ou logo en coin, affiché par-dessus le contenu
- Contenu : s'insère dans la playlist avec une priorité configurable

**Programmation**
- Immédiat : la diffusion démarre dès l'activation
- Programmé : déclenchement à une date et heure précises
- Fuseau horaire : 25+ zones supportées pour synchroniser avec les écrans locaux

**Récurrence**
- Unique : une seule diffusion
- Quotidien : répétition chaque jour
- Hebdomadaire : sélection des jours (lundi, mardi, etc.)
- Mensuel : répétition le même jour chaque mois

**Priorité et override**
- Priorité de 20 à 200 (plus haut = plus fréquent dans la playlist)
- Option "override" pour décaler temporairement les contenus existants

## Calcul des prix

Le prix d'une diffusion se calcule ainsi :

1. **Prix de base** = prix par minute de l'écran × (durée en secondes / 60)
2. **Prix avec période** = prix de base × multiplicateur de la période horaire
3. **Prix total** = prix avec période × nombre de diffusions

Exemple concret :
- Écran à 2€/minute
- Créneau de 15 secondes = 0,50€ par diffusion
- Période "soir" avec multiplicateur x1.8 = 0,90€ par diffusion
- 100 diffusions = 90€ total

## Validation des contenus

Le système valide automatiquement plusieurs critères :

**Pour les images**
- Format accepté : JPEG, PNG, GIF, WebP
- Résolution exacte requise (doit correspondre à l'écran)
- Taille maximale respectée

**Pour les vidéos**
- Format accepté : MP4, WebM, MOV
- Durée ≤ durée du créneau choisi
- Résolution vérifiée
- Taille maximale respectée

Les contenus non conformes sont rejetés automatiquement avec un message explicatif. Les contenus conformes passent en file d'attente pour validation manuelle par l'établissement.

## Reçus de réservation

Après une réservation, l'annonceur peut télécharger son reçu dans deux formats :

**Image thermique**
- Style ticket de caisse noir et blanc
- En-tête avec le nom de l'établissement et de l'écran
- Numéro de réservation encadré
- Détails : créneau, durée, nombre de diffusions
- Prix dans la devise locale
- QR code de vérification
- Date et statut

**PDF**
- Format A4 imprimable
- Mêmes informations que l'image
- Compatible avec toutes les imprimantes

## Facturation hebdomadaire

Le système de facturation fonctionne par cycle hebdomadaire (lundi à dimanche).

**Génération**
- Automatique lorsqu'un établissement accède à sa page de factures
- Ou via un endpoint pour automatisation externe

**Contenu de la facture**
- Période couverte
- Revenus bruts de l'établissement
- Commission calculée (revenus × taux de commission)
- TVA sur la commission
- Total à reverser

**Workflow**
1. Facture générée avec statut "en attente"
2. L'établissement uploade sa preuve de paiement
3. L'opérateur vérifie et valide
4. La facture passe en statut "validée"

## Contenu publicitaire de l'opérateur (Ad Content)

L'opérateur peut créer des campagnes publicitaires ciblées.

**Création**
- Nom et description de la campagne
- Sélection des écrans cibles (par pays, ville, établissement ou écran)
- Upload du contenu (image ou vidéo)
- Dates de début et fin
- Nombre de diffusions quotidiennes

**Suivi**
- Statistiques de diffusion par écran
- Facturation aux annonceurs
- Export des rapports

**Contrôle par l'établissement**
- Chaque établissement peut désactiver cette fonctionnalité
- Dans ce cas, les contenus de l'opérateur ne s'affichent pas sur ses écrans

## Données géographiques

Le fichier `utils/world_data.py` contient une base de données géographique complète :

- 208 pays avec code ISO, drapeau, continent et devise par défaut
- Plus de 4 600 villes (1 à 30 par pays, moyenne de 22)
- Couverture de tous les continents

L'API `/api/cities/<country_code>` retourne la liste des villes pour un pays donné, utilisée pour les formulaires avec autocomplétion.

## Fonctionnalités prévues

Ces fonctionnalités ne sont pas encore disponibles mais sont planifiées :

- Paiement en ligne (intégration Stripe)
- Notifications email (validation, refus, rapports)
- Liste noire de contenus
- Audit logs (traçabilité des actions)
