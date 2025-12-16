# Algorithmes métier

Ce document explique la logique de calcul utilisée par Shabaka AdScreen pour les prix, les disponibilités et la diffusion des contenus.

## Calcul des prix

### Principe de base

Chaque écran a un **prix par minute** défini par l'établissement. Tout le reste en découle.

**Exemple** : Un écran à 2€/minute

### Créneaux horaires

Les créneaux (time slots) sont définis en secondes. Le prix d'un créneau se calcule ainsi :

```
Prix du créneau = Prix par minute × (Durée en secondes / 60)
```

| Durée | Calcul | Prix |
|-------|--------|------|
| 10 secondes | 2€ × (10/60) | 0,33€ |
| 15 secondes | 2€ × (15/60) | 0,50€ |
| 30 secondes | 2€ × (30/60) | 1,00€ |
| 60 secondes | 2€ × (60/60) | 2,00€ |

### Multiplicateurs de période

Chaque période de la journée a un multiplicateur qui ajuste le prix :

| Période | Horaires | Multiplicateur | Logique |
|---------|----------|----------------|---------|
| Matin | 06h-12h | ×0,8 | Moins d'affluence |
| Midi | 12h-14h | ×1,5 | Heure de pointe |
| Après-midi | 14h-18h | ×1,0 | Tarif de référence |
| Soir | 18h-22h | ×1,8 | Prime time |
| Nuit | 22h-06h | ×0,5 | Tarif réduit |

**Prix avec période** = Prix du créneau × Multiplicateur

Exemple : Créneau de 15 secondes (0,50€) en soirée (×1,8) = 0,90€

### Prix total d'une réservation

```
Prix total = Prix avec période × Nombre de diffusions
```

Exemple : 100 diffusions à 0,90€ = 90€

## Calcul des disponibilités

### Capacité d'une période

Pour calculer combien de diffusions sont disponibles, on part du temps total de la période.

**Exemple** : Période "matin" de 6h à 12h = 6 heures = 21 600 secondes

```
Nombre de créneaux disponibles = Temps total / Durée du créneau
```

Pour des créneaux de 15 secondes : 21 600 / 15 = 1 440 diffusions possibles

### Impact des réservations existantes

Quand une réservation est faite, on soustrait le temps occupé :

```
Créneaux restants = (Temps total - Temps réservé) / Durée du créneau
```

Exemple :
- Période matin : 21 600 secondes
- Réservation existante : 100 × 15 secondes = 1 500 secondes
- Temps restant : 21 600 - 1 500 = 20 100 secondes
- Créneaux disponibles : 20 100 / 15 = 1 340 diffusions

### Calcul sur plusieurs jours

Pour une réservation sur plusieurs jours, on calcule les disponibilités pour chaque jour et période, puis on somme.

```
Disponibilité totale = Σ (disponibilité par jour × nombre de jours)
```

## Répartition équitable des diffusions

Quand un client réserve 100 diffusions sur 5 jours, on ne les met pas toutes le premier jour. On les répartit équitablement.

### Algorithme de distribution

```
Diffusions par jour = ceil(Diffusions totales / Nombre de jours)
```

La fonction `ceil` (arrondi supérieur) garantit qu'on ne perd aucune diffusion.

