# Fonctionnalités Shabaka AdScreen

## Vue d'ensemble

Shabaka AdScreen est une plateforme SaaS permettant aux établissements (bars, restaurants, centres commerciaux) de monétiser leurs écrans publicitaires via un système de location self-service. La plateforme supporte les opérations multi-pays et multi-devises.

## Rôles utilisateurs

### 1. Superadmin (Administrateur SaaS)

Gestion globale de la plateforme.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Gestion établissements | ✅ Disponible | Créer, modifier, suspendre des établissements |
| Configuration commissions | ✅ Disponible | Définir le taux de commission par établissement |
| Plans d'abonnement | ✅ Disponible | Assigner des plans (basic, premium, enterprise) |
| Multi-devises | ✅ Disponible | Support EUR, MAD, XOF, TND |
| Statistiques globales | ✅ Disponible | Revenus totaux, écrans actifs, uptime moyen |
| Configuration WhatsApp | ✅ Disponible | Numéro pour demandes d'inscription |
| Paramètres SEO | ✅ Disponible | Titre, description du site |
| Mode maintenance | ✅ Disponible | Activation/désactivation |
| Liste noire contenus | 🔄 Prévu | Bloquer des contenus ou IP abusives |
| Audit logs | 🔄 Prévu | Traçabilité des actions |

### 2. Établissement (Organisation)

Gestion des écrans et contenus pour un établissement.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Gestion écrans | ✅ Disponible | Créer, configurer, activer/désactiver des écrans |
| Configuration résolution | ✅ Disponible | Définir largeur, hauteur, orientation |
| Types de contenu | ✅ Disponible | Activer/désactiver images, vidéos |
| Créneaux horaires | ✅ Disponible | Définir durées et prix par type de contenu |
| Périodes journée | ✅ Disponible | Multiplicateurs de prix (matin, soir, etc.) |
| QR Codes | ✅ Disponible | Génération automatique par écran |
| Validation contenus | ✅ Disponible | File d'attente, aperçu, validation/refus |
| Contenus fillers | ✅ Disponible | Images de remplissage générées automatiquement |
| Contenus internes | ✅ Disponible | Promos établissement prioritaires |
| **Overlays/Bandeaux** | ✅ Disponible | Textes défilants superposés sur le player |
| Statistiques | ✅ Disponible | Revenus par écran/période, diffusions |
| État temps réel | ✅ Disponible | Online/offline, dernière activité |

### 3. Client / Annonceur

Accès public via QR code ou lien pour réserver de l'espace publicitaire.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Consultation écran | ✅ Disponible | Voir specs, résolution, prix en devise locale |
| Sélection créneau | ✅ Disponible | Choisir durée, période, nombre de diffusions |
| Upload contenu | ✅ Disponible | Images et vidéos avec validation |
| Validation format | ✅ Disponible | Vérification résolution, ratio, durée |
| Calcul prix | ✅ Disponible | Prix dynamique selon choix (multi-devise) |
| Suivi réservation | ✅ Disponible | Statut en attente, validé, refusé |
| **Reçu thermique** | ✅ Disponible | Image style ticket de caisse |
| **Reçu PDF** | ✅ Disponible | PDF imprimable |
| Paiement en ligne | 🔄 Prévu | Intégration Stripe |
| Notifications email | 🔄 Prévu | Validation, refus, rapports |

### 4. Écran (Player)

Interface de diffusion pour les écrans publicitaires.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Login écran | ✅ Disponible | Authentification par code et mot de passe |
| Récupération playlist | ✅ Disponible | API JSON des contenus à diffuser |
| Mode plein écran | ✅ Disponible | Affichage optimisé fullscreen |
| Loop automatique | ✅ Disponible | Enchaînement des contenus |
| **Overlays temps réel** | ✅ Disponible | Affichage des bandeaux défilants |
| Heartbeat | ✅ Disponible | Ping régulier pour statut online |
| Logging diffusions | ✅ Disponible | Enregistrement des passages |

## Détail des fonctionnalités

### Multi-devises

La plateforme supporte 4 devises selon le pays de l'établissement :

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

### Système d'overlays

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

Ordre de diffusion :
1. **Contenus payants validés** (priorité 100)
2. **Contenus internes** (priorité 80)
3. **Fillers / démos** (priorité 20)

Le player récupère la playlist via API et enchaîne les contenus avec les overlays actifs.

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

## Roadmap

### Phase 2 (à venir)

- [ ] Intégration paiement Stripe multi-devise
- [ ] Notifications email automatiques
- [ ] WebSocket temps réel pour état écrans
- [ ] Dashboard client avec historique
- [ ] Rapports PDF téléchargeables
- [ ] Overlay type image (logo fixe)

### Phase 3 (futur)

- [ ] Marketplace inter-établissements
- [ ] API publique pour intégrations
- [ ] Application mobile player
- [ ] Analytics avancés
- [ ] Multi-langue interface
- [ ] Campagnes programmées

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
