# Fonctionnalités Shabaka AdScreen

## Vue d'ensemble

Shabaka AdScreen est une plateforme SaaS permettant aux établissements (bars, restaurants, centres commerciaux) de monétiser leurs écrans publicitaires via un système de location self-service. La plateforme supporte les opérations multi-pays et multi-devises, ainsi qu'un système de diffusion centralisé pour les superadmins.

## Rôles utilisateurs

### 1. Superadmin (Administrateur SaaS)

Gestion globale de la plateforme.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Gestion établissements | Disponible | Créer, modifier, suspendre des établissements |
| **Types établissements** | Disponible | Payant (accès complet) ou Gratuit (fonctionnalités limitées) |
| Configuration commissions | Disponible | Définir le taux de commission par établissement |
| Plans d'abonnement | Disponible | Assigner des plans (basic, premium, enterprise) |
| Multi-devises | Disponible | Support EUR, MAD, XOF, TND |
| Statistiques globales | Disponible | Revenus totaux, écrans actifs, uptime moyen |
| Configuration WhatsApp | Disponible | Numéro pour demandes d'inscription |
| Paramètres SEO | Disponible | Titre, description du site |
| Mode maintenance | Disponible | Activation/désactivation |
| **Diffusion (Broadcast)** | Disponible | Pousser du contenu vers les écrans ciblés |
| Facturation hebdomadaire | Disponible | Génération automatique des factures |
| **Gestion Admins** | Disponible | Créer des administrateurs avec permissions |
| **Permissions granulaires** | Disponible | Accès menu par menu pour chaque admin |
| Liste noire contenus | Prévu | Bloquer des contenus ou IP abusives |
| Audit logs | Prévu | Traçabilité des actions |

### 2. Établissement (Organisation)

Gestion des écrans et contenus pour un établissement.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Gestion écrans | Disponible | Créer, configurer, activer/désactiver des écrans |
| **Contrôle publicités** | Disponible | Activer/désactiver les publicités superadmin |
| Configuration résolution | Disponible | Définir largeur, hauteur, orientation |
| Types de contenu | Disponible | Activer/désactiver images, vidéos |
| Créneaux horaires | Disponible | Définir durées et prix par type de contenu |
| Périodes journée | Disponible | Multiplicateurs de prix (matin, soir, etc.) |
| QR Codes | Disponible | Génération automatique par écran |
| Validation contenus | Disponible | File d'attente, aperçu, validation/refus |
| Contenus fillers | Disponible | Images de remplissage générées automatiquement |
| Contenus internes | Disponible | Promos établissement avec programmation (période + passages total distribués équitablement) |
| **Calcul disponibilités** | Disponible | Même algorithme que les réservations clients (dates, périodes, créneaux) |
| **Overlays/Bandeaux** | Disponible | Textes défilants superposés sur le player |
| Statistiques | Disponible | Revenus par écran/période, diffusions |
| État temps réel | Disponible | Online/offline, dernière activité |

### 3. Client / Annonceur

Accès public via QR code ou lien pour réserver de l'espace publicitaire.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Consultation écran | Disponible | Voir specs, résolution, prix en devise locale |
| Sélection créneau | Disponible | Choisir durée, période, nombre de diffusions |
| Upload contenu | Disponible | Images et vidéos avec validation |
| Validation format | Disponible | Vérification résolution, ratio, durée |
| Calcul prix | Disponible | Prix dynamique selon choix (multi-devise) |
| Suivi réservation | Disponible | Statut en attente, validé, refusé |
| **Reçu thermique** | Disponible | Image style ticket de caisse |
| **Reçu PDF** | Disponible | PDF imprimable |
| Paiement en ligne | Prévu | Intégration Stripe |
| Notifications email | Prévu | Validation, refus, rapports |

### 4. Écran (Player)

