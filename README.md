# Shabaka AdScreen

**Transformez vos écrans en source de revenus**

Shabaka AdScreen est une plateforme développée par Shabaka InnovLab qui permet aux commerces - restaurants, bars, centres commerciaux, hôtels - de rentabiliser leurs écrans d'affichage. Les annonceurs locaux réservent des créneaux publicitaires directement via un QR code, sans intermédiaire.

## Ce que fait la plateforme

La plateforme connecte trois acteurs :

**Les établissements** installent l'application sur leurs écrans et définissent leurs tarifs. Chaque écran génère un QR code unique que les clients peuvent scanner pour réserver de l'espace publicitaire.

**Les annonceurs** scannent le QR code, voient les disponibilités et les prix, uploadent leur contenu (image ou vidéo), paient et reçoivent un reçu. C'est aussi simple que ça.

**L'opérateur** (vous) gère l'ensemble depuis une console d'administration : établissements, commissions, diffusions centralisées, facturation automatique.

## Couverture internationale

La plateforme fonctionne dans 208 pays avec plus de 4 600 villes référencées. Quatre devises sont nativement supportées :

- Euro (EUR) pour la France et l'Europe
- Dirham marocain (MAD) pour le Maroc
- Franc CFA (XOF) pour l'Afrique de l'Ouest
- Dinar tunisien (TND) pour la Tunisie

Les prix, reçus et statistiques s'affichent automatiquement dans la devise de chaque établissement.

## Comment ça marche

### Pour un établissement

1. Créez votre compte et configurez vos écrans (résolution, orientation, tarifs)
2. Imprimez ou affichez le QR code généré automatiquement
3. Validez ou refusez les contenus soumis par les annonceurs
4. Consultez vos statistiques et revenus

### Pour un annonceur

1. Scannez le QR code de l'écran qui vous intéresse
2. Choisissez la durée, la période horaire et le nombre de diffusions
3. Uploadez votre image ou vidéo
4. Payez et téléchargez votre reçu

### Pour l'opérateur

1. Gérez les établissements et leurs commissions
2. Diffusez des messages sur tous les écrans d'un pays, d'une ville ou d'un établissement
3. Suivez les revenus globaux et la santé du réseau
4. Générez automatiquement les factures hebdomadaires

## Fonctionnalités principales

### Gestion des écrans
- Résolutions personnalisables (HD, Full HD, 4K, portrait ou paysage)
- Types de contenu : images, vidéos ou les deux
- Limite de taille de fichier configurable par écran
- Monitoring en temps réel (statut online/offline, uptime)

### Tarification flexible
- Prix par minute défini par l'établissement
- Créneaux de 10, 15, 30 ou 60 secondes
- Multiplicateurs horaires (matin, midi, soir, nuit)
- Calcul automatique du prix final

### Validation des contenus
- Vérification automatique de la résolution et du format
- Contrôle de la durée des vidéos
- File d'attente pour validation manuelle
- Motifs de refus personnalisables

### Diffusions centralisées
- L'opérateur peut pousser du contenu vers n'importe quel écran
- Ciblage par pays, ville, établissement ou écran spécifique
- Programmation avec dates et récurrence (quotidien, hebdomadaire, mensuel)
- Priorité configurable pour contrôler l'ordre d'affichage

### Mode OnlineTV
- Diffusez des chaînes TV en direct quand il n'y a pas de publicité
- Les bandeaux publicitaires restent visibles par-dessus le flux TV
- Streaming adaptatif qui ajuste la qualité selon la connexion

### Overlays et bandeaux
- Texte défilant personnalisable (couleurs, vitesse, position)
- Affichage par-dessus le contenu principal
- Géré par l'établissement ou diffusé centralement

### Facturation automatique
- Cycle hebdomadaire (lundi à dimanche)
- Commission configurable par établissement
- Upload des preuves de paiement
- Export PDF des factures

## Installation

### Prérequis

- Python 3.11 ou supérieur
- PostgreSQL 14 ou supérieur
- ffmpeg (pour la validation des vidéos)

### Configuration

Définissez ces variables d'environnement :

```bash
DATABASE_URL=postgresql://utilisateur:motdepasse@localhost:5432/shabaka_adscreen
SESSION_SECRET=une-clé-secrète-longue-et-aléatoire
SUPERADMIN_EMAIL=admin@votre-domaine.com
SUPERADMIN_PASSWORD=un-mot-de-passe-solide
```

### Lancement

```bash
# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base de données
python init_db.py

# Démarrer l'application
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

L'application est accessible sur `http://localhost:5000`

## Tester la plateforme

Lancez les données de démonstration pour explorer toutes les fonctionnalités :

```bash
python init_db_demo.py
```

Cela crée 7 établissements dans 4 pays, 10 écrans et plusieurs diffusions de test.

**Compte administrateur** : `admin@shabaka-adscreen.com` / `admin123`

**Comptes établissements** (mot de passe : `demo123`) :
- `manager@restaurant-paris.fr` - Restaurant parisien
- `manager@cafe-marrakech.ma` - Café au Maroc
- `manager@dakar-beach.sn` - Restaurant au Sénégal
- `manager@tunis-cafe.tn` - Café en Tunisie

**Mot de passe player** pour tous les écrans : `screen123`

## Documentation

La documentation complète se trouve dans le dossier `docs/` :

- [Guide des fonctionnalités](docs/features.md) - Détail de toutes les fonctionnalités
- [Architecture technique](docs/architecture.md) - Structure du code et des données
- [Guide de déploiement](docs/deployment.md) - Installation en production
- [Comptes de démonstration](docs/demo_accounts.md) - Données de test
- [Présentation commerciale](docs/COMMERCIAL_PRESENTATION.md) - Pour convaincre vos clients
- [API Mobile](docs/API_MOBILE_V1_SECURE.md) - Pour développer une app mobile

## Licence

Propriétaire - Tous droits réservés - Shabaka InnovLab
