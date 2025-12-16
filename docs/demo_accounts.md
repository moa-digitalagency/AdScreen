# Comptes de démonstration

Ce document liste tous les comptes et données créés par le script `init_db_demo.py`. Utilisez-les pour explorer la plateforme.

## Créer les données de démo

```bash
# Créer les données
python init_db_demo.py

# Recréer à zéro (supprime puis recrée)
python init_db_demo.py --force

# Tout supprimer
python init_db_demo.py --clear
```

## Compte administrateur

L'administrateur a accès à toute la plateforme via `/admin`.

| Champ | Valeur |
|-------|--------|
| Email | admin@shabaka-adscreen.com |
| Mot de passe | admin123 |

En production, utilisez les variables d'environnement `SUPERADMIN_EMAIL` et `SUPERADMIN_PASSWORD`. Ne gardez jamais les identifiants de démo.

## Comptes établissements

Chaque établissement a son propre compte pour gérer ses écrans via `/org`.

**Mot de passe commun : `demo123`**

### France (Euro)

| Établissement | Email | Plan | Commission | Écrans | Type |
|---------------|-------|------|------------|--------|------|
| Le Bistrot Parisien | manager@restaurant-paris.fr | Premium | 10% | 2 | Payant |
| Bar Le Central | manager@bar-lyon.fr | Basic | 12% | 1 | Payant |
| Centre Commercial Atlantis | manager@atlantis-mall.fr | Enterprise | 8% | 2 | Payant |
| Petit Café Gratuit | manager@cafe-gratuit.fr | Free | 0% | 1 | Gratuit |

### Maroc (Dirham)

| Établissement | Email | Plan | Commission | Écrans |
|---------------|-------|------|------------|--------|
| Café Marrakech | manager@cafe-marrakech.ma | Premium | 10% | 2 |

### Sénégal (Franc CFA)

| Établissement | Email | Plan | Commission | Écrans |
|---------------|-------|------|------------|--------|
| Restaurant Dakar Beach | manager@dakar-beach.sn | Basic | 12% | 1 |

### Tunisie (Dinar)

| Établissement | Email | Plan | Commission | Écrans |
|---------------|-------|------|------------|--------|
| Tunisian Café | manager@tunis-cafe.tn | Basic | 10% | 1 |

## Détail des écrans

### Écrans en France

| Établissement | Écran | Résolution | Orientation | Prix/min |
|---------------|-------|------------|-------------|----------|
| Le Bistrot Parisien | Écran Entrée | 1920×1080 | Paysage | 2,00 € |
| Le Bistrot Parisien | Écran Bar | 1080×1920 | Portrait | 1,50 € |
| Bar Le Central | Écran Principal | 1920×1080 | Paysage | 1,80 € |
| Centre Commercial Atlantis | Totem Hall A | 1080×1920 | Portrait | 3,00 € |
| Centre Commercial Atlantis | Écran Food Court | 3840×2160 | Paysage | 5,00 € |
| Petit Café Gratuit | Écran Petit Café | 1920×1080 | Paysage | 0,00 € |

### Écrans au Maroc

| Établissement | Écran | Résolution | Orientation | Prix/min |
|---------------|-------|------------|-------------|----------|
| Café Marrakech | Écran Terrasse | 1920×1080 | Paysage | 20,00 DH |
| Café Marrakech | Totem Médina | 1080×1920 | Portrait | 15,00 DH |

### Écrans au Sénégal

| Établissement | Écran | Résolution | Orientation | Prix/min |
|---------------|-------|------------|-------------|----------|
| Restaurant Dakar Beach | Écran Beach Bar | 1920×1080 | Paysage | 1 000 FCFA |

### Écrans en Tunisie

| Établissement | Écran | Résolution | Orientation | Prix/min |
|---------------|-------|------------|-------------|----------|
| Tunisian Café | Écran Café Habib | 1920×1080 | Paysage | 3,00 DT |

## Mot de passe player

Pour connecter un écran via `/player`, utilisez le code unique de l'écran et ce mot de passe :

**Mot de passe : `screen123`**

## Créneaux horaires

Chaque écran propose ces durées, avec des prix calculés automatiquement :

| Type | Durées disponibles |
|------|-------------------|
| Image | 10s, 15s, 30s |
| Vidéo | 15s, 30s, 60s |

Le prix d'un créneau = prix par minute × (durée en secondes / 60)

## Périodes horaires

Les multiplicateurs de prix s'appliquent selon l'heure :

