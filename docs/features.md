# Fonctionnalités AdScreen

## Vue d'ensemble

AdScreen est une plateforme SaaS permettant aux établissements de monétiser leurs écrans publicitaires via un système de location self-service.

## Rôles utilisateurs

### 1. Superadmin (Administrateur SaaS)

Gestion globale de la plateforme.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Gestion établissements | Disponible | Créer, modifier, suspendre des établissements |
| Configuration commissions | Disponible | Définir le taux de commission par établissement |
| Plans d'abonnement | Disponible | Assigner des plans (basic, premium, enterprise) |
| Statistiques globales | Disponible | Revenus totaux, écrans actifs, uptime moyen |
| Liste noire contenus | Prévu | Bloquer des contenus ou IP abusives |
| Audit logs | Prévu | Traçabilité des actions |

### 2. Établissement (Organisation)

Gestion des écrans et contenus pour un établissement.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Gestion écrans | Disponible | Créer, configurer, activer/désactiver des écrans |
| Configuration résolution | Disponible | Définir largeur, hauteur, orientation |
| Types de contenu | Disponible | Activer/désactiver images, vidéos |
| Créneaux horaires | Disponible | Définir durées et prix par type de contenu |
| Périodes journée | Disponible | Multiplicateurs de prix (matin, soir, etc.) |
| QR Codes | Disponible | Génération automatique par écran |
| Validation contenus | Disponible | File d'attente, aperçu, validation/refus |
| Contenus fillers | Disponible | Images/vidéos de remplissage |
| Contenus internes | Disponible | Promos établissement prioritaires |
| Statistiques | Disponible | Revenus par écran/période, diffusions |
| État temps réel | Disponible | Online/offline, dernière activité |

### 3. Client / Annonceur

Accès public via QR code ou lien pour réserver de l'espace publicitaire.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Consultation écran | Disponible | Voir specs, résolution, prix, disponibilités |
| Sélection créneau | Disponible | Choisir durée, période, nombre de diffusions |
| Upload contenu | Disponible | Images et vidéos avec validation |
| Validation format | Disponible | Vérification résolution, ratio, durée |
| Calcul prix | Disponible | Prix dynamique selon choix |
| Suivi réservation | Disponible | Statut en attente, validé, refusé |
| Paiement en ligne | Prévu | Intégration Stripe |
| Notifications email | Prévu | Validation, refus, rapports |

### 4. Écran (Player)

Interface de diffusion pour les écrans publicitaires.

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Login écran | Disponible | Authentification par code et mot de passe |
| Récupération playlist | Disponible | API JSON des contenus à diffuser |
| Mode plein écran | Disponible | Affichage optimisé fullscreen |
| Loop automatique | Disponible | Enchaînement des contenus |
| Heartbeat | Disponible | Ping régulier pour statut online |
| Logging diffusions | Disponible | Enregistrement des passages |

## Détail des fonctionnalités

### Gestion des écrans

Chaque écran est configurable avec :
- **Nom et localisation** : Identification et géolocalisation
- **Résolution** : Largeur x Hauteur (ex: 1920x1080)
- **Orientation** : Paysage, portrait ou carré
- **Types acceptés** : Images, vidéos ou les deux
- **Taille max fichier** : Limite en Mo
- **Code unique** : Généré automatiquement pour le QR code

### Créneaux horaires (Time Slots)

Configuration des durées de diffusion :
- Par type de contenu (image ou vidéo)
- Avec durée en secondes (5s, 10s, 15s, 30s...)
- Et prix par diffusion

Exemple :
| Type | Durée | Prix |
|------|-------|------|
| Image | 10s | 0,80 € |
| Vidéo | 30s | 3,50 € |

### Périodes de la journée (Time Periods)

Multiplicateurs de prix selon l'heure :
- Définir des tranches horaires
- Appliquer un coefficient multiplicateur

Exemple :
| Période | Horaires | Multiplicateur |
|---------|----------|----------------|
| Soir | 18h-22h | x1.8 |

Prix final = Prix de base × Multiplicateur

### Validation des contenus

Règles de validation strictes :
- **Images** : Vérification résolution, ratio exact
- **Vidéos** : Extraction durée, rejet si > slot choisi
- **Taille** : Respect de la limite configurée

Workflow :
1. Client uploade un contenu
2. Validation automatique des specs techniques
3. File d'attente pour l'établissement
4. Validation ou refus manuel avec motif

### Playlist et priorités

Ordre de diffusion :
1. **Contenus payants** (priorité 100)
2. **Contenus internes** (priorité 80)
3. **Fillers / démos** (priorité 20)

Le player récupère la playlist via API et enchaîne les contenus.

### Statistiques

Données disponibles :
- Nombre de diffusions par contenu
- Revenus par écran, jour, période
- Uptime des écrans
- Temps moyen de validation

## Roadmap

### Phase 2 (à venir)

- [ ] Intégration paiement Stripe
- [ ] Notifications email automatiques
- [ ] WebSocket temps réel pour état écrans
- [ ] Dashboard client avec historique
- [ ] Rapports PDF téléchargeables

### Phase 3 (futur)

- [ ] Marketplace inter-établissements
- [ ] API publique pour intégrations
- [ ] Application mobile player
- [ ] Analytics avancés
- [ ] Multi-langue

## Limites techniques

- Taille max fichier : Configurable par écran (défaut 50 Mo)
- Formats images : JPEG, PNG, GIF, WebP
- Formats vidéos : MP4, WebM, MOV
- Durée vidéo : Doit correspondre au slot choisi
- Résolution : Doit correspondre exactement à l'écran (pas de redimensionnement)
