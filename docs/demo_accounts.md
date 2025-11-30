# Comptes de Démonstration

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
| Email | admin@adscreen.com |
| Mot de passe | admin123 |
| Rôle | superadmin |

**Accès** : http://localhost:5000/admin

### Établissements

Chaque établissement a son propre compte pour gérer ses écrans.

#### 1. Le Bistrot Parisien

| Champ | Valeur |
|-------|--------|
| Email | manager@restaurant-paris.fr |
| Mot de passe | demo123 |
| Plan | Premium |
| Commission | 10% |

**Écrans** :
- Écran Entrée (1920x1080 paysage)
- Écran Bar (1080x1920 portrait)

#### 2. Bar Le Central

| Champ | Valeur |
|-------|--------|
| Email | manager@bar-lyon.fr |
| Mot de passe | demo123 |
| Plan | Basic |
| Commission | 12% |

**Écrans** :
- Écran Principal (1920x1080 paysage, images uniquement)

#### 3. Centre Commercial Atlantis

| Champ | Valeur |
|-------|--------|
| Email | manager@atlantis-mall.fr |
| Mot de passe | demo123 |
| Plan | Enterprise |
| Commission | 8% |

**Écrans** :
- Totem Hall A (1080x1920 portrait)
- Écran Géant Food Court (3840x2160 4K paysage)

**Accès établissement** : http://localhost:5000/org

## Configuration des écrans

### Mot de passe Player

Tous les écrans de démonstration ont le même mot de passe player :

```
screen123
```

**Accès player** : http://localhost:5000/player

### Créneaux horaires (par écran)

| Type | Durée | Prix/diffusion |
|------|-------|----------------|
| Image | 5s | 0,50 € |
| Image | 10s | 0,80 € |
| Image | 15s | 1,00 € |
| Vidéo | 10s | 1,50 € |
| Vidéo | 15s | 2,00 € |
| Vidéo | 30s | 3,50 € |

### Périodes horaires (multiplicateurs de prix)

| Période | Horaires | Multiplicateur |
|---------|----------|----------------|
| Matin | 06:00 - 12:00 | x0.8 |
| Midi | 12:00 - 14:00 | x1.5 |
| Après-midi | 14:00 - 18:00 | x1.0 |
| Soir | 18:00 - 22:00 | x1.8 |
| Nuit | 22:00 - 06:00 | x0.5 |

## Scénarios de test

### 1. Test Superadmin

1. Connectez-vous avec admin@adscreen.com
2. Consultez la liste des établissements
3. Visualisez les statistiques globales
4. Créez un nouvel établissement

### 2. Test Établissement

1. Connectez-vous avec manager@restaurant-paris.fr
2. Consultez vos écrans
3. Modifiez la configuration d'un écran
4. Téléchargez le QR code d'un écran

### 3. Test Client (Annonceur)

1. Scannez un QR code ou accédez au lien d'un écran
2. Consultez les spécifications de l'écran
3. Sélectionnez un créneau et une période
4. Uploadez un contenu (image ou vidéo)
5. Suivez le statut de votre réservation

### 4. Test Player

1. Accédez à http://localhost:5000/player
2. Entrez le code unique d'un écran
3. Entrez le mot de passe : screen123
4. Lancez la playlist en mode plein écran

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
