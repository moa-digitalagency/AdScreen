# Documentation Shabaka AdScreen

Bienvenue dans la documentation de Shabaka AdScreen, la plateforme de monétisation d'écrans publicitaires.

## Qu'est-ce que Shabaka AdScreen ?

Shabaka AdScreen permet aux commerces de transformer leurs écrans en source de revenus. Un restaurant, un bar ou un centre commercial peut proposer de l'espace publicitaire à des annonceurs locaux, qui réservent et paient directement via un QR code.

La plateforme gère tout : la réservation, la validation des contenus, la diffusion, la facturation. Elle fonctionne dans 208 pays avec 4 devises natives (Euro, Dirham marocain, Franc CFA, Dinar tunisien).

## Organisation de la documentation

### Pour comprendre le produit

**[Présentation commerciale](COMMERCIAL_PRESENTATION.md)** - Le pitch complet pour présenter Shabaka AdScreen à des investisseurs ou des clients potentiels. Vision, problèmes résolus, avantages concurrentiels, modèle économique.

**[Guide des fonctionnalités](features.md)** - La liste exhaustive de tout ce que sait faire la plateforme, organisée par type d'utilisateur (opérateur, établissement, annonceur, écran).

### Pour utiliser la plateforme

**[Comptes de démonstration](demo_accounts.md)** - Les identifiants de test et les scénarios pour explorer chaque interface. Indispensable pour une première prise en main.

**[Algorithmes métier](Algo.md)** - Comment sont calculés les prix, les disponibilités, la répartition des diffusions. Utile pour comprendre la logique commerciale.

### Pour déployer et maintenir

**[Guide de déploiement](deployment.md)** - Installation sur Replit ou un serveur classique, configuration, maintenance, dépannage.

**[Déploiement VPS](VPS_DEPLOYMENT.md)** - Instructions spécifiques pour installer l'application sur un serveur privé virtuel avec systemd et Nginx.

### Pour développer

**[Architecture technique](architecture.md)** - Structure du code, modèle de données, flux d'information. Le point d'entrée pour les développeurs.

**[API Mobile](API_MOBILE_DOCUMENTATION.md)** - Documentation complète de l'API REST pour intégrer la plateforme dans d'autres applications.

**[API Mobile sécurisée v1](API_MOBILE_V1_SECURE.md)** - La version JWT de l'API avec authentification par tokens et rate limiting.

**[SDK Player Mobile](PLAYER_MOBILE_SDK.md)** - Guide pour développer un player natif Android ou iOS qui se synchronise avec le backend.

## Les quatre interfaces

Shabaka AdScreen expose quatre interfaces distinctes, chacune pour un type d'utilisateur :

### Interface opérateur (`/admin`)

C'est la console de pilotage. L'opérateur (vous ou votre équipe) y gère :
- Les établissements et leurs commissions
- Les diffusions centralisées vers les écrans
- Les administrateurs et leurs permissions
- La facturation hebdomadaire
- Les paramètres globaux (SEO, WhatsApp, maintenance)

### Interface établissement (`/org`)

Chaque établissement accède à son propre tableau de bord pour :
- Configurer ses écrans (résolution, prix, types de contenu)
- Valider ou refuser les contenus soumis par les annonceurs
- Gérer ses bandeaux défilants et contenus internes
- Consulter ses statistiques et revenus
- Accéder à ses factures

### Interface annonceur (`/book/<code>`)

Les annonceurs accèdent via le QR code de l'écran. Ils peuvent :
- Voir les caractéristiques et le prix de l'écran
- Choisir leur créneau (durée, période, nombre de diffusions)
- Uploader leur contenu (image ou vidéo)
- Recevoir un reçu (image thermique ou PDF)
- Suivre le statut de leur réservation

### Interface player (`/player`)

C'est l'interface de diffusion, affichée sur les écrans publicitaires. Elle :
- Enchaîne les contenus selon leur priorité
- Affiche les bandeaux et overlays par-dessus
- Envoie un signal régulier pour confirmer que l'écran fonctionne
- Peut basculer en mode TV quand il n'y a pas de publicité

## Stack technique

Le backend est en Python avec Flask, SQLAlchemy et PostgreSQL. Le frontend utilise des templates Jinja2 avec Tailwind CSS. Pas de framework JavaScript complexe : les pages sont générées côté serveur.

Le player utilise HLS.js pour le streaming adaptatif et des Service Workers pour le cache hors ligne.

L'application tourne sur Gunicorn et peut être déployée sur Replit, un VPS classique ou tout environnement compatible Python.

## Premiers pas

1. **Explorer** : Lancez les données de démonstration avec `python init_db_demo.py` et connectez-vous avec les comptes de test
2. **Comprendre** : Lisez le [guide des fonctionnalités](features.md) pour avoir une vue d'ensemble
3. **Configurer** : Suivez le [guide de déploiement](deployment.md) pour mettre en production
4. **Personnaliser** : Consultez l'[architecture technique](architecture.md) pour adapter le code à vos besoins

## Besoin d'aide ?

La documentation couvre l'essentiel, mais si vous bloquez sur un point précis :
- Vérifiez la section Troubleshooting du [guide de déploiement](deployment.md)
- Consultez les logs de l'application pour identifier les erreurs
- Les données de démonstration permettent de tester chaque fonctionnalité isolément

Bonne exploration !
