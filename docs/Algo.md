ALGORITHME DE RESERVATION ET PLAYLIST
=====================================

LOGIQUE PRINCIPALE
------------------
1. PRIX BASE : Établissement fixe PRIX_PAR_MINUTE (ex: 2€/min) pour son écran
2. SLOTS : Établissement crée plages en SECONDES (10s, 15s, 30s) pour image/vidéo
3. PRIX_AUTO : Prix_slot = (duree_secondes / 60) * prix_par_minute
   Exemple: slot 15s à 2€/min = (15/60)*2 = 0.50€ par diffusion

4. RESERVATION CLIENT :
   - Remplit infos (nom, email, tel)
   - Choisit TYPE (image/vidéo) + SLOT (15s)
   - Sélectionne DATES (ex: 1-5 décembre)
   - Système ANALYSE playlist existante → affiche DISPOS LIBRES

5. CALCUL DISPONIBILITE :
   - Pour chaque jour de la période :
     - Divise en PERIODES (matin:6-12h, midi:12-14h, soir:18-22h etc)
     - Compte secondes LIBRES par période (60min*60s = 3600s disponibles)
     - Soustrait slots RESERVES existants
     - Affiche slots libres : "15s dispo: 240 fois dans matin"

6. CHOIX CLIENT :
   - "Je veux 100 passages de 15s dans matin 1-5 déc"
   - COUT_TOTAL = 100 * 0.50€ = 50€
   - Système RESERVE 100*15s = 1500 secondes EQUITABLEMENT répartis

7. REPARTITION EQUITABLE :
   - 5 jours = 100 passages → 20 passages/jour
   - Matin = 6h = 21600s → 20*15s = 300s occupés (1.4% capacité)
   - Algo place les 20 passages uniformément dans les 6h (toutes les 18min)

8. PROCHAINES RESERVATIONS :
   - Recalcule dispos en IGNORANT les 1500s réservés
   - Ex: matin jour1 : 21600s - 300s = 21300s libres → 1420 slots 15s dispo

==========================
Règle pour lecteur de visionnage
==========================