Exemple :
- 100 diffusions sur 7 jours
- 100 / 7 = 14,28
- ceil(14,28) = 15 diffusions par jour
- 15 × 7 = 105 → les 5 dernières diffusions ne seront pas utilisées (le système s'arrête à 100)

### Espacement des diffusions

Dans une période donnée, les diffusions sont espacées uniformément.

```
Intervalle = Durée de la période / Nombre de diffusions
```

Exemple :
- Période matin : 6 heures = 21 600 secondes
- 15 diffusions de 15 secondes
- Intervalle : 21 600 / 15 = 1 440 secondes = 24 minutes

Les diffusions sont placées à 6h00, 6h24, 6h48, 7h12, etc.

## Lecture des contenus

### Ordre de la playlist

La playlist est triée par priorité décroissante :

| Type | Priorité | Source |
|------|----------|--------|
| Diffusions opérateur | 200 | Broadcasts avec override |
| Contenus payants | 100 | Réservations clients |
| Contenus internes | 80 | Établissement |
| Contenus publicitaires opérateur | 60 | AdContent |
| Fillers | 20 | Générés automatiquement |

À priorité égale, l'ordre est déterminé par la date de création.

### Durée d'affichage

**Images** : Affichées pendant la durée du créneau réservé (10, 15 ou 30 secondes).

**Vidéos** : Lues intégralement. Si la vidéo est plus courte que le créneau, la dernière image reste affichée jusqu'à atteindre la durée totale.

Exemple : Vidéo de 13 secondes dans un créneau de 15 secondes → 13 secondes de vidéo + 2 secondes sur la dernière image.

### Épuisement des diffusions

Chaque réservation a un quota de diffusions. À chaque passage :

1. Le player signale la diffusion au serveur
2. Le compteur de diffusions effectuées est incrémenté
3. Quand le quota est atteint, le contenu est retiré de la playlist
4. Le serveur répond `exhausted: true` pour confirmer

## Mode OnlineTV

Quand le mode OnlineTV est activé pour un écran :

1. Le player détecte `mode: "iptv"` dans la réponse de l'API playlist
2. Il arrête la lecture de la playlist
3. Il démarre le flux HLS configuré
4. Les overlays (locaux et broadcasts) restent affichés par-dessus
5. Les heartbeats continuent normalement

### Fallback

Si le flux HLS échoue :
1. HLS.js tente une récupération automatique (8 essais)
2. Si HLS échoue, mpegts.js prend le relais pour les flux MPEG-TS
3. Si tout échoue, un message d'erreur s'affiche
4. L'établissement peut repasser en mode playlist manuellement

## Streaming adaptatif (ABR)

Le player OnlineTV utilise l'Adaptive Bitrate Streaming pour ajuster la qualité vidéo en temps réel.

### Estimation de la bande passante

L'algorithme EWMA (Exponentially Weighted Moving Average) estime la bande passante disponible :

```
Nouvelle estimation = α × Mesure actuelle + (1-α) × Estimation précédente
```

Deux coefficients sont utilisés :
- Fast (α = 0.33) pour réagir rapidement aux changements
- Slow (α = 0.11) pour une moyenne stable

### Sélection de la qualité

Le player choisit la qualité maximale qui tient dans 95% de la bande passante estimée.

Pour monter en qualité, il faut atteindre 70% du seuil supérieur (pour éviter les oscillations).

### Buffers

| Paramètre | Valeur | Rôle |
|-----------|--------|------|
| Buffer arrière | 60 secondes | Permet de revenir en arrière |
| Buffer avant | 30-120 secondes | Anticipe les variations de débit |
| Taille max | 60 Mo | Limite la consommation mémoire |

### Récupération d'erreurs

En cas d'erreur réseau :
- 8 tentatives par fragment
- Délai de 500 ms entre les tentatives
- Si un fragment échoue, passage à une qualité inférieure
- Pas d'interruption visible pour l'utilisateur

### Indicateur de qualité

L'indicateur affiche :
- La résolution actuelle (720p, 1080p, etc.)
- Un badge de qualité (FHD, HD, SD, LD, LOW)
- Une barre colorée selon la bande passante :
  - Vert : >5 Mbps
  - Jaune : 2-5 Mbps
  - Orange : 1-2 Mbps
  - Rouge : <1 Mbps

## Contrôle de l'audio

### État par défaut

L'audio est **activé** par défaut. C'est un choix pour les établissements où le son fait partie de l'expérience.

### Synchronisation

L'état mute/unmute est partagé entre :
- Les vidéos de la playlist
- Le flux IPTV

Quand on bascule de la playlist vers l'IPTV (ou inversement), l'état audio est conservé.

### Contrôles

- Bouton visuel en bas à droite de l'écran
- Touche M pour basculer mute/unmute
- L'icône change selon l'état (volume-up / volume-mute)

## Contrôle des publicités opérateur

Les établissements peuvent refuser les publicités diffusées par l'opérateur (AdContent).

### Paramètre `allow_ad_content`

- Par défaut : `true` (opt-in)
- Modifiable dans les paramètres de l'établissement
- Affecte uniquement les contenus AdContent, pas les overlays ni les broadcasts

### Filtrage

Quand la playlist est générée :
1. On vérifie si l'établissement autorise les publicités opérateur
2. Si non, les contenus AdContent ciblant cet établissement (ou son pays/ville) sont exclus
3. Les overlays et broadcasts continuent de s'afficher

### Ciblage concerné

Le paramètre `allow_ad_content` est vérifié pour tous les types de ciblage :
- Ciblage par pays → Vérifié pour chaque établissement du pays
- Ciblage par ville → Vérifié pour chaque établissement de la ville
- Ciblage par établissement → Vérifié pour l'établissement ciblé
- Ciblage par écran → Vérifié pour l'établissement propriétaire de l'écran

## Contenus internes

Les établissements peuvent créer leurs propres contenus promotionnels.

### Programmation

Comme pour les réservations clients :
- Date de début et de fin
- Heures de début et de fin (08h-22h par défaut)
- Nombre total de passages

### Distribution

```
Passages par jour = ceil(Passages totaux / Nombre de jours)
```

Les passages sont répartis équitablement sur la période choisie.

### Priorité

Les contenus internes ont une priorité de 80, entre les contenus payants (100) et les fillers (20). Ils s'affichent donc régulièrement, mais les publicités payantes restent prioritaires.