| Période | Horaires | Multiplicateur |
|---------|----------|----------------|
| Matin | 06h-12h | ×0,8 |
| Midi | 12h-14h | ×1,5 |
| Après-midi | 14h-18h | ×1,0 |
| Soir | 18h-22h | ×1,8 |
| Nuit | 22h-06h | ×0,5 |

## Overlays de démonstration

Des bandeaux défilants sont créés pour tester l'affichage :

| Écran | Position | Message |
|-------|----------|---------|
| Écran Entrée (Paris) | Bas | Happy Hour 17h-19h |
| Totem Hall A (Atlantis) | Haut | Soldes -50% |
| Écran Bar (Paris) | Centre | Menu du jour |
| Écran Food Court (Atlantis) | Bas | Horaires restauration |
| Terrasse Marrakech | Bas | Message bilingue AR/FR |
| Beach Bar Dakar | Haut | Happy Hour FCFA |
| Café Habib Tunis | Bas | WiFi gratuit |

## Diffusions de démonstration

L'administrateur a accès à 5 diffusions centralisées avec différents modes :

| Nom | Ciblage | Mode | Récurrence |
|-----|---------|------|------------|
| Promotion Été France | Pays: France | Immédiat | - |
| Message Marrakech | Ville: Marrakech | Immédiat | - |
| Promo Centre Atlantis | Établissement | Programmé | Quotidien 12h |
| Info Écran Beach | Écran spécifique | Programmé | Vendredi/samedi 18h |
| Promo Mensuelle Tunisie | Pays: Tunisie | Programmé | Mensuel 9h |

## Scénarios de test

### Tester l'interface administrateur

1. Connectez-vous avec `admin@shabaka-adscreen.com` / `admin123`
2. Consultez la liste des établissements (7 établissements, 4 pays)
3. Visualisez les statistiques globales
4. Créez un nouvel établissement
5. Accédez au menu Diffusion pour gérer les broadcasts

### Tester les diffusions centralisées

1. Connectez-vous en administrateur
2. Allez dans "Diffusion" dans le menu
3. Consultez les diffusions existantes
4. Créez une nouvelle diffusion ciblant un pays
5. Activez/désactivez une diffusion
6. Vérifiez sur le player que la diffusion apparaît

### Tester l'interface établissement

1. Connectez-vous avec `manager@restaurant-paris.fr` / `demo123`
2. Consultez vos 2 écrans
3. Modifiez la configuration d'un écran
4. Téléchargez le QR code
5. Gérez les overlays

### Tester la réservation (annonceur)

1. Accédez au lien d'un écran ou scannez son QR code
2. Consultez les caractéristiques et prix
3. Sélectionnez un créneau et une période
4. Uploadez une image ou vidéo
5. Téléchargez le reçu (image ou PDF)

### Tester le player

1. Accédez à `/player`
2. Entrez le code unique d'un écran
3. Entrez le mot de passe `screen123`
4. Passez en plein écran (F11)
5. Vérifiez l'affichage des overlays
6. Testez le contrôle audio (touche M)

### Tester le multi-devises

1. Réservez sur un écran français (prix en €)
2. Réservez sur un écran marocain (prix en DH)
3. Réservez sur un écran sénégalais (prix en FCFA)
4. Vérifiez que les reçus affichent la bonne devise

### Tester le mode OnlineTV

1. Connectez-vous en tant que manager
2. Allez dans OnlineTV sur un écran
3. Configurez une URL de liste M3U
4. Sélectionnez une chaîne
5. Basculez en mode OnlineTV
6. Vérifiez que les overlays restent visibles
7. Testez le contrôle audio

### Tester le streaming adaptatif

1. Lancez un stream OnlineTV
2. Observez l'indicateur de qualité (en bas à droite)
3. Simulez une connexion lente (outils développeur du navigateur)
4. Vérifiez que la qualité baisse automatiquement
5. Rétablissez la connexion normale
6. Vérifiez que la qualité remonte

### Tester l'établissement gratuit

1. Connectez-vous avec `manager@cafe-gratuit.fr` / `demo123`
2. Vérifiez l'accès limité : pas de réservations, pas de facturation
3. Testez la gestion des contenus internes et overlays
4. Vérifiez que le player affiche les fillers

## Réinitialisation

Pour revenir à un état propre :

```bash
python init_db_demo.py --force
```

## Avertissement

Ces données sont uniquement destinées aux tests.

- Les mots de passe sont faibles et ne doivent pas être utilisés en production
- Supprimez les données de démo avant de mettre en production (`--clear`)
- En production, configurez le super-administrateur via les variables d'environnement