Interface de diffusion pour les écrans publicitaires.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Login écran | Disponible | Authentification par code et mot de passe |
| Récupération playlist | Disponible | API JSON des contenus à diffuser |
| Mode plein écran | Disponible | Affichage optimisé fullscreen (F11) |
| Loop automatique | Disponible | Enchaînement des contenus |
| **Overlays temps réel** | Disponible | Affichage des bandeaux défilants |
| **Diffusions (Broadcasts)** | Disponible | Réception des diffusions centralisées |
| Heartbeat | Disponible | Ping régulier pour statut online |
| Logging diffusions | Disponible | Enregistrement des passages |
| **Mode OnlineTV** | Disponible | Streaming M3U/HLS avec overlays actifs |
| **Contrôle audio** | Disponible | Mute/unmute avec bouton et raccourci (M) |
| **Raccourcis clavier** | Disponible | F11: plein écran, M: mute, Espace: pause |

## Détail des fonctionnalités

### Multi-devises

La plateforme supporte 4 devises principales selon le pays de l'établissement :

| Pays | Devise | Symbole | Exemple |
|------|--------|---------|---------|
| France | EUR | € | 2.50 € |
| Maroc | MAD | DH | 25.00 DH |
| Sénégal | XOF | FCFA | 1500 FCFA |
| Tunisie | TND | DT | 8.00 DT |

Les prix sont affichés dans la devise de l'établissement partout : écran de réservation, reçus, statistiques.

### Gestion des écrans