- Si c'est une image, elle est afficher dans la durer du slot choisie
- Si c'est une vidéo, meme si elle n'a pas les secondes totales réservées (exemple video est de 13s mais slot réservé est de 15s, le lecteur va lire la video et garder le dernier frame a l’écran jusqu'a pour 2s supplémentaire pour atteindre 15s réglementaire ainsi de suite.

=================
EXEMPLE CONCRET
=================
ÉCRAN : Prix 2€/min, slot 15s → 0.50€/diffusion
CLIENT1 : 100 passages matin 1-5 déc → 1500s → 50€

Jour 1 matin (6h=21600s):
- Places 20 slots 15s → 300s occupés
- Positions: 6h05, 6h23, 6h41, 6h59... toutes les 18min

CLIENT2 arrive après :
- Matin jour1: 21600s - 300s = 21300s libres
- 21300/15 = 1420 slots 15s DISPONIBLES

=================
MODE ONLINETV
=================

LOGIQUE ONLINETV
----------------
1. ACTIVATION : L'établissement active OnlineTV et configure une URL M3U
2. PAR ÉCRAN : Chaque écran peut avoir OnlineTV activé/désactivé
3. BASCULE : Mode "playlist" (défaut) ou "iptv" (OnlineTV)
4. OVERLAYS : Restent actifs en mode OnlineTV (bandeaux, diffusions)

FLUX TECHNIQUE
--------------
1. Établissement configure URL M3U (liste de chaînes)
2. Service iptv_service.py parse le M3U → liste de chaînes
3. Manager sélectionne une chaîne pour un écran
4. Player détecte mode "iptv" via API playlist
5. HLS.js charge le stream M3U/HLS
6. Overlays continuent à s'afficher par-dessus le stream

PRIORITÉS EN MODE ONLINETV
--------------------------
- Le stream OnlineTV remplace la playlist
- Les overlays locaux (établissement) restent actifs
- Les diffusions (broadcasts) restent actives
- Les heartbeats continuent normalement

FALLBACK
--------
- Si stream échoue → HLS.js tente récupération automatique
- Si HLS échoue → mpegts.js prend le relais pour flux MPEG-TS
- Si récupération échoue → affichage message erreur
- Possibilité de repasser en mode playlist manuellement

=================
STREAMING ADAPTATIF (ABR)
=================

LOGIQUE ABR (Décembre 2025)
---------------------------
Le streaming OnlineTV utilise désormais l'Adaptive Bitrate Streaming (ABR) comme YouTube/Netflix :

1. ESTIMATION BANDE PASSANTE :
   - Algorithme EWMA (Exponentially Weighted Moving Average)
   - Coefficients Fast (3.0) et Slow (9.0) pour réactivité optimale
   - Mesure continue pendant le téléchargement des segments

2. SÉLECTION QUALITÉ AUTOMATIQUE :
   - startLevel: -1 (auto, pas de niveau forcé)
   - abrBandWidthFactor: 0.95 (utilise 95% de la bande passante estimée)
   - abrBandWidthUpFactor: 0.7 (monte en qualité à 70% du seuil)

3. GESTION DES BUFFERS :
   - backBufferLength: 60s (tampon arrière)
   - maxBufferLength: 30s (tampon avant standard)
   - maxMaxBufferLength: 120s (tampon avant maximum)
   - maxBufferSize: 60MB

4. RÉCUPÉRATION ERREURS :
   - fragLoadingMaxRetry: 8 (tentatives par fragment)
   - fragLoadingRetryDelay: 500ms (délai entre tentatives)
   - manifestLoadingMaxRetry: 6
   - levelLoadingMaxRetry: 6

COMPORTEMENT ABR
----------------
| Situation | Action |
|-----------|--------|
| Bande passante baisse | Qualité descend automatiquement |
| Bande passante remonte | Qualité remonte progressivement |
| Erreur réseau | Retry automatique sans interruption |
| Fragment manquant | Continue avec qualité inférieure |

INDICATEUR QUALITÉ
------------------
L'indicateur visuel affiche :
- Résolution actuelle (ex: 720p, 1080p)
- Badge qualité (FHD/HD/SD/LD/LOW)
- Barre de bande passante (vert=bon, jaune=moyen, rouge=faible)
- Débit en Mbps

NIVEAUX QUALITÉ
---------------
| Badge | Résolution | Débit typique |
|-------|------------|---------------|
| FHD | 1080p+ | 4+ Mbps |
| HD | 720p | 2-4 Mbps |
| SD | 480p | 1-2 Mbps |
| LD | 360p | 0.5-1 Mbps |
| LOW | <360p | <0.5 Mbps |

AUDIO
-----
- Son activé par défaut sur tous les flux
- État audio synchronisé entre vidéo et IPTV
- Touche 'M' pour basculer mute/unmute
- Bouton audio visible en bas à droite du player

=================
CONTRÔLE AUDIO PLAYER
=================

LOGIQUE AUDIO
-------------
1. ÉTAT INITIAL : Audio activé (muted = false)
2. SYNCHRONISATION : État partagé entre videoEl et iptvEl
3. BASCULE : Touche 'M' ou clic sur bouton toggle mute/unmute
4. PERSISTANCE : État conservé lors du changement de mode (playlist ↔ TV)

IMPLÉMENTATION
--------------
1. Variable globale `isMuted` gère l'état
2. Fonction `updateMuteState()` applique l'état aux deux éléments
3. EventListener sur keydown pour touche 'M'
4. Bouton avec icône dynamique (fa-volume-up / fa-volume-mute)

SYNCHRONISATION VIDEO/IPTV
--------------------------
- Quand on bascule de playlist → IPTV : l'état mute est appliqué au stream
- Quand on bascule de IPTV → playlist : l'état mute est appliqué à la vidéo
- L'icône du bouton reflète toujours l'état courant

RACCOURCIS CLAVIER
------------------
| Touche | Action |
|--------|--------|
| F11 | Mode plein écran |
| M | Mute / Unmute |
| Espace | Pause / Play |

=================
CONTRÔLE PUBLICITÉS
=================

LOGIQUE ALLOW_AD_CONTENT
------------------------
1. Chaque établissement a un paramètre `allow_ad_content` (défaut: TRUE)
2. Accessible via les paramètres de l'établissement (toggle)
3. Affecte uniquement les contenus publicitaires du superadmin (AdContent)

FILTRAGE
--------
- Si allow_ad_content = TRUE (ou NULL) → Publicités superadmin affichées
- Si allow_ad_content = FALSE → Publicités superadmin filtrées

CIBLAGE CONCERNÉ
----------------
- Ciblage par pays : vérifie allow_ad_content de chaque organisation
- Ciblage par ville : vérifie allow_ad_content de chaque organisation
- Ciblage par organisation : vérifie allow_ad_content de l'organisation ciblée
- Ciblage par écran : vérifie allow_ad_content de l'organisation de l'écran

NOTE: N'affecte pas les overlays, broadcasts et contenus internes de l'établissement