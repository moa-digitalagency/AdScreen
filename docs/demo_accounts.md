# Comptes de Démonstration - Shabaka AdScreen

Ce document décrit les comptes et données créés par le script `init_db_demo.py`.

## Création des données de démo

```bash
# Créer les données de démonstration
python init_db_demo.py

# Forcer la recréation (supprime les données existantes)
python init_db_demo.py --force

# Supprimer toutes les données
python init_db_demo.py --clear
```

## Comptes utilisateurs

### Superadmin

Accès complet à la plateforme : gestion des établissements, statistiques globales, configuration.

| Champ | Valeur |
|-------|--------|
| Email | admin@shabaka-adscreen.com |
| Mot de passe | admin123 |
| Rôle | superadmin |

**Accès** : `/admin`

### Établissements par pays

Chaque établissement a son propre compte pour gérer ses écrans. **Mot de passe commun : `demo123`**

#### 🇫🇷 France (EUR - €)

| Établissement | Email | Plan | Commission | Écrans |
|--------------|-------|------|------------|--------|
| Le Bistrot Parisien | manager@restaurant-paris.fr | Premium | 10% | 2 |
| Bar Le Central | manager@bar-lyon.fr | Basic | 12% | 1 |
| Centre Commercial Atlantis | manager@atlantis-mall.fr | Enterprise | 8% | 2 |

#### 🇲🇦 Maroc (MAD - DH)

| Établissement | Email | Plan | Commission | Écrans |
|--------------|-------|------|------------|--------|
| Café Marrakech | manager@cafe-marrakech.ma | Premium | 10% | 2 |

#### 🇸🇳 Sénégal (XOF - FCFA)

| Établissement | Email | Plan | Commission | Écrans |
|--------------|-------|------|------------|--------|
| Restaurant Dakar Beach | manager@dakar-beach.sn | Basic | 12% | 1 |

#### 🇹🇳 Tunisie (TND - DT)

| Établissement | Email | Plan | Commission | Écrans |
|--------------|-------|------|------------|--------|
| Tunisian Café | manager@tunis-cafe.tn | Basic | 10% | 1 |

**Accès établissement** : `/org`

## Détail des écrans

### France

| Établissement | Écran | Résolution | Orientation | Prix/min |
|--------------|-------|------------|-------------|----------|
| Le Bistrot Parisien | Écran Entrée | 1920x1080 | Paysage | 2.00 € |
| Le Bistrot Parisien | Écran Bar | 1080x1920 | Portrait | 1.50 € |
| Bar Le Central | Écran Principal | 1920x1080 | Paysage | 1.80 € |
| Centre Commercial Atlantis | Totem Hall A | 1080x1920 | Portrait | 3.00 € |
| Centre Commercial Atlantis | Écran Géant Food Court | 3840x2160 | Paysage | 5.00 € |

### Maroc

| Établissement | Écran | Résolution | Orientation | Prix/min |
|--------------|-------|------------|-------------|----------|
| Café Marrakech | Écran Terrasse | 1920x1080 | Paysage | 20.00 DH |
| Café Marrakech | Totem Médina | 1080x1920 | Portrait | 15.00 DH |

### Sénégal

| Établissement | Écran | Résolution | Orientation | Prix/min |
|--------------|-------|------------|-------------|----------|
| Restaurant Dakar Beach | Écran Beach Bar | 1920x1080 | Paysage | 1000 FCFA |

### Tunisie

| Établissement | Écran | Résolution | Orientation | Prix/min |
|--------------|-------|------------|-------------|----------|
| Tunisian Café | Écran Café Habib | 1920x1080 | Paysage | 3.00 DT |

## Mot de passe Player

Tous les écrans de démonstration ont le même mot de passe player :

```
screen123
```

**Accès player** : `/player`

## Créneaux horaires (par écran)

Prix calculés automatiquement basé sur le prix par minute de chaque écran.

| Type | Durée | Formule |
|------|-------|---------|
| Image | 10s | prix_min × (10/60) |
| Image | 15s | prix_min × (15/60) |
| Image | 30s | prix_min × (30/60) |
| Vidéo | 15s | prix_min × (15/60) |
| Vidéo | 30s | prix_min × (30/60) |
| Vidéo | 60s | prix_min × (60/60) |

## Périodes horaires (multiplicateurs de prix)

| Période | Horaires | Multiplicateur |
|---------|----------|----------------|
| Matin | 06:00 - 12:00 | x0.8 |
| Midi | 12:00 - 14:00 | x1.5 |
| Après-midi | 14:00 - 18:00 | x1.0 |
| Soir | 18:00 - 22:00 | x1.8 |
| Nuit | 22:00 - 06:00 | x0.5 |

## Overlays de démonstration

7 bandeaux défilants pré-configurés :

| Écran | Position | Message |
|-------|----------|---------|
| Écran Entrée (Paris) | Footer | Happy Hour 17h-19h |
| Totem Hall A (Atlantis) | Header | Soldes -50% |
| Écran Bar (Paris) | Body | Menu du jour |
| Écran Food Court (Atlantis) | Footer | Horaires restauration |
| Terrasse Marrakech | Footer | Bilingue AR/FR |
| Beach Bar Dakar | Header | Happy Hour FCFA |
| Café Habib Tunis | Footer | Services WiFi |

## Scénarios de test

### 1. Test Superadmin

1. Connectez-vous avec admin@shabaka-adscreen.com / admin123
2. Consultez la liste des établissements (6 établissements, 4 pays)
3. Visualisez les statistiques globales
4. Créez un nouvel établissement

### 2. Test Établissement

1. Connectez-vous avec manager@restaurant-paris.fr / demo123
2. Consultez vos écrans (2 écrans)
3. Modifiez la configuration d'un écran
4. Téléchargez le QR code d'un écran
5. Gérez les overlays (bandeaux défilants)

### 3. Test Client (Annonceur)

1. Scannez un QR code ou accédez au lien d'un écran
2. Consultez les specs (résolution, prix en devise locale)
3. Sélectionnez un créneau et une période
4. Uploadez un contenu (image ou vidéo)
5. Téléchargez votre reçu (image thermique ou PDF)

### 4. Test Player

1. Accédez à `/player`
2. Entrez le code unique d'un écran
3. Entrez le mot de passe : screen123
4. Lancez la playlist en mode plein écran
5. Vérifiez l'affichage des overlays

### 5. Test Multi-devises

1. Réservez sur un écran français (prix en €)
2. Réservez sur un écran marocain (prix en DH)
3. Réservez sur un écran sénégalais (prix en FCFA)
4. Vérifiez que les reçus affichent la bonne devise

## Réinitialisation

Pour revenir à un état propre :

```bash
# Supprimer toutes les données et recréer les démos
python init_db_demo.py --force
```

## Notes importantes

- Les mots de passe de démonstration sont faibles et ne doivent **jamais** être utilisés en production
- Les données de démonstration sont destinées uniquement aux tests
- Après les tests, utilisez `--clear` pour supprimer toutes les données avant la mise en production
- Les devises sont configurées par organisation et affectent tous les écrans de l'établissement