Chaque écran est configurable avec :
- **Nom et localisation** : Identification et géolocalisation
- **Résolution** : Largeur x Hauteur (ex: 1920x1080, 3840x2160)
- **Orientation** : Paysage, portrait ou carré
- **Types acceptés** : Images, vidéos ou les deux
- **Taille max fichier** : Limite en Mo (jusqu'à 200 Mo)
- **Prix par minute** : Base de calcul des créneaux
- **Code unique** : Généré automatiquement pour le QR code

### Créneaux horaires (Time Slots)

Configuration des durées de diffusion avec prix calculés automatiquement :

| Type | Durées disponibles | Calcul prix |
|------|-------------------|-------------|
| Image | 10s, 15s, 30s | prix_par_minute × (durée/60) |
| Vidéo | 15s, 30s, 60s | prix_par_minute × (durée/60) |

### Périodes de la journée (Time Periods)

Multiplicateurs de prix selon l'heure :

| Période | Horaires | Multiplicateur | Usage |
|---------|----------|----------------|-------|
| Matin | 06h-12h | x0.8 | Tarif réduit |
| Midi | 12h-14h | x1.5 | Heure de pointe |
| Après-midi | 14h-18h | x1.0 | Tarif normal |
| Soir | 18h-22h | x1.8 | Prime time |
| Nuit | 22h-06h | x0.5 | Tarif réduit |

**Prix final** = Prix de base × Multiplicateur période

### Système d'overlays (par établissement)

Les overlays permettent d'afficher des informations superposées sur le player :

**Type Bandeau (Ticker)**
- Texte défilant horizontal
- Vitesse de défilement configurable (30-100 px/s)
- Couleurs personnalisables (fond, texte)
- Taille de police ajustable

**Positions**
- Header : En haut de l'écran
- Body : Au centre
- Footer : En bas de l'écran

**Fréquence d'affichage**
- Par durée : Afficher pendant X secondes
- Par passage : Afficher X fois par jour/période

### Types d'établissements

La plateforme permet de distinguer deux types d'établissements :

**Établissement Payant**
- Accès complet à toutes les fonctionnalités
- Réservations, facturation, créneaux, périodes
- Contenus internes et overlays
- Statistiques avancées

**Établissement Gratuit**
- Fonctionnalités limitées aux contenus internes et overlays
- Pas de réservations ni de facturation
- Pas de configuration des créneaux payants
- Commission à 0%

### Contrôle des Publicités Superadmin

Les établissements peuvent contrôler la diffusion des publicités créées par le superadmin sur leurs écrans :

**Option allow_ad_content**
- Activée par défaut (opt-in)
- Toggle accessible dans les paramètres de l'établissement
- Si désactivé, les contenus publicitaires du superadmin ne s'affichent pas sur les écrans de l'établissement
- N'affecte pas les overlays et broadcasts de l'établissement lui-même

| État | Comportement |
|------|--------------|
| Activé (défaut) | Les publicités superadmin s'affichent normalement |
| Désactivé | Les publicités superadmin sont filtrées |

### Gestion des Administrateurs

Le superadmin peut créer d'autres administrateurs avec des permissions granulaires :

| Permission | Description |
|------------|-------------|
| dashboard | Accès au tableau de bord |
| organizations | Gestion des établissements |
| screens | Gestion des écrans |
| broadcasts | Gestion des diffusions |
| stats | Accès aux statistiques |
| billing | Gestion de la facturation |
| registration_requests | Gestion des demandes |
| settings | Paramètres du site |
| users | Gestion des administrateurs |

### Système de diffusion (Broadcast)

Les superadmins peuvent diffuser du contenu vers plusieurs écrans simultanément :

**Types de ciblage**

| Ciblage | Description | Portée |
|---------|-------------|--------|
| Pays | Tous les écrans d'un pays | Large |
| Ville | Tous les écrans d'une ville | Moyenne |
| Établissement | Tous les écrans d'un établissement | Précise |
| Écran | Un écran spécifique | Ciblée |

**Types de diffusion**

| Type | Description | Priorité playlist |
|------|-------------|------------------|
| Overlay | Bandeau défilant superposé | N/A (superposition) |
| Contenu | S'intègre dans la playlist | Configurable (20-200) |

**Types d'overlay disponibles**
- Ticker : Bandeau défilant horizontal
- Image : Image en position fixe
- Corner : Logo/image en coin d'écran

**Modes de programmation**

| Mode | Description | Usage |
|------|-------------|-------|
| Immédiat | Diffusion instantanée dès activation | Annonces urgentes |
| Programmé | Déclenchement à date/heure précise | Événements planifiés |

**Fuseau horaire (NOUVEAU)**

Les diffusions programmées supportent désormais un fuseau horaire cible pour assurer la synchronisation avec les écrans dans différentes régions :

| Région | Fuseaux horaires supportés |
|--------|---------------------------|
| Europe | Paris, London, Berlin, Madrid, Rome, Brussels, Zurich |
| Afrique | Casablanca, Tunis, Algiers, Dakar, Abidjan, Lagos, Johannesburg, Cairo |
| Amérique | New York, Chicago, Los Angeles, Toronto, Sao Paulo |
| Asie/Océanie | Dubai, Riyadh, Tokyo, Shanghai, Singapore, Sydney |

Le fuseau horaire par défaut est Europe/Paris.

**Système de récurrence (NOUVEAU)**

| Type | Description | Exemple |
|------|-------------|---------|
| Unique | Une seule diffusion | Événement ponctuel |
| Quotidien | Répétition chaque jour | Promo du jour |
| Hebdomadaire | Jours de la semaine sélectionnés | Happy Hour vendredi/samedi |
| Mensuel | Répétition mensuelle | Offre du 1er du mois |

**Priorité et Override (NOUVEAU)**

| Priorité | Usage | Override |
|----------|-------|----------|
| 20-50 | Fillers, contenu de fond | Non |
| 80-100 | Contenu standard | Non |
| 100-150 | Contenu prioritaire | Optionnel |
| 150-200 | Contenu urgent | Oui (décale la playlist) |

L'option "Override playlist" permet de décaler temporairement les contenus existants pour insérer la diffusion à l'heure exacte programmée.

**Cascade hiérarchique**
- Sélectionner "France" affecte tous les écrans en France
- Les diffusions s'additionnent aux overlays locaux
- Priorité configurable pour contrôler l'ordre d'affichage

### Génération de reçus

Deux formats disponibles après réservation :

**Reçu Image (Thermique)**
- Style ticket de caisse noir et blanc
- En-tête : Nom établissement + Nom écran
- Numéro de réservation encadré
- Détails : créneau, durée, diffusions
- Tarification avec devise locale
- QR code de vérification
- Footer avec date et statut

**Reçu PDF**
- Format A4 imprimable
- Mêmes informations que l'image
- Compatible imprimantes standards

### Validation des contenus

Règles de validation strictes :
- **Images** : Vérification résolution, ratio exact requis
- **Vidéos** : Extraction durée, rejet si > durée slot choisi
- **Taille** : Respect de la limite configurée par écran

Workflow :
1. Client uploade un contenu
2. Validation automatique des specs techniques
3. File d'attente pour l'établissement
4. Validation ou refus manuel avec motif
5. Notification du client

### Playlist et priorités

Ordre de diffusion (du plus prioritaire au moins prioritaire) :

| Type de contenu | Priorité | Source |
|-----------------|----------|--------|
| **Diffusions (Broadcasts)** | 200 | Superadmin |
| Contenus payants validés | 100 | Clients |
| Contenus internes | 80 | Établissement |
| Fillers / démos | 20 | Auto-généré |

Le player récupère la playlist via API et enchaîne les contenus avec les overlays actifs (locaux + broadcasts).

### Mode OnlineTV (IPTV)

Le mode OnlineTV permet de diffuser des chaînes TV en direct sur les écrans :

**Fonctionnalités**
| Fonction | Description |
|----------|-------------|
| Streaming M3U/HLS | Support des flux M3U, M3U8 via HLS.js |
| Fallback MPEG-TS | Support des flux TS via mpegts.js |
| Bascule instantanée | Changement rapide entre playlist et TV |
| Overlays actifs | Les bandeaux restent visibles pendant la TV |
| Gestion chaînes | Liste personnalisable par établissement |
| Fallback automatique | Repli en cas d'erreur de stream |
| **Contrôle audio** | Audio activé par défaut, mute/unmute disponible |

**Configuration par établissement**
- Activation OnlineTV au niveau de l'établissement
- Activation par écran (chaque écran peut avoir le mode activé ou non)
- URL de la liste M3U configurable
- Sélection de la chaîne active par écran

**Technologies de streaming**
| Bibliothèque | Usage | Formats supportés |
|--------------|-------|-------------------|
| HLS.js | Streaming principal | M3U8, HLS |
| mpegts.js | Fallback streaming | MPEG-TS (.ts) |

**Avantages**
- Garde l'attention des visiteurs quand il n'y a pas de publicité
- Les overlays et diffusions restent visibles
- Bascule automatique ou manuelle entre modes
- Audio synchronisé avec l'état mute/unmute du player

### Contrôle Audio du Player

Le player dispose d'un système de contrôle audio complet :

**État audio**
| État | Description |
|------|-------------|
| Son activé | Audio par défaut au démarrage |
| Mute | Audio désactivé, icône muet affichée |

**Méthodes de contrôle**
| Méthode | Action |
|---------|--------|
| Bouton | Clic sur l'icône audio en bas à droite |
| Raccourci | Touche 'M' pour basculer mute/unmute |

**Synchronisation audio**
- L'état mute est synchronisé entre vidéo et IPTV
- Changement de mode (playlist ↔ TV) préserve l'état audio
- L'icône reflète toujours l'état courant

**Raccourcis clavier du Player**
| Touche | Action |
|--------|--------|
| F11 | Mode plein écran |
| M | Mute / Unmute audio |
| Espace | Pause / Play |

**Écran d'accueil**
L'écran d'accueil affiche les raccourcis clavier disponibles pour guider l'utilisateur.

### Contenus internes (établissement)

Les établissements peuvent créer leurs propres contenus promotionnels :

**Fonctionnalités**
| Fonction | Description |
|----------|-------------|
| Upload fichier | Interface drag & drop avec aperçu temps réel |
| Aperçu résolution | Simulation à la résolution exacte de l'écran |
| Sélection période | Même calendrier que les réservations clients |
| Calcul disponibilités | API identique au système de réservation |
| Distribution équitable | Passages répartis sur les jours de la période |

**Champs**
| Champ | Description |
|-------|-------------|
| Nom | Identification du contenu |
| Priorité | 1-100 (défaut 80, plus haut = plus fréquent) |
| Date début/fin | Période de diffusion |
| Passages total | Nombre total de diffusions sur la période |
| Passages/jour | Calculé automatiquement (ceiling division) |

**Calcul distribution**
```
passages_par_jour = ceil(passages_total / nombre_jours)
```
Exemple : 5 passages sur 7 jours = 1 passage/jour (arrondi supérieur pour ne perdre aucun passage)

### Fillers automatiques

À la création d'un écran, un filler par défaut est généré automatiquement :
- Image avec QR code de réservation
- Texte "Votre publicité ici"
- Dimensions adaptées à l'écran
- Peut être remplacé ou désactivé

### Statistiques

Données disponibles par établissement :
- Nombre de diffusions par contenu
- Revenus par écran, jour, période
- Revenus par devise
- Uptime des écrans
- Temps moyen de validation
- Réservations en attente

### Sélection Pays et Ville

La plateforme intègre un système complet de sélection géographique :

**Données mondiales exhaustives**
- 208 pays avec codes ISO, drapeaux et devises par défaut
- Plus de 4 600 villes réparties sur tous les continents
- Moyenne de 22 villes par pays (minimum 1, maximum 30)
- Chargement dynamique des villes via API AJAX

**Fonctionnalités**
- Sélection du pays lors de la création d'organisation
- Chargement automatique des villes correspondantes
- Recherche avec autocomplétion
- Support multilingue (noms en français)

**Couverture géographique**
| Continent | Pays | Villes (moy.) |
|-----------|------|---------------|
| Afrique | 54+ | 20-30 |
| Europe | 45+ | 20-30 |
| Asie | 48+ | 20-30 |
| Amérique | 35+ | 20-30 |
| Océanie | 14+ | 15-20 |

## Roadmap

### Facturation hebdomadaire

Le système génère des factures chaque semaine via plusieurs mécanismes :

**Processus de facturation**
- Génération on-demand lorsqu'une organisation accède à la page "Factures"
- Endpoint cron disponible (`/billing/cron/generate-invoices`) pour automatisation externe
- Une facture par organisation avec tous les écrans combinés
- Calcul automatique de la commission basée sur le taux de l'organisation

**Configuration cron externe (recommandé)**
```bash
# Ajouter au crontab pour générer les factures chaque dimanche à 23h
59 23 * * 0 curl -X POST https://votre-domaine.com/billing/cron/generate-invoices
```

**Statuts des factures**

| Statut | Description |
|--------|-------------|
| pending | En attente de paiement |
| paid | Payé (preuve uploadée) |
| validated | Validé par superadmin |
| cancelled | Annulé |

**Preuves de paiement**
- Upload par l'organisation (PDF, PNG, JPG)
- Validation par le superadmin
- Historique conservé

**Calculs**
- Commission = Revenu brut × Taux commission organisation
- TVA calculée sur la commission (taux plateforme configurable)
- Total = Commission + TVA

## Roadmap

### Phase 2 (à venir)

- [ ] Intégration paiement Stripe multi-devise
- [ ] Notifications email automatiques
- [ ] WebSocket temps réel pour état écrans
- [ ] Dashboard client avec historique
- [ ] Rapports PDF téléchargeables
- [ ] Overlay type image (logo fixe) pour établissements

### Phase 3 (futur)

- [ ] Marketplace inter-établissements
- [ ] API publique pour intégrations
- [ ] Application mobile player
- [ ] Analytics avancés
- [ ] Multi-langue interface
- [ ] Campagnes programmées multi-écrans

## Limites techniques

| Paramètre | Limite |
|-----------|--------|
| Taille max fichier | Configurable par écran (défaut 50 Mo, max 200 Mo) |
| Formats images | JPEG, PNG, GIF, WebP |
| Formats vidéos | MP4, WebM, MOV |
| Durée vidéo | Doit correspondre au slot choisi |
| Résolution | Doit correspondre exactement à l'écran |
| Devises supportées | EUR, MAD, XOF, TND (+ 200 autres via pays) |
| Pays supportés | 208 pays (couverture mondiale) |
| Villes par pays | 1-30 (moyenne 22) |
| Diffusions simultanées | Illimité |
| Ciblages par diffusion | 1 (pays, ville, établissement ou écran) |
